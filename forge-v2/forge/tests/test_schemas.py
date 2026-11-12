import pytest
from pydantic import ValidationError

from forge.schemas import CodeBundle, GeneratedFile, ProjectRequest, RepairBundle


def test_valid_project_request():
    request = ProjectRequest(
        requirement="Build a Python document management application.",
        project_name="Document Manager",
    )
    assert request.project_name == "Document Manager"
    assert request.preferred_language == "Python"


def test_short_requirement_is_rejected():
    with pytest.raises(ValidationError):
        ProjectRequest(requirement="Too short")


def test_long_requirement_is_rejected():
    with pytest.raises(ValidationError):
        ProjectRequest(requirement="x" * 13000)


def test_generated_file():
    f = GeneratedFile(path="main.py", content="print('Hello')")
    assert f.path == "main.py"
    assert "Hello" in f.content


def test_empty_file_path_is_rejected():
    with pytest.raises(ValidationError):
        GeneratedFile(path="", content="something")


def test_file_path_traversal_is_rejected():
    with pytest.raises(ValidationError):
        GeneratedFile(path="../etc/passwd", content="x")


def test_absolute_file_path_is_rejected():
    with pytest.raises(ValidationError):
        GeneratedFile(path="/etc/passwd", content="x")


def test_code_bundle():
    bundle = CodeBundle(
        summary="A bundle",
        files=[GeneratedFile(path="main.py", content="print(1)")],
        setup_instructions="pip install x",
    )
    assert len(bundle.files) == 1
    assert bundle.setup_instructions == "pip install x"


def test_code_bundle_default_empty_files():
    bundle = CodeBundle(summary="Empty")
    assert bundle.files == []


def test_repair_bundle_includes_complete_code_fields():
    bundle = RepairBundle(
        summary="Fixed",
        files=[{"path": "main.py", "content": "print('ok')"}],
        fixes_applied=["fixed output formatting"],
    )
    assert bundle.fixes_applied == ["fixed output formatting"]
