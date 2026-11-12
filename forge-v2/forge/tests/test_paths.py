import pytest

from forge.paths import validate_relative_path


def test_valid_path():
    result = validate_relative_path("src/main.py")
    assert result.name == "main.py"
    assert result.parent.name == "src"


def test_valid_nested_path():
    result = validate_relative_path("app/services/auth.py")
    assert result.name == "auth.py"


def test_reject_parent_directory():
    with pytest.raises(ValueError):
        validate_relative_path("../secret.txt")


def test_reject_absolute_path():
    with pytest.raises(ValueError):
        validate_relative_path("/etc/passwd")


def test_reject_windows_drive_path():
    with pytest.raises(ValueError):
        validate_relative_path("C:\\Windows\\system.ini")


def test_reject_empty_path():
    with pytest.raises(ValueError):
        validate_relative_path("")


def test_reject_dot_path():
    with pytest.raises(ValueError):
        validate_relative_path(".")


def test_reject_double_dot_in_middle():
    with pytest.raises(ValueError):
        validate_relative_path("src/../etc/passwd")
