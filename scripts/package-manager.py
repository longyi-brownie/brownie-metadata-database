#!/usr/bin/env python3
"""
Package management script for brownie-metadata-db.

Usage:
    python3 scripts/package-manager.py build
    python3 scripts/package-manager.py test
    python3 scripts/package-manager.py publish
    python3 scripts/package-manager.py version 0.1.1
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=check)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


def get_current_version():
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if match:
        return match.group(1)
    raise ValueError("Could not find version in pyproject.toml")


def update_version(new_version):
    """Update version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Update version
    content = re.sub(r'version = "[^"]+"', f'version = "{new_version}"', content)

    pyproject_path.write_text(content)
    print(f"Updated version to {new_version}")


def build_package():
    """Build the package."""
    print("🔨 Building package...")

    # Clean previous builds
    run_command(["rm", "-rf", "dist/", "build/", "*.egg-info/"], check=False)

    # Format and lint
    print("📝 Formatting code...")
    run_command(["python3", "-m", "black", "."])
    run_command(["python3", "-m", "isort", "."])

    print("🔍 Linting code...")
    run_command(["python3", "-m", "flake8", "."])

    # Build package
    print("📦 Building wheel and source distribution...")
    run_command(["python3", "-m", "build"])

    print("✅ Package built successfully!")


def test_package():
    """Test the package locally."""
    print("🧪 Testing package...")

    # Build first
    build_package()

    # Install locally
    print("📥 Installing package locally...")
    wheel_files = list(Path("dist").glob("*.whl"))
    if not wheel_files:
        print("❌ No wheel files found. Run build first.")
        return False

    run_command(
        ["python3", "-m", "pip", "install", str(wheel_files[0]), "--force-reinstall"]
    )

    # Test import
    print("🔍 Testing import...")
    result = run_command(
        [
            "python3",
            "-c",
            "import brownie_metadata_db as bmd; print(f'Version: {bmd.__version__}')",
        ]
    )

    # Test CLI
    print("🔍 Testing CLI...")
    run_command(["brownie-backup", "--help"])

    print("✅ Package test successful!")
    return True


def publish_package():
    """Publish package to PyPI."""
    print("🚀 Publishing package...")

    # Test first
    if not test_package():
        print("❌ Package test failed. Not publishing.")
        return False

    # Check if we're in a git repository
    try:
        run_command(["git", "status"], check=True)
    except subprocess.CalledProcessError:
        print("❌ Not in a git repository. Please commit changes first.")
        return False

    # Check for uncommitted changes
    result = run_command(["git", "status", "--porcelain"], check=True)
    if result.stdout.strip():
        print("❌ Uncommitted changes detected. Please commit first.")
        return False

    # Publish to PyPI
    print("📤 Uploading to PyPI...")
    run_command(["python3", "-m", "twine", "upload", "dist/*"])

    print("✅ Package published successfully!")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Package management for brownie-metadata-db"
    )
    parser.add_argument(
        "command",
        choices=["build", "test", "publish", "version"],
        help="Command to run",
    )
    parser.add_argument("--version", help="New version (for version command)")

    args = parser.parse_args()

    if args.command == "version":
        if not args.version:
            print("❌ Version required for version command")
            sys.exit(1)
        update_version(args.version)
        print(f"✅ Version updated to {args.version}")
        print("Don't forget to:")
        print("1. Update CHANGELOG.md")
        print("2. Commit changes")
        print("3. Create a git tag")
        print("4. Run: python3 scripts/package-manager.py publish")

    elif args.command == "build":
        build_package()

    elif args.command == "test":
        test_package()

    elif args.command == "publish":
        publish_package()


if __name__ == "__main__":
    main()
