#!/usr/bin/env python3
"""Regression checks for the MTA .NET source-staging helper."""

import json
import subprocess
import tempfile
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "roles/mta_dotnet_analyzer/files/prepare_mta_dotnet.py"


def run_helper(source, workspace):
    staged = workspace / "source"
    manifest = workspace / "analysis-scope.json"
    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "--source",
            str(source),
            "--workspace",
            str(workspace),
            "--staged-source",
            str(staged),
            "--manifest",
            str(manifest),
            "--exclude-json",
            '["bin", "obj", ".git"]',
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout), staged, manifest


def main():
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        source = root / "application"
        workspace = root / "output" / "workspace"
        source.mkdir()
        (source / "Application.sln").write_text("Solution\n", encoding="utf-8")
        (source / "Application.csproj").write_text("<Project />\n", encoding="utf-8")
        (source / "Program.cs").write_text("using System.Web;\n", encoding="utf-8")
        (source / "Legacy.vb").write_text("Public Class Legacy\nEnd Class\n", encoding="utf-8")
        (source / "bin").mkdir()
        (source / "bin" / "generated.dll").write_bytes(b"generated")

        result, staged, manifest = run_helper(source, workspace)
        assert result["source_kind"] == "mixed"
        assert result["mta_csharp_ready"] is True
        assert result["csharp_entrypoint"] == "Application.sln"
        assert result["counts"]["csharp_projects"] == 1
        assert result["counts"]["visual_basic_files"] == 1
        assert not (staged / "bin").exists()
        assert manifest.is_file()

        (source / "Second.cs").write_text("public class Second {}\n", encoding="utf-8")
        second_result, _, _ = run_helper(source, workspace)
        assert second_result["counts"]["csharp_files"] == 2

    print("prepare_mta_dotnet.py: all checks passed")


if __name__ == "__main__":
    main()
