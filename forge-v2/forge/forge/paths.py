from pathlib import Path, PurePosixPath

from forge.config import settings


def validate_relative_path(relative_path: str) -> Path:
    normalized = relative_path.replace("\\", "/").strip()
    if not normalized:
        raise ValueError("File path is empty.")
    if normalized.startswith("/"):
        raise ValueError("Absolute paths are not allowed.")
    if ":" in normalized:
        raise ValueError("Drive paths are not allowed.")

    parts = PurePosixPath(normalized).parts
    if not parts or any(part in ("..", ".", "") for part in parts):
        raise ValueError("Path traversal is not allowed.")

    root = settings.workspace_directory.resolve()
    destination = (root / Path(*parts)).resolve()
    if destination != root and root not in destination.parents:
        raise ValueError("File is outside the workspace.")
    return destination


def write_project_files(project_id: str, files: list[dict]) -> list[str]:
    if not project_id.isalnum():
        raise ValueError("Invalid project ID.")

    written_files = []
    base = settings.workspace_directory / project_id
    base.mkdir(parents=True, exist_ok=True)

    for f in files:
        rel_path = f["path"]
        content = f["content"]
        dest = validate_relative_path(f"{project_id}/{rel_path}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
        written_files.append(str(dest.relative_to(settings.workspace_directory)))
    return written_files
