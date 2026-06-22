import os
import json
import zipfile

def export_to_execution_env():
    print("🚀 [Yaru 1.5] Preparing package matrix for External Execution Environment...")
    
    manifest_path = os.path.join("telemetry", "ai_input_manifest.json")
    output_package = os.path.join("telemetry", "ready_for_inference.zip")
    
    if not os.path.exists(manifest_path):
        print("❌ Export Aborted: Active 'ai_input_manifest.json' not found.")
        return False
        
    try:
        with open(manifest_path, "r") as f:
            manifest_data = json.load(f)
            
        with zipfile.ZipFile(output_package, 'w', zipfile.ZIP_DEFLATED) as zip_pack:
            zip_pack.write(manifest_path, "ai_input_manifest.json")
            
            for view_name, view_info in manifest_data.get("views", {}).items():
                local_file_path = view_info.get("source_file")
                if os.path.exists(local_file_path):
                    archive_name = f"images/{os.path.basename(local_file_path)}"
                    zip_pack.write(local_file_path, archive_name)
                    print(f"  ➕ Injected view element: {archive_name}")
                    
        print(f"🎉 Build Complete! Deployable environment asset ready at: {output_package}")
        return True
    except Exception as bridge_err:
        print(f"❌ Failed to construct environment transfer package: {bridge_err}")
        return False

if __name__ == "__main__":
    export_to_execution_env()
  
