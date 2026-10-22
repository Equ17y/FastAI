import asyncio
import logging

import httpx
from gotenberg_api import GotenbergServerError, ScreenshotHTMLRequest

from src.env_settings import settings

logger = logging.getLogger(__name__)

GOTENBERG_MAX_ATTEMPTS = 3


async def create_screenshot(
    gotenberg_client: httpx.AsyncClient,
    html_code: str,
) -> bytes:
    """Создаёт PNG через Gotenberg с ограниченным числом повторных попыток."""
    screenshot_request = ScreenshotHTMLRequest(
        index_html=html_code,
        width=settings.gotenberg.screenshot_width,
        format="png",
        wait_delay=settings.gotenberg.wait_delay,
    )

    for attempt in range(1, GOTENBERG_MAX_ATTEMPTS + 1):
        try:
            return await screenshot_request.asend(gotenberg_client)
        except (httpx.HTTPError, GotenbergServerError) as exc:
            if attempt == GOTENBERG_MAX_ATTEMPTS:
                raise

            logger.warning(
                "Gotenberg: попытка %s/%s не удалась: %s",
                attempt,
                GOTENBERG_MAX_ATTEMPTS,
                exc,
            )
            await asyncio.sleep(attempt * 2)

    raise RuntimeError("Не удалось создать скриншот")
