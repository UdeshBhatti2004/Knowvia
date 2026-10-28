import asyncio
from unittest.mock import MagicMock

from app.knowledge.startup import stop_retrying, warm_up


def test_successful_startup_needs_no_retry():
    refresh = MagicMock()

    async def scenario():
        return await warm_up(refresh, delays=(0,))

    assert asyncio.run(scenario()) is None
    assert refresh.call_count == 1


def test_failed_startup_does_not_raise_and_retries_until_it_works():
    refresh = MagicMock(side_effect=[RuntimeError("429"), None])

    async def scenario():
        task = await warm_up(refresh, delays=(0, 0))
        assert task is not None
        await task

    asyncio.run(scenario())

    assert refresh.call_count == 2  # the failure, then one successful retry


def test_gives_up_quietly_after_all_retries_fail():
    refresh = MagicMock(side_effect=RuntimeError("429"))

    async def scenario():
        task = await warm_up(refresh, delays=(0, 0, 0))
        await task

    asyncio.run(scenario())

    assert refresh.call_count == 4  # startup + 3 retries


def test_pending_retry_is_cancelled_on_shutdown():
    refresh = MagicMock(side_effect=RuntimeError("429"))

    async def scenario():
        task = await warm_up(refresh, delays=(60,))
        await stop_retrying(task)
        return task

    task = asyncio.run(scenario())

    assert task.done()
    assert refresh.call_count == 1


def test_stop_retrying_accepts_no_task():
    asyncio.run(stop_retrying(None))