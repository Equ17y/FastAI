import json
import logging
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path

import aioboto3
import httpx
from botocore.config import Config
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from html_page_generator import AsyncDeepseekClient, AsyncUnsplashClient

from src.api.sites import router as sites_router
from src.api.users import router as users_router
from src.env_settings import settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и завершение работы клиентов при старте/остановке приложения."""

    ds_key = settings.deepseek.api_key.get_secret_value()
    ds_base_url = str(settings.deepseek.base_url)
    ds_model = settings.deepseek.model
    ds_timeout = settings.deepseek.timeout

    us_key = settings.unsplash.api_key.get_secret_value()
    us_timeout = settings.unsplash.timeout

    s3_config = Config(
        connect_timeout=settings.aws.connect_timeout,
        read_timeout=settings.aws.read_timeout,
        max_pool_connections=settings.aws.max_connections,
    )

    print("=== APP SETTINGS (JSON) ===")
    print(json.dumps(settings.model_dump(mode="json"), indent=2, ensure_ascii=False))
    print("===========================\n")

    async with AsyncExitStack() as stack:
        app.state.generation_tasks = set()

        await stack.enter_async_context(
            AsyncUnsplashClient.setup(
                us_key,
                timeout=us_timeout,
                limits=httpx.Limits(
                    max_connections=settings.unsplash.max_connections,
                ),
            ),
        )
        app.state.unsplash_client = AsyncUnsplashClient.get_initialized_instance()

        await stack.enter_async_context(
            AsyncDeepseekClient.setup(
                ds_key,
                ds_base_url,
                ds_model,
                timeout=ds_timeout,
                limits=httpx.Limits(
                    max_connections=settings.deepseek.max_connections,
                ),
            ),
        )
        app.state.deepseek_client = AsyncDeepseekClient.get_initialized_instance()

        s3_session = aioboto3.Session()

        app.state.s3_client = await stack.enter_async_context(
            s3_session.client(
                "s3",
                endpoint_url=str(settings.aws.endpoint_url),
                aws_access_key_id=settings.aws.access_key.get_secret_value(),
                aws_secret_access_key=settings.aws.secret_key.get_secret_value(),
                config=s3_config,
            ),
        )

        app.state.gotenberg_client = await stack.enter_async_context(
            httpx.AsyncClient(
                base_url=str(settings.gotenberg.api_url),
                timeout=httpx.Timeout(settings.gotenberg.timeout),
                limits=httpx.Limits(
                    max_connections=settings.gotenberg.max_connections,
                    max_keepalive_connections=settings.gotenberg.max_connections,
                ),
            ),
        )

        print("Клиенты DeepSeek, Unsplash, S3 и Gotenberg успешно инициализированы!")
        print("===========================\n")

        logger.info("Клиенты DeepSeek, Unsplash, S3 и Gotenberg инициализированы")

        yield

    logger.info("Клиенты API закрыты")


app = FastAPI(lifespan=lifespan)
app.include_router(users_router)
app.include_router(sites_router)


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@app.get("/")
async def read_root():
    index_path = FRONTEND_DIR / "index.html"
    return FileResponse(str(index_path))


app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="static")
