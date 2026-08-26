"""Import every cog and support package to catch load-time errors before deploy.

Run from the repo root: python scripts/check_imports.py
"""
import importlib
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COGS_DIR = os.path.join(ROOT_DIR, "cogs")

PACKAGES = ["birthday", "gaw", "hangman", "music", "rps"]


def cog_modules():
    for filename in sorted(os.listdir(COGS_DIR)):
        if filename.endswith(".py") and filename != "__init__.py":
            yield f"cogs.{filename[:-3]}"


def main():
    sys.path.insert(0, ROOT_DIR)

    modules = [*cog_modules(), *PACKAGES]
    failures = []

    for module in modules:
        try:
            importlib.import_module(module)
            print(f"OK    {module}")
        except Exception as exc:
            print(f"FAIL  {module}: {exc}")
            failures.append(module)

    if failures:
        print(f"\n{len(failures)} module(s) failed to import: {', '.join(failures)}")
        sys.exit(1)

    print(f"\nAll {len(modules)} modules imported successfully.")


if __name__ == "__main__":
    main()
