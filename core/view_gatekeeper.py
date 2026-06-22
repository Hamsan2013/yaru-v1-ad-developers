import os
import json
from PIL import Image
import numpy as np

def run_yaru_gatekeeper():
    print("🤖 [Yaru 1.0 Gatekeeper] Scanning input environment...")
    input_folder = "input"
    target_file = os.path.join(input_folder, "front.png")
    
    if not os.path.exists(target_file):
        print(f"❌ Critical Error: '{target_file}' is missing from the repository!")
        print("Ensure you have created the 'input' folder and pushed 'front.png' inside it.")
        return False

    try:
        with Image.open(target_file) as img:
            img_rgb = img.convert('RGB')
            arr = np.array(img_rgb)
            corner_pixel = arr[0, 0]
            
            # Identify background threshold
            is_black = np.all(corner_pixel <= 20)
            is_white = np.all(corner_pixel >= 235)
            
            if not (is_black or is_white):
                print(f"⚠️ Warning: Background corner {corner_pixel} is not absolute black/white. Forcing isolation mask.")
            
            bg_mode = "SOLID_BLACK" if (is_black or np.mean(corner_pixel) < 128) else "SOLID_WHITE"
            
            manifest = {
                "engine_version": "Yaru 1.0",
                "status": "VALIDATED",
                "views": {
                    "front": {
                        "source_file": target_file,
                        "resolution": img.size,
                        "background_mask_target": bg_mode
                    }
                }
            }
            
            os.makedirs("telemetry", exist_ok=True)
            with open("telemetry/ai_input_manifest.json", "w") as f:
                json.dump(manifest, f, indent=4)
                
            print("✅ Success: Source graphic target linked and mapped to telemetry registry.")
            return True
            
    except Exception as e:
        print(f"❌ Failed to parse graphic file layers: {e}")
        return False

if __name__ == "__main__":
    run_yaru_gatekeeper()
            
