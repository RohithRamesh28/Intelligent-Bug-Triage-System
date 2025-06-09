import zipfile
import os
from utils.constants import JUNK_FOLDERS, MAX_PATH_LENGTH

def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            # Skip too long paths → avoid Windows path error
            if len(member.filename) > MAX_PATH_LENGTH:
                continue
            
            # Skip known junk folders
            if any(junk_folder in member.filename for junk_folder in JUNK_FOLDERS):
                continue
            
            # Skip directory entries
            if member.is_dir():
                continue
            
            # Safe extract → create needed folders first
            target_path = os.path.join(extract_to, member.filename)
            target_dir = os.path.dirname(target_path)
            os.makedirs(target_dir, exist_ok=True)

            with zip_ref.open(member) as source, open(target_path, "wb") as target:
                target.write(source.read())

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
