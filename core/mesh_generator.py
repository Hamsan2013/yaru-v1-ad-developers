import os
import json
import struct
from PIL import Image
import numpy as np

def generate_yaru_glb():
    print("🔮 [Yaru 1.0 AI Engine] Starting deep pixel extraction and 3D modeling loop...")
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
        print(f"❌ Core Halt: Physical file '{img_path}' not found in workspace!")
        return False

    print(f"🖼️ Reading pixel matrix array from: {img_path}")
    with Image.open(img_path) as img:
        # 64x64 resolution generates 4,096 prospective voxels (up to 32,768 vertices)
        # This creates a real, heavy computation workload for the CPU runner!
        grid_res = 64 
        img_resized = img.convert('RGB').resize((grid_res, grid_res), Image.Resampling.LANCZOS)
        pixel_matrix = np.array(img_resized)

    # Segment the silhouette shape away from the background canvas
    if bg_mode == "SOLID_BLACK":
        object_mask = (pixel_matrix[:, :, 0] > 20) | (pixel_matrix[:, :, 1] > 20) | (pixel_matrix[:, :, 2] > 20)
    else:
        object_mask = (pixel_matrix[:, :, 0] < 235) | (pixel_matrix[:, :, 1] < 235) | (pixel_matrix[:, :, 2] < 235)

    vertices = []
    indices = []
    vertex_counter = 0
    
    voxel_scale = 1.0 / grid_res
    depth_thickness = 0.08

    print("🧬 Computing low-poly coordinate topology matrices...")
    for y in range(grid_res):
        for x in range(grid_res):
            if object_mask[y, x]:
                # Map 2D raster coordinates cleanly to centered 3D spatial points
                xf = (x * voxel_scale) - 0.5
                yf = 0.5 - (y * voxel_scale)
                
                # Extract RGB normalized vector data to paint the vertex arrays
                r, g, b = pixel_matrix[y, x] / 255.0
                
                # Construct custom geometry: 8 corners per pixel node
                box_vertices = [
                    [xf, yf, depth_thickness, r, g, b], [xf + voxel_scale, yf, depth_thickness, r, g, b],
                    [xf + voxel_scale, yf - voxel_scale, depth_thickness, r, g, b], [xf, yf - voxel_scale, depth_thickness, r, g, b],
                    [xf, yf, -depth_thickness, r, g, b], [xf + voxel_scale, yf, -depth_thickness, r, g, b],
                    [xf + voxel_scale, yf - voxel_scale, -depth_thickness, r, g, b], [xf, yf - voxel_scale, -depth_thickness, r, g, b]
                ]
                
                for v in box_vertices:
                    vertices.extend(v)
                
                # Map the 12 triangular polygon indices for the 6 cube faces
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

    print(f"📊 Extraction completed. Generated {vertex_counter} points / {len(indices) // 3} triangles.")

    if vertex_counter == 0:
        print("❌ Error: Zero target subject pixels detected inside the mask boundaries.")
        return False

    # Compile data blocks directly into byte sequences
    v_buffer = b""
    for i in range(0, len(vertices), 6):
        v_buffer += struct.pack("<ffffff", *vertices[i:i+6])
        
    i_buffer = b""
    for index_val in indices:
        i_buffer += struct.pack("<H", index_val)
        
    while len(i_buffer) % 4 != 0:
        i_buffer += b"\x00"

    len_v = len(v_buffer)
    len_i = len(i_buffer)
    payload_size = len_v + len_i

    # Construct the binary structure manifest
    glb_manifest = {
        "asset": {"version": "2.0", "generator": "Yaru Engine v1.0 Core"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": "Yaru_Carved_Mesh"}],
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
            {"bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": vertex_counter, "type": "VEC3"},
            {"bufferView": 0, "byteOffset": 12, "componentType": 5126, "count": vertex_counter, "type": "VEC3"},
            {"bufferView": 1, "byteOffset": 0, "componentType": 5123, "count": len(indices), "type": "SCALAR"}
        ],
        "buffers": [{"byteLength": payload_size}]
    }

    json_bytes = json.dumps(glb_manifest).encode('utf-8')
    while len(json_bytes) % 4 != 0:
        json_bytes += b' '

    total_glb_size = 12 + 8 + len(json_bytes) + 8 + payload_size
    
    # Binary Pack Header Layer
    header = struct.pack("<III", 0x46544C67, 2, total_glb_size)
    json_chunk = struct.pack("<II", len(json_bytes), 0x4E4F534A)
    binary_chunk = struct.pack("<II", payload_size, 0x004E4942)

    with open(output_glb_path, "wb") as glb_out:
        glb_out.write(header)
        glb_out.write(json_chunk)
        glb_out.write(json_bytes)
        glb_out.write(binary_chunk)
        glb_out.write(v_buffer)
        glb_out.write(i_buffer)

    print(f"🎉 SUCCESS! Custom textured 3D mesh written out to: {output_glb_path}")
    return True

if __name__ == "__main__":
    generate_yaru_glb()
    
