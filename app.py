import os
import re
from datetime import datetime, timedelta

# 🔹 GitHub details
USERNAME = "your-username"
REPO = "your-repo"
BRANCH = "main"  # or "master"

BASE_DIR = "."
HIGHLIGHT_DAYS = 7

FOLDER_NAMES = {
    "ML": "Machine Learning",
    "NLP": "Natural Language Processing",
    "CV": "Computer Vision",
    "DL": "Deep Learning",
    "Data": "Data Analysis",
    "Misc": "Miscellaneous"
}

def prettify(name: str) -> str:
    name = os.path.splitext(name)[0]
    name = name.replace("_", " ").replace("-", " ")
    return name.title()

def pretty_folder(name: str) -> str:
    return FOLDER_NAMES.get(name, prettify(name))

def get_timestamp(path: str) -> str:
    mtime = os.path.getmtime(path)
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")

def is_recent(path: str) -> bool:
    mtime = os.path.getmtime(path)
    return datetime.now() - datetime.fromtimestamp(mtime) <= timedelta(days=HIGHLIGHT_DAYS)

def walk_folders(base_dir):
    folders = {}
    for entry in sorted(os.listdir(base_dir)):
        full_path = os.path.join(base_dir, entry)
        if os.path.isdir(full_path):
            subfolders = walk_folders(full_path)
            if subfolders:
                folders[entry] = subfolders
        elif entry.endswith(".ipynb"):
            folders.setdefault("_notebooks", []).append(entry)
    return folders

def build_toc(folders_dict, base_path="", depth=2):
    lines = []
    indent = "  " * (depth - 2)
    for folder in sorted(folders_dict.keys()):
        if folder == "_notebooks":
            continue
        folder_title = pretty_folder(folder)
        anchor = folder_title.lower().replace(" ", "-")
        lines.append(f"{indent}- [{folder_title}](#{anchor})")
        lines.extend(build_toc(folders_dict[folder], os.path.join(base_path, folder), depth + 1))
    return lines

def build_section_collapsible(folders_dict, base_path="", depth=2):
    lines = []
    heading = "#" * depth
    for folder in sorted(folders_dict.keys()):
        if folder == "_notebooks":
            for f in sorted(folders_dict[folder], key=lambda x: prettify(x).lower()):
                path = os.path.join(base_path, f)
                pretty_name = prettify(f)
                timestamp = get_timestamp(path)
                recent = is_recent(path)
                highlight = "⭐ " if recent else ""
                url = f"https://colab.research.google.com/github/{USERNAME}/{REPO}/blob/{BRANCH}/{path}"
                lines.append(f"- {highlight}[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url}) {pretty_name} _(Last updated: {timestamp})_")
        else:
            folder_title = pretty_folder(folder)
            if depth == 2:
                # Top-level folder: normal heading
                lines.append(f"{heading} 📂 {folder_title}")
                lines.extend(build_section_collapsible(folders_dict[folder], os.path.join(base_path, folder), depth + 1))
            else:
                # Subfolder: collapsible
                lines.append(f"<details>")
                lines.append(f"<summary>📂 {folder_title}</summary>\n")
                lines.extend(build_section_collapsible(folders_dict[folder], os.path.join(base_path, folder), depth + 1))
                lines.append("</details>\n")
    return lines

# Build folder tree
folders_tree = walk_folders(BASE_DIR)

# Build auto-generated section
auto_lines = ["<!-- NOTEBOOKS-START -->", "## 📑 Table of Contents"]
auto_lines.extend(build_toc(folders_tree))
auto_lines.append("\n---\n")
auto_lines.extend(build_section_collapsible(folders_tree))
auto_lines.append("\n<!-- NOTEBOOKS-END -->")
auto_section = "\n".join(auto_lines)

# Read existing README.md
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()
    pattern = r"<!-- NOTEBOOKS-START -->.*?<!-- NOTEBOOKS-END -->"
    if re.search(pattern, content, flags=re.DOTALL):
        new_content = re.sub(pattern, auto_section, content, flags=re.DOTALL)
    else:
        new_content = content.strip() + "\n\n" + auto_section
else:
    new_content = auto_section

# Save updated README.md
with open("README.md", "w", encoding="utf-8") as f:
    f.write(new_content)

print("✅ README.md updated with collapsible subfolders! Recent notebooks highlighted with ⭐")
