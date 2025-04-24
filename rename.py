import os
import glob

def rename_fits_files(reduction1_dir):
    event_mapping = {
        "086": "flat",
        "074": "capella"
    }
    for i in range(1, 74):
        event_mapping[f"{i:03d}"] = "algol"
    for i in range(75, 86):
        event_mapping[f"{i:03d}"] = "dark"
        
    fits_files = glob.glob(os.path.join(reduction1_dir, "event*.fits"))
    
    for file in fits_files:
        filename = os.path.basename(file)
        event_num = filename[5:8]  
        new_name = filename.replace(f"event{event_num}", event_mapping[event_num])
        new_path = os.path.join(reduction1_dir, new_name)

        try:
            os.rename(file, new_path)
            print(f"Renamed: {filename} --> {new_name}")
        except Exception as e:
            print(f"Warning: Could not rename {filename} ({e})")

reduction1_dir = "/home/manya/Documents/Reduction1/"
rename_fits_files(reduction1_dir)

