import zipfile
import os
from utils.constants import JUNK_FOLDERS, MAX_PATH_LENGTH

MAX_DEPTH = 5  

def normalize_zip_path(zip_path):
    """Remove leading common folders from ZIP paths like __MACOSX/project/..."""
    parts = zip_path.strip("/").split("/")
    for i, part in enumerate(parts):
        if part not in JUNK_FOLDERS:
            return "/".join(parts[i:])  
    return os.path.basename(zip_path)  

ENV_MARKERS = {"site-packages", "Lib", "bin", "Scripts", "pyvenv.cfg", "conda-meta", "pycache"}
SKIP_EXTENSIONS = {".dll", ".pyd", ".so", ".exe", ".bin", ".lib", ".a"}

def looks_like_env(path_parts):
    return any(part in ENV_MARKERS for part in path_parts)

def extract_zip(zip_path, extract_to):
    extracted_files = []

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            path_parts = member.filename.replace("\\", "/").split("/")
            full_path = os.path.join(extract_to, member.filename)

            if len(full_path) > MAX_PATH_LENGTH:
                print(f"[SKIPPED] Path too long: {member.filename}")
                continue

            if member.is_dir():
                continue

            if any(junk in member.filename for junk in JUNK_FOLDERS):
                continue

            if looks_like_env(path_parts):
                print(f"[SKIPPED] Looks like environment folder: {member.filename}")
                continue

            _, ext = os.path.splitext(member.filename)
            if ext.lower() in SKIP_EXTENSIONS:
                print(f"[SKIPPED] Binary file: {member.filename}")
                continue

            os.makedirs(os.path.dirname(full_path), exist_ok=True)
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
            if not first_lines.strip() or "\x00" in first_lines:
                return False
            return True
    except:
        return False
