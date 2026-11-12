from forge.diff_utils import build_project_diff, compute_file_diffs, files_to_dict, summarize_diffs


def test_files_to_dict():
    files = [{"path": "a.py", "content": "x"}, {"path": "b.py", "content": "y"}]
    d = files_to_dict(files)
    assert d == {"a.py": "x", "b.py": "y"}


def test_added_file():
    diffs = compute_file_diffs([], [{"path": "new.py", "content": "print(1)"}])
    assert len(diffs) == 1
    assert diffs[0].status == "added"
    assert diffs[0].additions >= 1
    assert diffs[0].deletions == 0


def test_removed_file():
    diffs = compute_file_diffs([{"path": "old.py", "content": "print(1)"}], [])
    assert diffs[0].status == "removed"
    assert diffs[0].deletions >= 1


def test_modified_file():
    old = [{"path": "m.py", "content": "print('hi')"}]
    new = [{"path": "m.py", "content": "print('bye')"}]
    diffs = compute_file_diffs(old, new)
    assert diffs[0].status == "modified"
    assert diffs[0].additions >= 1
    assert diffs[0].deletions >= 1
    assert "print('bye')" in diffs[0].patch
    assert "print('hi')" in diffs[0].patch


def test_unchanged_file():
    files = [{"path": "u.py", "content": "same"}]
    diffs = compute_file_diffs(files, files)
    assert diffs[0].status == "unchanged"
    assert diffs[0].additions == 0
    assert diffs[0].deletions == 0
    assert diffs[0].patch == ""


def test_build_project_diff_totals():
    old = [{"path": "a.py", "content": "1\n2\n3"}, {"path": "b.py", "content": "keep"}]
    new = [{"path": "a.py", "content": "1\n2\n3\n4"}, {"path": "c.py", "content": "new"}]
    diff = build_project_diff("proj1", old, new, "approved", "current")
    paths = {f.path: f.status for f in diff.files}
    assert paths["a.py"] == "modified"
    assert paths["b.py"] == "removed"
    assert paths["c.py"] == "added"
    assert diff.total_additions >= 2
    assert diff.total_deletions >= 0


def test_summarize_diffs():
    diffs = compute_file_diffs(
        [{"path": "a.py", "content": "x"}, {"path": "b.py", "content": "y"}],
        [{"path": "a.py", "content": "z"}, {"path": "c.py", "content": "new"}],
    )
    summary = summarize_diffs(diffs)
    assert summary["modified"] == 1
    assert summary["removed"] == 1
    assert summary["added"] == 1
    assert summary["unchanged"] == 0
    assert summary["additions"] >= 1
