import pytest

from forge.json_utils import extract_json


def test_extract_plain_json():
    result = extract_json('{"name": "test", "count": 5}')
    assert result["name"] == "test"
    assert result["count"] == 5


def test_extract_markdown_json():
    result = extract_json('```json\n{"status": "success"}\n```')
    assert result["status"] == "success"


def test_extract_json_without_language_tag():
    result = extract_json('```\n{"x": 1}\n```')
    assert result["x"] == 1


def test_extract_json_from_extra_text():
    result = extract_json('Here is the result:\n{"valid": true}\nDone.')
    assert result["valid"] is True


def test_invalid_json_raises_error():
    with pytest.raises(ValueError):
        extract_json("This is not JSON at all.")


def test_json_array_is_rejected():
    with pytest.raises(ValueError):
        extract_json("[1, 2, 3]")


def test_json_with_nested_objects():
    result = extract_json('{"a": {"b": {"c": 1}}}')
    assert result["a"]["b"]["c"] == 1
