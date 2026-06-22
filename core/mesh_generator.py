import os
import json
import struct
from PIL import Image
import numpy as np

def generate_yaru_glb():
    print("🔮 [Yaru 1.0 AI Engine] Starting strict binary 3D reconstruction loop...")
    manifest_path = "telemetry/ai_input_manifest.json"
    output_glb_path = "output_models/yaru_model.glb"
    os.makedirs("output_models", exist_ok=True)

    if not os.path.exists(manifest_path):
        print("❌ Core Halt: Manifest registry missing.")
        return False

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    front_info = manifest["views"]["front"]
    img_path = front_info["source_file"]
    bg_mode = front_info["background_mask_target"]

    if not os.path.exists(img_path):
        print(f"❌ Core Halt: Physical file '{img_path}' not found!")
        return False

    print(f"🖼️ Deep-scanning pixel grid array from: {img_path}")
    with Image.open(img_path) as img:
        grid_res = 64 
        img_resized = img.convert('RGB').resize((grid_res, grid_res), Image.Resampling.LANCZOS)
        pixel_matrix = np.array(img_resized)

    if bg_mode == "SOLID_BLACK":
        object_mask = (pixel_matrix[:, :, 0] > 20) | (pixel_matrix[:, :, 1] > 20) | (pixel_matrix[:, :, 2] > 20)
    else:
        object_mask = (pixel_matrix[:, :, 0] < 235) | (pixel_matrix[:, :, 1] < 235) | (pixel_matrix[:, :, 2] < 235)

    vertices = []
    indices = []
    vertex_counter = 0
    
    voxel_scale = 1.0 / grid_res
    depth_thickness = 0.08

    for y in range(grid_res):
        for x in range(grid_res):
            if object_mask[y, x]:
                xf = (x * voxel_scale) - 0.5
                yf = 0.5 - (y * voxel_scale)
                r, g, b = pixel_matrix[y, x] / 255.0
                
                # 8 corners per voxel node
                box_vertices = [
                    [xf, yf, depth_thickness, r, g, b], [xf + voxel_scale, yf, depth_thickness, r, g, b],
                    [xf + voxel_scale, yf - voxel_scale, depth_thickness, r, g, b], [xf, yf - voxel_scale, depth_thickness, r, g, b],
                    [xf, yf, -depth_thickness, r, g, b], [xf + voxel_scale, yf, -depth_thickness, r, g, b],
                    [xf + voxel_scale, yf - voxel_scale, -depth_thickness, r, g, b], [xf, yf - voxel_scale, -depth_thickness, r, g, b]
                ]
                
                for v in box_vertices:
                    vertices.extend(v)
                
                base = vertex_counter
                box_faces = [
                    base, base+1, base+2, base, base+2, base+3,     # Front
                    base+4, base+6, base+5, base+4, base+7, base+6, # Back
                    base, base+3, base+7, base, base+7, base+4,     # Left
                    base+1, base+5, base+6, base+1, base+6, base+2, # Right
                    base, base+4, base+5, base, base+5, base+1,     # Top
                    base+3, base+2, base+6, base+3, base+6, base+7  # Bottom
                ]
                indices.extend(box_faces)
                vertex_counter += 8

    if vertex_counter == 0:
        print("❌ Error: No subject pixels isolated inside graphic mask.")
        return False

    # 1. Compile Vertex Buffer (Fills positions and color strides)
    v_buffer = b""
    for i in range(0, len(vertices), 6):
        v_buffer += struct.pack("<ffffff", *vertices[i:i+6])
        
    # 2. Compile Index Buffer
    i_buffer = b""
    for index_val in indices:
        i_buffer += struct.pack("<H", index_val)
        
    # Standard-compliance padding rule: Indices chunk must be a multiple of 4 bytes
    while len(i_buffer) % 4 != 0:
        i_buffer += b"\x00"

    len_v = len(v_buffer)
    len_i = len(i_buffer)
    total_binary_payload_len = len_v + len_i

    # 3. Construct clean, standardized JSON scene blueprint
    json_blueprint = {
        "asset": {
            "version": "2.0",
            "generator": "Yaru Engine v1.0"
        },
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "Yaru_Carved_Mesh"}],
        "meshes": [{
            "primitives": [{
                "attributes": {
                    "POSITION": 0,
                    "COLOR_0": 1
                },
                "indices": 2,
                "mode": 4
            }]
        }],
        "bufferViews": [
            {
                "buffer": 0,
                "byteOffset": 0,
                "byteLength": len_v,
                "byteStride": 24,
                "target": 34962
            },
            {
                "buffer": 0,
                "byteOffset": len_v,
                "byteLength": len_i,
                "target": 34963
            }
        ],
        "accessors": [
            {
                "bufferView": 0,
                "byteOffset": 0,
                "componentType": 5126,
                "count": vertex_counter,
                "type": "VEC3"
            },
            {
                "bufferView": 0,
                "byteOffset": 12,
                "componentType": 5126,
                "count": vertex_counter,
                "type": "VEC3"
            },
            {
                "bufferView": 1,
                "byteOffset": 0,
                "componentType": 5123,
                "count": len(indices),
                "type": "SCALAR"
            }
        ],
        "buffers": [{
            "byteLength": total_binary_payload_len
        }]
    }

    # Format JSON tightly without illegal hidden formatting characters
    json_bytes = json.dumps(json_blueprint, separators=(',', ':')).encode('utf-8')
    
    # Pad JSON block using standard ASCII trailing spaces (0x20) up to a perfect 4-byte boundary
    while len(json_bytes) % 4 != 0:
        json_bytes += b'\x20'

    # Compute explicit overall file architecture sizes
    json_chunk_len = len(json_bytes)
    total_glb_size = 12 + 8 + json_chunk_len + 8 + total_binary_payload_len
    
    # 4. Pack final structural GLB headers
    glb_header = struct.pack("<III", 0x46544C67, 2, total_glb_size)    # 'glTF' magic descriptor, glTF v2 target, full file size
    json_chunk_header = struct.pack("<II", json_chunk_len, 0x4E4F534A) # Chunk length, type string code ('JSON')
    binary_chunk_header = struct.pack("<II", total_binary_payload_len, 0x004E4942) # Chunk length, type string code ('BIN')

    with open(output_glb_path, "wb") as glb_out:
        glb_out.write(glb_header)
        glb_out.write(json_chunk_header)
        glb_out.write(json_bytes)
        glb_out.write(binary_chunk_header)
        glb_out.write(v_buffer)
        glb_out.write(i_buffer)

    print(f"🎉 SUCCESS! Securely aligned 3D model generated at: {output_glb_path}")
    return True

if __name__ == "__main__":
    generate_yaru_glb()
                
