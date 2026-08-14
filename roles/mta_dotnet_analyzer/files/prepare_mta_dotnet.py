#!/usr/bin/env python3
"""Stage a .NET source tree without changing or translating its source code."""

import argparse
import json
import shutil
import sys
from pathlib import Path


MARKER_NAME = ".mta-dotnet-workspace"
MARKER_VALUE = "managed by the mta_dotnet_analyzer Ansible role\n"
INVENTORY_EXTENSIONS = {
    "solutions": ".sln",
    "csharp_projects": ".csproj",
    "visual_basic_projects": ".vbproj",
    "csharp_files": ".cs",
    "visual_basic_files": ".vb",
    "configuration_files": ".config",
    "assemblies": ".dll",
    "wsdl_files": ".wsdl",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create a clean MTA input tree and an analysis-scope manifest."
    )
    parser.add_argument("--source", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--staged-source", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--exclude-json", default="[]")
    return parser.parse_args()


def is_relative_to(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_paths(source, workspace, staged_source, manifest):
    if not source.is_dir():
        raise ValueError(f"Source directory does not exist: {source}")
    if source == workspace or is_relative_to(workspace, source):
        raise ValueError("The managed workspace must not be inside the source tree.")
    if is_relative_to(source, workspace):
        raise ValueError("The source tree must not be inside the managed workspace.")
    if staged_source.parent != workspace:
        raise ValueError("The staged source directory must be a direct child of the workspace.")
    if manifest.parent != workspace:
        raise ValueError("The manifest must be written directly under the workspace.")


def prepare_workspace(workspace, staged_source):
    marker = workspace / MARKER_NAME
    if workspace.exists():
        if not marker.is_file() or marker.read_text(encoding="utf-8") != MARKER_VALUE:
            raise ValueError(
                f"Refusing to reuse unmarked workspace directory: {workspace}"
            )
        if staged_source.exists():
            if staged_source.is_symlink() or not staged_source.is_dir():
                raise ValueError(f"Unsafe staged source path: {staged_source}")
            shutil.rmtree(staged_source)
    else:
        workspace.mkdir(parents=True, mode=0o750)
        marker.write_text(MARKER_VALUE, encoding="utf-8")


def copy_source(source, staged_source, excluded_directories):
    excluded = set(excluded_directories)

    def ignore(_directory, names):
        return [name for name in names if name in excluded]

    shutil.copytree(
        source,
        staged_source,
        symlinks=False,
        ignore=ignore,
        copy_function=shutil.copy2,
    )


def inventory(staged_source):
    matches = {name: [] for name in INVENTORY_EXTENSIONS}
    for path in sorted(staged_source.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        for name, extension in INVENTORY_EXTENSIONS.items():
            if suffix == extension:
                matches[name].append(path.relative_to(staged_source).as_posix())

    if not (matches["solutions"] or matches["csharp_projects"]):
        csharp_entrypoint = None
    elif matches["solutions"]:
        csharp_entrypoint = matches["solutions"][0]
    else:
        csharp_entrypoint = matches["csharp_projects"][0]

    return {
        "source_kind": (
            "mixed"
            if matches["csharp_files"] and matches["visual_basic_files"]
            else "csharp"
            if matches["csharp_files"]
            else "visual-basic"
            if matches["visual_basic_files"]
            else "unknown"
        ),
        "mta_csharp_ready": bool(
            matches["csharp_files"]
            and (matches["solutions"] or matches["csharp_projects"])
        ),
        "csharp_entrypoint": csharp_entrypoint,
        "counts": {name: len(paths) for name, paths in matches.items()},
        "files": matches,
    }


def main():
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    workspace = Path(args.workspace).expanduser().resolve()
    staged_source = Path(args.staged_source).expanduser().resolve()
    manifest = Path(args.manifest).expanduser().resolve()
    excluded_directories = json.loads(args.exclude_json)
    if not isinstance(excluded_directories, list) or not all(
        isinstance(item, str) and item for item in excluded_directories
    ):
        raise ValueError("--exclude-json must be a JSON array of directory names.")

    validate_paths(source, workspace, staged_source, manifest)
    prepare_workspace(workspace, staged_source)
    copy_source(source, staged_source, excluded_directories)
    result = inventory(staged_source)
    result.update(
        {
            "source_path": str(source),
            "staged_source_path": str(staged_source),
            "excluded_directories": sorted(set(excluded_directories)),
        }
    )
    manifest.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(2)
