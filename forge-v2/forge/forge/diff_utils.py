"""Unified-diff utilities for the project diff viewer.

Compares two sets of files ({path: content}) using stdlib difflib.
Used both for repair-iteration diffs (current code vs previous code)
and for cross-project diffs (current awaiting-approval code vs the
last approved snapshot).
"""
import difflib

from forge.schemas import FileDiff, ProjectDiff


def files_to_dict(files: list[dict]) -> dict[str, str]:
    """Normalize a list of {'path','content'} dicts into a dict."""
    out: dict[str, str] = {}
    for f in files or []:
        path = f.get("path", "")
        if not path:
            continue
        out[path] = f.get("content", "")
    return out


def _status(old: str | None, new: str | None) -> str:
    if old is None and new is not None:
        return "added"
    if old is not None and new is None:
        return "removed"
    if old == new:
        return "unchanged"
    return "modified"


def compute_file_diffs(old_files: list[dict], new_files: list[dict]) -> list[FileDiff]:
    old = files_to_dict(old_files)
    new = files_to_dict(new_files)
    all_paths = sorted(set(old) | set(new))
    diffs: list[FileDiff] = []
    for path in all_paths:
        old_text = old.get(path)
        new_text = new.get(path)
        status = _status(old_text, new_text)
        if status == "unchanged":
            diffs.append(FileDiff(path=path, status="unchanged"))
            continue
        old_lines = (old_text or "").splitlines(keepends=True)
        new_lines = (new_text or "").splitlines(keepends=True)
        patch = "\n".join(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                lineterm="",
            )
        )
        additions = sum(
            1
            for line in patch.splitlines()
            if line.startswith("+") and not line.startswith("+++")
        )
        deletions = sum(
            1
            for line in patch.splitlines()
            if line.startswith("-") and not line.startswith("---")
        )
        diffs.append(
            FileDiff(
                path=path,
                status=status,
                additions=additions,
                deletions=deletions,
                patch=patch,
            )
        )
    return diffs


def build_project_diff(
    project_id: str,
    old_files: list[dict],
    new_files: list[dict],
    base_label: str = "approved_snapshot",
    comparison_label: str = "current",
) -> ProjectDiff:
    files = compute_file_diffs(old_files, new_files)
    total_add = sum(f.additions for f in files)
    total_del = sum(f.deletions for f in files)
    return ProjectDiff(
        project_id=project_id,
        base=base_label,
        comparison=comparison_label,
        files=files,
        total_additions=total_add,
        total_deletions=total_del,
    )


def summarize_diffs(files: list[FileDiff]) -> dict:
    """Return {added, removed, modified, unchanged, additions, deletions}."""
    counts = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}
    additions = deletions = 0
    for f in files:
        counts[f.status] = counts.get(f.status, 0) + 1
        additions += f.additions
        deletions += f.deletions
    return {**counts, "additions": additions, "deletions": deletions}
