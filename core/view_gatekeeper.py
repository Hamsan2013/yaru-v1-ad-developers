import os
import json
import struct
from PIL import Image
import numpy as np

def generate_yaru_glb():
    print("🤖 [Yaru 1.0 AI Engine] Initiating Intelligent 3D Spatial Reconstruction...")
    
    manifest_path = "telemetry/ai_input_manifest.json"
    output_dir = "output_models"
    output_glb_path = os.path.join(output_dir, "yaru_model.glb")
    
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(manifest_path):
        print("❌ Error: Manifest file not found.")
        return False
        
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        
    views = manifest.get("views", {})
    if "front" not in views:
        print("❌ Error: Yaru AI Engine requires a verified 'front' view to calculate shape extrusion.")
        return False

    front_info = views["front"]
    front_img_path = front_info["source_file"]
    bg_mode = front_info["background_mask_target"]
    
    print(f"🖼️ Carving 3D coordinates from image: {front_img_path}")
    try:
        with Image.open(front_img_path) as img:
            # Process as a clean, manageable pixel grid
            img_resized = img.convert('RGB').resize((64, 64))
            arr = np.array(img_resized)
    except Exception as e:
        print(f"❌ Failed to parse image data matrix: {e}")
        return False

    if bg_mode == "SOLID_BLACK":
        mask = (arr[:, :, 0] > 15) | (arr[:, :, 1] > 15) | (arr[:, :, 2] > 15)
    else:
        mask = (arr[:, :, 0] < 240) | (arr[:, :, 1] < 240) | (arr[:, :, 2] < 240)

    vertices = []
    indices = []
    vertex_count = 0
    
    height, width = mask.shape

    # Construct voxel geometry from pixel masks
    for y in range(height):
        for x in range(width):
            if mask[y, x]:
                xf = (x / width) - 0.5
                yf = 0.5 - (y / height)
                zf_front = 0.1
                zf_back = -0.1
                
                r, g, b = arr[y, x] / 255.0

                box_verts = [
                    [xf, yf, zf_front, r, g, b], [xf + 0.02, yf, zf_front, r, g, b],
                    [xf + 0.02, yf - 0.02, zf_front, r, g, b], [xf, yf - 0.02, zf_front, r, g, b],
                    [xf, yf, zf_back, r, g, b], [xf + 0.02, yf, zf_back, r, g, b],
                    [xf + 0.02, yf - 0.02, zf_back, r, g, b], [xf, yf - 0.02, zf_back, r, g, b]
                ]
                
                for v in box_verts:
                    vertices.extend(v)
                
                base = vertex_count
                box_indices = [
                    base, base+1, base+2, base, base+2, base+3,
                    base+4, base+6, base+5, base+4, base+7, base+6,
                    base, base+3, base+7, base, base+7, base+4,
                    base+1, base+5, base+6, base+1, base+6, base+2,
                    base, base+4, base+5, base, base+5, base+1,
                    base+3, base+2, base+6, base+3, base+6, base+7
                ]
                indices.extend(box_indices)
                vertex_count += 8

    if vertex_count == 0:
        print("⚠️ Warning: Silhouette mask was empty. Generating standard baseline container shape.")
        vertices = [0.0, 0.0, 0.0, 1.0, 1.0, 1.0]
        indices = [0, 0, 0]
        vertex_count = 1

    v_buffer = b""
    for i in range(0, len(vertices), 6):
        v_buffer += struct.pack("<ffffff", vertices[i], vertices[i+1], vertices[i+2], vertices[i+3], vertices[i+4], vertices[i+5])
        
    i_buffer = b""
    for idx in indices:
        i_buffer += struct.pack("<H", idx)
        
    while len(i_buffer) % 4 != 0:
        i_buffer += b"\x00"

    len_v = len(v_buffer)
    len_i = len(i_buffer)
    total_payload = len_v + len_i

    json_blueprint = {
        "asset": {"version": "2.0", "generator": "Yaru Engine V1-Pro"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "Yaru_Mesh"}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0, "COLOR_0": 1},
                "indices": 2,
                "mode": 4
            }]
        }],
        "bufferViews": [
            {"buffer": 0, "byteOffset": 0, "byteLength": len_v, "byteStride": 24, "target": 34962},
            {"buffer": 0, "byteOffset": len_v, "byteLength": len_i, "target": 34963}
        ],
        "accessors": [
            {"bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": vertex_count, "type": "VEC3"},
            {"bufferView": 0, "byteOffset": 12, "componentType": 5126, "count": vertex_count, "type": "VEC3"},
            {"bufferView": 1, "byteOffset": 0, "componentType": 5123, "count": len(indices), "type": "SCALAR"}
        ],
        "buffers": [{"byteLength": total_payload}]
    }

    json_bytes = json.dumps(json_blueprint).encode('utf-8')
    while len(json_bytes) % 4 != 0:
        json_bytes += b' '

    total_glb_size = 12 + 8 + len(json_bytes) + 8 + total_payload
    glb_header = struct.pack("<III", 0x46544C67, 2, total_glb_size)
    json_chunk_header = struct.pack("<II", len(json_bytes), 0x4E4F534A)
    binary_chunk_header = struct.pack("<II", total_payload, 0x004E4942)

    try:
        with open(output_glb_path, "wb") as out:
            out.write(glb_header)
            out.write(json_chunk_header)
            out.write(json_bytes)
            out.write(binary_chunk_header)
            out.write(v_buffer)
            out.write(i_buffer)
        print(f"🎉 [Yaru Engine] 3D Model file created successfully at: {output_glb_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to pack GLB file: {e}")
        return False

if __name__ == "__main__":
    generate_yaru_glb()
                
