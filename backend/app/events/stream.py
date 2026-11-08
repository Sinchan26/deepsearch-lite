import asyncio

from app.domain.models import PublicEvent


def encode(event: PublicEvent) -> str:
    return f"id: {event.seq}\ndata: {event.model_dump_json()}\n\n"


async def heartbeat(waiter: asyncio.Event, seconds: float) -> bool:
    try:
        await asyncio.wait_for(waiter.wait(), timeout=seconds)
        return True
    except TimeoutError:
        return False
