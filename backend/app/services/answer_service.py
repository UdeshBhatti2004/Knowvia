import time

import httpx
from google.genai import errors, types

from app.core.ai_client import client

PRIMARY_MODEL = "gemini-3.5-flash-lite"
FALLBACK_MODEL = "gemini-2.5-flash"
CALL_TIMEOUT_MS = 12_000
TOTAL_BUDGET_SECONDS = 30
ATTEMPTS_PER_MODEL = 2


class AnswerQuotaExceeded(Exception):
    """The daily limit for answer generation has been used up."""


def _is_daily_quota_error(exc) -> bool:
    # Google names the daily limit in the error text ("...PerDay..." in the
    # quota id, "requests per day" in the description). Retrying cannot help.
    text = str(exc).lower().replace(" ", "")
    return exc.code == 429 and "perday" in text


def _build_prompt(question: str, context: str) -> str:
    return f"""
                You are a polite, professional, and helpful AI assistant for a business knowledge base.

                Answer user questions using only the information provided in the context.

                Rules:
                1. Use only facts explicitly supported by the context.
                2. Never invent facts, prices, dates, policies, or contact details.
                3. Answer the user's actual question directly and concisely.
                4. Preserve policy conditions, restrictions, and time limits accurately.
                5. If information is missing, say:
                "Sorry, I couldn't find relevant information in the available documents."
                6. If the context contains conflicting information, explain the conflict.
                7. Do not mention similarity scores, embeddings, or internal implementation details.

                Context:
                {context}

                Question:
                {question}

                Answer:
                """


def generate_answer(question: str, context: str) -> str:
    prompt = _build_prompt(question, context)
    config = types.GenerateContentConfig(
        http_options=types.HttpOptions(timeout=CALL_TIMEOUT_MS)
    )
    deadline = time.monotonic() + TOTAL_BUDGET_SECONDS
    last_exc: Exception | None = None

    for model in (PRIMARY_MODEL, FALLBACK_MODEL):
        for attempt in range(ATTEMPTS_PER_MODEL):
            if time.monotonic() >= deadline:
                break

            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )

                if not response.text:
                    raise RuntimeError("Gemini returned an empty answer.")

                return response.text.strip()

            except errors.APIError as exc:
                print(
                    f"Gemini generation failed "
                    f"({model}, attempt {attempt + 1}): {exc}"
                )

                if _is_daily_quota_error(exc):
                    raise AnswerQuotaExceeded(
                        "Daily Gemini answer limit reached."
                    ) from exc

                if exc.code not in (429, 500, 502, 503, 504):
                    raise

                last_exc = exc

            except httpx.TimeoutException as exc:
                print(
                    f"Gemini timed out "
                    f"({model}, attempt {attempt + 1}): {exc}"
                )
                last_exc = exc

            except Exception as exc:
                print(f"Unexpected error during answer generation: {exc}")
                raise

            if attempt < ATTEMPTS_PER_MODEL - 1:
                time.sleep(1)

    if last_exc is not None:
        raise last_exc

    raise RuntimeError("Answer generation ran out of time.")