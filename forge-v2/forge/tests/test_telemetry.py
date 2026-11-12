import types

from forge.config import settings
from forge.telemetry import cost_for, new_telemetry, record


def _mock_result(input_tokens, output_tokens):
    usage = types.SimpleNamespace(
        input_tokens=input_tokens, output_tokens=output_tokens
    )
    return types.SimpleNamespace(usage=usage)


def test_cost_for_uses_configured_rates():
    # 1M input + 1M output at default 0.10 / 0.15 = 0.25
    assert abs(cost_for(1_000_000, 1_000_000) - 0.25) < 1e-9


def test_cost_for_zero():
    assert cost_for(0, 0) == 0.0


def test_record_extracts_tokens_and_cost():
    result = _mock_result(1200, 800)
    usage = record(result, "Senior Developer", "code")
    assert usage.agent == "Senior Developer"
    assert usage.input_tokens == 1200
    assert usage.output_tokens == 800
    expected = 1200 / 1e6 * settings.input_cost_per_mtok + 800 / 1e6 * settings.output_cost_per_mtok
    assert abs(usage.cost_usd - expected) < 1e-9


def test_record_handles_missing_usage():
    result = types.SimpleNamespace(usage=None)
    usage = record(result, "X", "y")
    assert usage.input_tokens == 0
    assert usage.output_tokens == 0
    assert usage.cost_usd == 0.0


def test_telemetry_accumulates():
    tel = new_telemetry()
    tel.add(record(_mock_result(100, 50), "A", "s1"))
    tel.add(record(_mock_result(200, 100), "B", "s2"))
    assert tel.total_input_tokens == 300
    assert tel.total_output_tokens == 150
    assert tel.total_tokens == 450
    assert len(tel.agents) == 2
    assert tel.total_cost_usd > 0


def test_telemetry_to_dict_roundtrip():
    tel = new_telemetry()
    tel.add(record(_mock_result(10, 5), "A", "s1"))
    d = tel.to_dict()
    assert d["total_input_tokens"] == 10
    assert d["total_output_tokens"] == 5
    assert d["total_tokens"] == 15
    assert len(d["agents"]) == 1
