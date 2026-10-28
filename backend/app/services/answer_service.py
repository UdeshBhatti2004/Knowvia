import time

from google.genai import errors

from app.core.ai_client import client


class AnswerQuotaExceeded(Exception):
    """The daily limit for answer generation has been used up."""


def _is_daily_quota_error(exc) -> bool:
    # Google names the daily limit in the error text ("...PerDay..." in the
    # quota id, "requests per day" in the description). Retrying cannot help.
    text = str(exc).lower().replace(" ", "")
    return exc.code == 429 and "perday" in text


def generate_answer(question: str, context: str) -> str:
    max_attempts = 3

    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=f"""
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
                """,
            )

            if not response.text:
                raise RuntimeError("Gemini returned an empty answer.")

            return response.text.strip()

        except errors.APIError as exc:
            print(
                f"Gemini generation failed "
                f"(attempt {attempt + 1}): {exc}"
            )

            if _is_daily_quota_error(exc):
                raise AnswerQuotaExceeded(
                    "Daily Gemini answer limit reached."
                ) from exc

            if exc.code not in (429, 500, 502, 503, 504):
                raise

            if attempt == max_attempts - 1:
                raise

            time.sleep(2 ** attempt)

        except Exception as exc:
            print(f"Unexpected error during answer generation: {exc}")
            raise