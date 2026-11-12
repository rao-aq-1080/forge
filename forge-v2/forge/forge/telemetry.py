"""Token and cost accounting for Forge agents.

Extracts usage from an OpenAI Agents SDK RunResult defensively —
the SDK exposes ``result.usage`` (a Usage object) on most versions,
but the exact shape varies, so we fall back gracefully to zeros.
"""
from forge.config import settings
from forge.schemas import AgentUsage, Telemetry


def _extract_tokens(result) -> tuple[int, int]:
    """Return (input_tokens, output_tokens) from a RunResult, or (0, 0)."""
    usage = getattr(result, "usage", None)
    if usage is None:
        return 0, 0
    input_tokens = (
        getattr(usage, "input_tokens", None)
        or getattr(usage, "prompt_tokens", None)
        or 0
    )
    output_tokens = (
        getattr(usage, "output_tokens", None)
        or getattr(usage, "completion_tokens", None)
        or 0
    )
    return int(input_tokens or 0), int(output_tokens or 0)


def cost_for(input_tokens: int, output_tokens: int) -> float:
    """USD cost for a token pair, using configured per-million rates."""
    return (
        input_tokens / 1_000_000 * settings.input_cost_per_mtok
        + output_tokens / 1_000_000 * settings.output_cost_per_mtok
    )


def record(result, agent_name: str, stage: str) -> AgentUsage:
    """Build an AgentUsage from a RunResult."""
    input_tokens, output_tokens = _extract_tokens(result)
    return AgentUsage(
        agent=agent_name,
        stage=stage,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost_for(input_tokens, output_tokens),
    )


def new_telemetry() -> Telemetry:
    return Telemetry()
