#!/usr/bin/env python3
"""
Generate Kodi repository files with proper checksums
Run this after updating addon version to update repository
"""

import os
import hashlib
import shutil

def generate_md5(file_path):
    """Generate MD5 hash of file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def update_repository():
    """Update repository files with checksums."""
    repo_dir = "repository.cloudsync"

    # Generate MD5 for addons.xml
    addons_xml = os.path.join(repo_dir, "addons.xml")
    if os.path.exists(addons_xml):
        md5_hash = generate_md5(addons_xml)

        # Write MD5 file
        with open(os.path.join(repo_dir, "addons.xml.md5"), "w") as f:
            f.write(md5_hash)

        print(f"Generated addons.xml.md5: {md5_hash}")

    # Copy latest addon zip to repository
    service_dir = "service.cloudsync"
    if os.path.exists(service_dir):
        # Read version from addon.xml
        addon_xml = os.path.join(service_dir, "addon.xml")
        with open(addon_xml, "r", encoding="utf-8") as f:
            content = f.read()
            # Extract version
            import re
            # Find the addon tag with version, not the xml version
            version_match = re.search(r'<addon[^>]*version="([^"]+)"', content)
            if version_match:
                version = version_match.group(1)

                # Create zip
                zip_name = f"service.cloudsync-{version}.zip"
                zip_path = os.path.join(repo_dir, zip_name)

                shutil.make_archive(
                    zip_path.replace('.zip', ''),
                    'zip',
                    '.',
                    service_dir
                )

                print(f"Created {zip_name} in repository")

                # Generate MD5 for zip
                if os.path.exists(zip_path):
                    zip_md5 = generate_md5(zip_path)
                    with open(f"{zip_path}.md5", "w") as f:
                        f.write(zip_md5)
                    print(f"Generated {zip_name}.md5: {zip_md5}")

def create_repository_zip():
    """Create repository zip for installation."""
    repo_dir = "repository.cloudsync"
    repo_zip = "repository.cloudsync.zip"

    if os.path.exists(repo_zip):
        os.remove(repo_zip)

    shutil.make_archive(
        repo_zip.replace('.zip', ''),
        'zip',
        '.',
        repo_dir
    )

    print(f"Created {repo_zip} for installation")

if __name__ == "__main__":
    print("Updating CloudSync repository...")
    update_repository()
    create_repository_zip()
    print("Repository update complete!")
    print("\nNext steps:")
    print("1. Commit and push changes to GitHub")
    print("2. Create release tag: git tag v4.1.2 && git push --tags")
    print("3. GitHub Actions will automatically create release")