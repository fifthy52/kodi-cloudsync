#!/usr/bin/env python3
"""
GitHub Actions script to automatically update repository files.

This script:
1. Generates MD5 checksums for the main addons.xml
2. Updates repository.cloudsync files if they exist
3. Creates necessary ZIP files for distribution
"""

import os
import hashlib
import shutil
import sys

def generate_md5(file_path):
    """Generate MD5 hash of file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def main():
    """Main function called by GitHub Actions."""
    print("Starting repository update...")

    # Step 1: Update main addons.xml.md5 (should already be done by commit, but just in case)
    if os.path.exists("addons.xml"):
        md5_hash = generate_md5("addons.xml")
        with open("addons.xml.md5", "w") as f:
            f.write(f"{md5_hash} *addons.xml\n")
        print(f"Updated addons.xml.md5: {md5_hash}")

    # Step 2: Copy to repository.cloudsync if it exists
    repo_dir = "repository.cloudsync"
    if os.path.exists(repo_dir):
        print(f"Updating {repo_dir}/...")

        # Copy main addons.xml files
        if os.path.exists("addons.xml"):
            shutil.copy2("addons.xml", os.path.join(repo_dir, "addons.xml"))
            print("Copied addons.xml to repository.cloudsync/")

        if os.path.exists("addons.xml.md5"):
            shutil.copy2("addons.xml.md5", os.path.join(repo_dir, "addons.xml.md5"))
            print("Copied addons.xml.md5 to repository.cloudsync/")

    # Step 3: Create addon ZIP (should be done by GitHub Actions, but ensure it exists)
    service_dir = "service.cloudsync"
    if os.path.exists(service_dir):
        import re
        addon_xml = os.path.join(service_dir, "addon.xml")
        with open(addon_xml, "r", encoding="utf-8") as f:
            content = f.read()
            version_match = re.search(r'<addon[^>]*version="([^"]+)"', content)
            if version_match:
                version = version_match.group(1)
                zip_name = f"service.cloudsync-{version}.zip"

                # Create the ZIP if it doesn't exist
                if not os.path.exists(zip_name):
                    shutil.make_archive(
                        zip_name.replace('.zip', ''),
                        'zip',
                        '.',
                        service_dir
                    )
                    print(f"Created {zip_name}")

                # Generate MD5 for ZIP
                if os.path.exists(zip_name):
                    zip_md5 = generate_md5(zip_name)
                    with open(f"{zip_name}.md5", "w") as f:
                        f.write(f"{zip_md5}\n")
                    print(f"Generated {zip_name}.md5: {zip_md5}")

    print("Repository files updated successfully!")

if __name__ == "__main__":
    main()