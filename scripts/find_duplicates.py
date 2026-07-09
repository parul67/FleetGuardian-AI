import os
import json

def find_duplicates(root_path):
    basename_map = {}
    for dirpath, _, filenames in os.walk(root_path):
        for name in filenames:
            # Skip hidden files and large directories like node_modules, venv
            if name.startswith('.'):
                continue
            full_path = os.path.join(dirpath, name)
            basename_map.setdefault(name, []).append(full_path)
    # Keep only groups with more than one occurrence
    dup_groups = {name: paths for name, paths in basename_map.items() if len(paths) > 1}
    return dup_groups

if __name__ == "__main__":
    # Assume script is located in <project_root>/scripts
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    duplicates = find_duplicates(project_root)
    if not duplicates:
        print("No duplicate filenames found.")
    else:
        print("Duplicate filename groups:")
        for name, paths in duplicates.items():
            print(f"\n{name} ({len(paths)} copies):")
            for p in paths:
                print(f"  {p}")
