from agents import OpenAIChatCompletionsModel, set_tracing_disabled
from openai import AsyncOpenAI

from forge.config import settings

if not settings.groq_api_key:
    raise RuntimeError("GROQ_API_KEY is missing. Add it to .env")

groq_client = AsyncOpenAI(
    api_key=settings.groq_api_key,
    base_url="https://api.groq.com/openai/v1",
)
set_tracing_disabled(True)

model = OpenAIChatCompletionsModel(
    model=settings.groq_model,
    openai_client=groq_client,
)
