import os
import json
from PIL import Image
import numpy as np

def run_yaru_gatekeeper(input_folder="input"):
    print("🤖 [Yaru 1.0] Starting Orthographic Orientation Validation...")
    
    valid_views = ['front', 'back', 'left', 'right', 'top', 'bottom']
    discovered_views = {}
    
    if not os.path.exists(input_folder):
        print(f"⚠️ Directory '/{input_folder}' not found. Creating path...")
        os.makedirs(input_folder, exist_ok=True)
        return False

    for file_name in os.listdir(input_folder):
        base, ext = os.path.splitext(file_name.lower())
        if base in valid_views and ext in ['.png', '.jpg', '.jpeg']:
            discovered_views[base] = os.path.join(input_folder, file_name)

    total_views = len(discovered_views)
    print(f"📊 Matrix Scanner localized {total_views} explicit orientation views.")

    if total_views == 0:
        print(f"❌ Error: No valid orthographic images found in /{input_folder}. Ensure file is named 'front.png'.")
        return False

    manifest = {
        "engine_version": "Yaru 1.0",
        "status": "VALIDATED",
        "configuration": f"{total_views}-view-mesh-bundle",
        "views": {}
    }

    for orientation, file_path in discovered_views.items():
        try:
            with Image.open(file_path) as img:
                img_rgb = img.convert('RGB')
                pixel_matrix = np.array(img_rgb)
                corner = pixel_matrix[0, 0]
                
                is_black = np.all(corner <= 15)
                is_white = np.all(corner >= 240)
                
                if not (is_black or is_white):
                    print(f"❌ Rule Violation: '{orientation}' background is not solid white or black. Corner: {corner}")
                    return False
                
                bg_mode = "SOLID_BLACK" if is_black else "SOLID_WHITE"
                manifest["views"][orientation] = {
                    "source_file": file_path,
                    "resolution": img.size,
                    "background_mask_target": bg_mode
                }
        except Exception as img_err:
            print(f"❌ Critical failure reading source view asset '{file_path}': {img_err}")
            return False

    os.makedirs("telemetry", exist_ok=True)
    manifest_path = os.path.join("telemetry", "ai_input_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=4)
        
    print(f"✅ Success! Structural alignment manifest generated at: {manifest_path}")
    return True

if __name__ == "__main__":
    run_yaru_gatekeeper()
    
