import os

pages_dir = 'frontend/pages'

# Map from emoji filename to new filename
renames = {
    '1_🏠_Home.py': '1_Home.py',
    '2_🚀_Analysis.py': '2_Analysis.py',
    '3_🤖_Agent_Monitor.py': '3_Agent_Monitor.py',
    '4_💬_Discussion.py': '4_Discussion.py',
    '5_📄_Reports.py': '5_Reports.py',
    '6_📤_Upload.py': '6_Upload.py',
    '7_📖_Knowledge_Wiki.py': '7_Knowledge_Wiki.py',
    '8_🔬_Research_Explorer.py': '8_Research_Explorer.py'
}

# Rename files in filesystem
for old_name, new_name in renames.items():
    old_path = os.path.join(pages_dir, old_name)
    new_path = os.path.join(pages_dir, new_name)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        print(f"Renamed {old_name} -> {new_name}")

# Files to update contents (both old and new paths since we renamed)
files_to_update = [
    'frontend/app.py',
    'frontend/pages/1_Home.py',
    'frontend/pages/2_Analysis.py'
]

# Replacements in files
replacements = {
    'pages/1_🏠_Home.py': 'pages/1_Home.py',
    'pages/2_🚀_Analysis.py': 'pages/2_Analysis.py',
    'pages/4_💬_Discussion.py': 'pages/4_Discussion.py',
    'pages/5_📄_Reports.py': 'pages/5_Reports.py'
}

for filepath in files_to_update:
    if os.path.exists(filepath):
        content = open(filepath, encoding='utf-8').read()
        for old_ref, new_ref in replacements.items():
            content = content.replace(old_ref, new_ref)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated references in {filepath}")
