"""Sequential multi-agent orchestration with RAG, auto-repair loop,
token/cost telemetry, and live event emission for SSE streaming."""
import uuid
from typing import Any, Awaitable, Callable

from agents import Runner
from pydantic import BaseModel

from forge.agents import (
    code_reviewer,
    developer,
    product_manager,
    qa_engineer,
    repair_developer,
    software_architect,
)
from forge.config import settings
from forge.json_utils import extract_json
from forge.rag import retrieve
from forge.schemas import ProjectRequest, RepairIteration
from forge.storage import save_project
from forge.telemetry import new_telemetry, record

EmitFn = Callable[[dict], Awaitable[None]] | None


async def _run(agent, prompt: str) -> tuple[dict, Any]:
    """Run one agent and return (parsed_json_dict, raw_result)."""
    retry_prompt = (
        "\n\nYour previous response was not valid JSON. Retry the same task and "
        "return only one complete, valid JSON object. Escape all newlines and "
        "quotes inside string values."
    )
    for attempt in range(2):
        result = await Runner.run(agent, prompt)
        if isinstance(result.final_output, BaseModel):
            return result.final_output.model_dump(), result
        if isinstance(result.final_output, str):
            try:
                return extract_json(result.final_output), result
            except ValueError as exc:
                if attempt == 1:
                    raise ValueError(
                        f"{agent.name} returned invalid JSON after retry: {exc}"
                    ) from exc
                prompt += retry_prompt
                continue
        raise ValueError(f"{agent.name} returned an unexpected output type.")
    raise RuntimeError(f"{agent.name} did not produce a result.")


async def generate_project(
    request: ProjectRequest,
    emit: EmitFn = None,
) -> dict:
    async def _emit(ev: dict) -> None:
        if emit is not None:
            await emit(ev)

    telemetry = new_telemetry()
    project_id = uuid.uuid4().hex[:12]

    # ---- Feature: RAG over past projects ----
    rag_context: list[dict] = []
    if settings.enable_rag and request.enable_rag:
        await _emit({"type": "stage_start", "stage": "rag", "agent": "RAG Retriever"})
        try:
            rag_context = retrieve(request.requirement, settings.rag_top_k)
        except Exception:
            rag_context = []
        await _emit(
            {"type": "stage_end", "stage": "rag", "data": {"matches": len(rag_context)}}
        )

    rag_block = ""
    if rag_context:
        rag_block = "\n\nRelevant prior approved projects for inspiration (do NOT copy):\n"
        for m in rag_context:
            rag_block += (
                f"- {m['meta'].get('project_name', '')} "
                f"(score {m['score']}): {m['snippet']}\n"
            )

    # ---- Stage 1: Product Manager ----
    await _emit({"type": "stage_start", "stage": "plan", "agent": product_manager.name})
    plan, raw = await _run(
        product_manager,
        f"Requirement: {request.requirement}\n"
        f"Additional context: {request.additional_context}{rag_block}",
    )
    usage = record(raw, product_manager.name, "plan")
    telemetry.add(usage)
    await _emit(
        {"type": "stage_end", "stage": "plan", "data": plan, "usage": usage.model_dump()}
    )

    # ---- Stage 2: Architect ----
    await _emit(
        {"type": "stage_start", "stage": "architecture", "agent": software_architect.name}
    )
    arch, raw = await _run(
        software_architect,
        f"Requirement: {request.requirement}\n"
        f"Preferred language: {request.preferred_language}\n"
        f"Development plan: {plan}{rag_block}",
    )
    usage = record(raw, software_architect.name, "architecture")
    telemetry.add(usage)
    await _emit(
        {"type": "stage_end", "stage": "architecture", "data": arch, "usage": usage.model_dump()}
    )

    # ---- Stage 3: Developer ----
    await _emit({"type": "stage_start", "stage": "code", "agent": developer.name})
    code, raw = await _run(
        developer,
        f"Development plan: {plan}\n\n"
        f"Architecture: {arch}\n\n"
        f"Preferred language: {request.preferred_language}",
    )
    usage = record(raw, developer.name, "code")
    telemetry.add(usage)
    await _emit(
        {"type": "stage_end", "stage": "code", "data": code, "usage": usage.model_dump()}
    )

    # ---- Stage 4: QA ----
    await _emit({"type": "stage_start", "stage": "qa", "agent": qa_engineer.name})
    qa, raw = await _run(
        qa_engineer,
        f"Development plan: {plan}\n\nArchitecture: {arch}\n\nGenerated code: {code}",
    )
    usage = record(raw, qa_engineer.name, "qa")
    telemetry.add(usage)
    await _emit(
        {"type": "stage_end", "stage": "qa", "data": qa, "usage": usage.model_dump()}
    )

    # ---- Stage 5: Review ----
    await _emit({"type": "stage_start", "stage": "review", "agent": code_reviewer.name})
    review, raw = await _run(
        code_reviewer,
        f"Generated code: {code}\n\nQA report: {qa}",
    )
    usage = record(raw, code_reviewer.name, "review")
    telemetry.add(usage)
    await _emit(
        {"type": "stage_end", "stage": "review", "data": review, "usage": usage.model_dump()}
    )

    # ---- Feature: Auto-repair loop ----
    iterations: list[dict] = []
    if settings.enable_repair_loop and request.enable_repair_loop:
        score = int(review.get("overall_score", 0))
        iteration = 0
        while (
            iteration < settings.max_repair_iterations
            and score < settings.repair_score_threshold
        ):
            iteration += 1
            score_before = score
            await _emit(
                {
                    "type": "repair_start",
                    "iteration": iteration,
                    "score_before": score_before,
                    "agent": repair_developer.name,
                }
            )
            fixed, raw = await _run(
                repair_developer,
                f"Current code: {code}\n\n"
                f"QA report: {qa}\n\n"
                f"Code review (fix these): {review}",
            )
            usage = record(raw, repair_developer.name, f"repair_{iteration}")
            telemetry.add(usage)
            # Replace code bundle with repaired version
            if fixed.get("files"):
                code = {
                    k: fixed.get(k, code.get(k, ""))
                    for k in ("summary", "files", "setup_instructions")
                }
                code.setdefault("summary", fixed.get("summary", "Repaired bundle"))
            # Re-run QA on repaired code
            qa, raw_qa = await _run(
                qa_engineer,
                f"Development plan: {plan}\n\nArchitecture: {arch}\n\nRepaired code: {code}",
            )
            telemetry.add(record(raw_qa, qa_engineer.name, f"repair_qa_{iteration}"))
            # Re-run review on repaired code
            review, raw_rev = await _run(
                code_reviewer,
                f"Repaired code: {code}\n\nQA report: {qa}",
            )
            telemetry.add(record(raw_rev, code_reviewer.name, f"repair_review_{iteration}"))
            score_after = int(review.get("overall_score", 0))
            it = RepairIteration(
                iteration=iteration,
                score_before=score_before,
                score_after=score_after,
                findings_addressed=len(fixed.get("fixes_applied", [])),
                qa_summary=qa.get("test_strategy", "")[:200],
                review_summary=review.get("summary", "")[:200],
                improved=score_after > score_before,
            )
            iterations.append(it.model_dump())
            await _emit(
                {
                    "type": "repair_end",
                    "iteration": iteration,
                    "score_before": score_before,
                    "score_after": score_after,
                    "improved": it.improved,
                    "fixes_applied": fixed.get("fixes_applied", []),
                }
            )
            score = score_after

    result = {
        "plan": plan,
        "architecture": arch,
        "code": code,
        "qa": qa,
        "review": review,
        "telemetry": telemetry.to_dict(),
        "iterations": iterations,
        "rag_context": rag_context,
    }

    save_project(
        project_id=project_id,
        project_name=request.project_name,
        requirement=request.requirement,
        status="awaiting_approval",
        result=result,
    )

    await _emit(
        {"type": "telemetry", "telemetry": telemetry.to_dict()}
    )
    await _emit(
        {
            "type": "done",
            "project_id": project_id,
            "status": "awaiting_approval",
            "iterations": len(iterations),
            "final_score": review.get("overall_score", 0),
        }
    )

    return {"project_id": project_id, "status": "awaiting_approval", "result": result}
