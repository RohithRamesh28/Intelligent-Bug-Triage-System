import zipfile
import os
from utils.constants import JUNK_FOLDERS, MAX_PATH_LENGTH


MAX_PATH_LENGTH = 240  # already defined

def extract_zip(zip_path, extract_to):
    extracted_files = []

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            # ✅ Skip if the full extraction path would be too long
            full_path = os.path.join(extract_to, member.filename)
            if len(full_path) > MAX_PATH_LENGTH:
                print(f"[SKIPPED] Path too long: {member.filename}")
                continue

            # Skip junk, folders, dirs (already present)
            if any(junk in member.filename for junk in JUNK_FOLDERS):
                continue
            if member.is_dir():
                continue

            # Safe extract
            target_dir = os.path.dirname(full_path)
            os.makedirs(target_dir, exist_ok=True)

            with zip_ref.open(member) as source, open(full_path, "wb") as target:
                target.write(source.read())

            extracted_files.append(member.filename)

    return extracted_files


def is_code_file(filepath):
    CODE_EXTENSIONS = [
        ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c", ".cs",
        ".rb", ".go", ".rs", ".php", ".swift", ".kt", ".m", ".scala"
    ]
    ext = os.path.splitext(filepath)[1].lower()
    return ext in CODE_EXTENSIONS

def is_valid_code_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            first_lines = f.read(1000)
            if not first_lines.strip():
                return False
            if "\x00" in first_lines:
                return False
            return True
    except:
        return False
