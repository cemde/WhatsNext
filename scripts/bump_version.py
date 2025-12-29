#!/usr/bin/env python3
"""
Bump version and create git tag consistently.

Usage:
    python scripts/bump_version.py patch  # 0.1.1 -> 0.1.2
    python scripts/bump_version.py minor  # 0.1.1 -> 0.2.0
    python scripts/bump_version.py major  # 0.1.1 -> 1.0.0
"""

import argparse
import re
import subprocess
from pathlib import Path

# Files containing version strings
VERSION_FILES = [
    ("pyproject.toml", r'^version\s*=\s*["\']([^"\']+)["\']', 'version = "{version}"'),
    ("whatsnext/cli/__init__.py", r'^__version__\s*=\s*["\']([^"\']+)["\']', '__version__ = "{version}"'),
]


def get_current_version(repo_root: Path) -> str:
    """Extract version from pyproject.toml."""
    pyproject = repo_root / "pyproject.toml"
    content = pyproject.read_text()
    match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)


def bump_version(version: str, part: str) -> str:
    """Bump version according to semver."""
    major, minor, patch = map(int, version.split("."))

    if part == "major":
        return f"{major + 1}.0.0"
    elif part == "minor":
        return f"{major}.{minor + 1}.0"
    elif part == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid version part: {part}")


def update_file(file_path: Path, pattern: str, replacement: str, new_version: str):
    """Update version in a file."""
    content = file_path.read_text()
    new_content = re.sub(pattern, replacement.format(version=new_version), content, flags=re.MULTILINE)
    file_path.write_text(new_content)


def main():
    parser = argparse.ArgumentParser(description="Bump version and create git tag")
    parser.add_argument("part", choices=["major", "minor", "patch"], help="Version part to bump")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent

    current_version = get_current_version(repo_root)
    new_version = bump_version(current_version, args.part)

    print(f"Current version: {current_version}")
    print(f"New version: {new_version}")

    if args.dry_run:
        print("\nDry run - no changes made")
        return

    # Update all version files
    updated_files = []
    for rel_path, pattern, replacement in VERSION_FILES:
        file_path = repo_root / rel_path
        if file_path.exists():
            print(f"Updating {rel_path}...")
            update_file(file_path, pattern, replacement, new_version)
            updated_files.append(str(file_path))

    # Commit and tag
    print("\nCreating git commit and tag...")
    subprocess.run(["git", "add"] + updated_files, check=True)
    subprocess.run(["git", "commit", "-m", f"Bump version to {new_version}"], check=True)
    subprocess.run(["git", "tag", "-a", f"v{new_version}", "-m", f"Release v{new_version}"], check=True)

    print(f"\nDone! Version bumped to {new_version}")
    print("\nNext steps:")
    print("  1. Review the changes: git show")
    print("  2. Push to GitHub: git push && git push --tags")
    print("  3. GitHub Actions will handle PyPI release automatically")


if __name__ == "__main__":
    main()
