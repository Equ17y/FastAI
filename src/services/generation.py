import asyncio
import logging

from html_page_generator import AsyncPageGenerator

from src.env_settings import settings
from src.services.screenshots import create_screenshot
from src.services.storage import (
    upload_html_to_s3,
    upload_screenshot_to_s3,
)

logger = logging.getLogger(__name__)


async def stream_generated_chunks(
    generator,
    prompt: str,
    chunks_queue: asyncio.Queue,
) -> None:
    """Передаёт сгенерированные фрагменты HTML в очередь."""
    async for chunk in generator(prompt):
        if isinstance(chunk, bytes):
            chunk_bytes = chunk
        elif isinstance(chunk, str):
            chunk_bytes = chunk.encode()
        else:
            chunk_bytes = str(chunk).encode()

        await chunks_queue.put(chunk_bytes)


async def publish_generated_site(
    s3_client,
    gotenberg_client,
    html_code: str,
    site_id: int,
) -> None:
    """Создаёт скриншот и сохраняет файлы конкретного сайта."""
    screenshot = await create_screenshot(
        gotenberg_client,
        html_code,
    )

    await upload_screenshot_to_s3(
        s3_client,
        screenshot,
        site_id,
    )
    await upload_html_to_s3(
        s3_client,
        html_code,
        site_id,
    )


async def generate_html_in_background(
    prompt: str,
    s3_client,
    gotenberg_client,
    chunks_queue: asyncio.Queue,
    site_id: int,
) -> None:
    """Генерирует сайт и сохраняет его файлы в S3."""
    generator = AsyncPageGenerator(debug_mode=settings.debug)

    try:
        await stream_generated_chunks(generator, prompt, chunks_queue)

        html_code = generator.html_page.html_code

        await publish_generated_site(
            s3_client,
            gotenberg_client,
            html_code,
            site_id,
        )

        await chunks_queue.put(
            b"\n\n<!-- Site successfully generated and saved to S3 -->",
        )

    except Exception:
        logger.exception("Не удалось завершить генерацию сайта")
        await chunks_queue.put(
            b"\n\n<!-- Site generation or publication failed -->",
        )

    finally:
        await chunks_queue.put(None)
