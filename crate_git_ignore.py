# create_gitignore.py
import os

GITIGNORE_CONTENT = """
# -----------------------------
# Python 기본
# -----------------------------
__pycache__/
*.pyc
*.pyo
*.pyd
*.pdb
*.pkl
*.tmp

# -----------------------------
# Virtual Environment
# -----------------------------
.venv/
venv/
env/

# -----------------------------
# IDE / OS 파일
# -----------------------------
.DS_Store
.idea/
.vscode/
*.swp
*.swo

# -----------------------------
# Qt / PyQt / UI
# -----------------------------
*.qmlc
*.jsc*
*.qrc~
*.ui~
*.pro.user
*.moc

# -----------------------------
# Logs / Temp
# -----------------------------
logs/
*.log
*.sqlite
*.db

# -----------------------------
# Cache
# -----------------------------
.cache/
__pycache__/

# -----------------------------
# Build / Distribution
# -----------------------------
dist/
build/
*.egg-info/

# -----------------------------
# Large data (필요한 경우)
# -----------------------------
*.csv
*.zip
*.tar
*.tar.gz
*.bak
"""

def create_gitignore():
    path = ".gitignore"

    if os.path.exists(path):
        print("⚠️  .gitignore already exists. Overwriting...")
    else:
        print("📄 Creating .gitignore ...")

    with open(path, "w", encoding="utf-8") as f:
        f.write(GITIGNORE_CONTENT.strip() + "\n")

    print("✅ .gitignore created successfully!")


if __name__ == "__main__":
    create_gitignore()
