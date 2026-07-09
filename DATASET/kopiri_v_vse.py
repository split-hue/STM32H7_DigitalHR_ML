import os
import shutil

SRC_DIR = r"F:\FRI_DIPLOMSKA\-delovna mapa-\DATASET\sken-OBRAZEC\izvozene_crke"
DEST_DIR = r"F:\FRI_DIPLOMSKA\-delovna mapa-\DATASET\sken-OBRAZEC\vse"

os.makedirs(DEST_DIR, exist_ok=True)

allowed_ext = ('.png', '.jpg', '.jpeg')

copied = 0

for root, dirs, files in os.walk(SRC_DIR):
    for file in files:
        if file.lower().endswith(allowed_ext):
            src_path = os.path.join(root, file)

            new_name = file
            base, ext = os.path.splitext(file)
            counter = 1

            while os.path.exists(os.path.join(DEST_DIR, new_name)):
                new_name = f"{base}_{counter}{ext}"
                counter += 1

            dest_path = os.path.join(DEST_DIR, new_name)

            shutil.copy2(src_path, dest_path)
            copied += 1

print(f"Končano. Skopiranih slik: {copied}")