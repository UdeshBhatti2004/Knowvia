import asyncio
from contextlib import suppress

# Seconds to wait before each automatic retry (about one rate-limit window).
RETRY_DELAYS = (65, 65, 65, 65, 65)


def _run_on_ready(on_ready):
    """Run the optional "knowledge base is ready" hook.

    A problem in the hook is only logged. The knowledge base itself is
    fine at this point, so it must not trigger another retry.
    """
    if on_ready is None:
        return

    try:
        on_ready()
    except Exception as exc:
        print(f"Post-startup recovery failed: {exc}")


async def _retry_in_background(refresh, delays, on_ready=None):
    for delay in delays:
        await asyncio.sleep(delay)

        try:
            await asyncio.to_thread(refresh)
        except Exception as exc:
            print(f"Knowledge base retry failed: {exc}")
        else:
            print("Knowledge base is ready after retry.")
            await asyncio.to_thread(_run_on_ready, on_ready)
            return

    print(
        "Knowledge base is still not ready. Upload a document or restart "
        "the server to try again."
    )


async def warm_up(refresh, delays=None, on_ready=None):
    """Build the knowledge base at startup without ever stopping the server.

    If it fails (for example a rate limit), the server still starts and the
    work is retried in the background. Progress already saved is reused.
    Returns the background task, or None if nothing needs retrying.

    on_ready (optional) runs only after a refresh SUCCEEDS, either now or
    in a later retry. It never runs if the refresh failed.
    """
    if delays is None:
        delays = RETRY_DELAYS

    try:
        refresh()
    except Exception as exc:
        print(
            f"Knowledge base could not be built at startup: {exc}\n"
            "The server will start anyway and retry in the background."
        )
        return asyncio.create_task(
            _retry_in_background(refresh, delays, on_ready)
        )

    _run_on_ready(on_ready)
    return None


async def stop_retrying(task):
    if task is None:
        return

    task.cancel()

    with suppress(asyncio.CancelledError):
        await task