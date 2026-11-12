"""Server-Sent Events streaming for the Forge pipeline.

Wraps the pipeline's emit callback with an asyncio.Queue and yields
SSE-formatted strings (`data: {json}\n\n`) so FastAPI's
StreamingResponse can push live stage/repair/telemetry events to the
dashboard while agents are still running.
"""
import asyncio
import json

from forge.pipeline import generate_project
from forge.schemas import ProjectRequest


async def stream_project(request: ProjectRequest):
    """Async generator yielding SSE lines for one project run."""
    queue: asyncio.Queue[dict | None] = asyncio.Queue()

    async def emit(event: dict) -> None:
        await queue.put(event)

    async def runner() -> None:
        try:
            await generate_project(request, emit=emit)
        except Exception as exc:  # surface errors to the stream
            await queue.put({"type": "error", "detail": str(exc)})
        finally:
            await queue.put(None)  # sentinel

    task = asyncio.create_task(runner())
    try:
        while True:
            event = await queue.get()
            if event is None:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
