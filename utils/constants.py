# utils/constants.py

# Folders we want to skip during extraction / walk
JUNK_FOLDERS = {
    "node_modules",
    ".git",
    "dist",
    "__pycache__",
    "venv",
    ".idea",
    ".vscode",
    "build",
    "target",
    "eslint.config.js",
    "vite.config.js"
}

# Max path length we want to allow (Windows safe limit ~240 chars is good)
MAX_PATH_LENGTH = 240
