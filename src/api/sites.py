import asyncio

from fastapi import APIRouter, Path, Request
from fastapi.responses import FileResponse, StreamingResponse

from src.schemas.sites import (
    GenerateRequest,
    SiteCreateRequest,
    SiteDetailResponse,
    SitesListResponse,
)
from src.services.generation import generate_html_in_background
from src.services.sites import get_mock_site

router = APIRouter(prefix="/sites", tags=["Sites"])


@router.post("/create", response_model=SiteDetailResponse)
async def create_site(request: SiteCreateRequest):
    return get_mock_site(
        site_id=1,
        title=request.title,
        prompt=request.prompt,
    )


@router.get("/my", response_model=SitesListResponse)
async def get_my_sites():
    return {
        "sites": [
            get_mock_site(
                site_id=1,
                title="Сайт про котиков",
                prompt="Сайт с котиками",
            ),
        ],
    }


@router.get("/{site_id}", response_model=SiteDetailResponse)
async def get_site(
    site_id: int = Path(description="ID сайта", ge=1),
):
    return get_mock_site(site_id=site_id)


@router.get("/{site_id}/view")
async def view_site(site_id: int = Path(description="ID сайта", ge=1)):
    return FileResponse("index.html")


@router.get("/{site_id}/download")
async def download_site(site_id: int = Path(description="ID сайта", ge=1)):
    return FileResponse(
        "index.html",
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=index.html"},
    )


@router.post("/{site_id}/generate")
async def generate_site_streaming(
    request: Request,
    site_id: int = Path(description="ID сайта", ge=1),
    req_body: GenerateRequest = None,
):
    prompt = (
        req_body.prompt
        if req_body and req_body.prompt
        else "Современный одностраничный сайт"
    )

    chunks_queue = asyncio.Queue()

    generation_task = asyncio.create_task(
        generate_html_in_background(
            prompt=prompt,
            s3_client=request.app.state.s3_client,
            gotenberg_client=request.app.state.gotenberg_client,
            chunks_queue=chunks_queue,
            site_id=site_id,
        ),
    )

    request.app.state.generation_tasks.add(generation_task)
    generation_task.add_done_callback(
        request.app.state.generation_tasks.discard,
    )

    async def html_stream():
        while True:
            chunk = await chunks_queue.get()

            if chunk is None:
                break

            yield chunk

    return StreamingResponse(
        html_stream(),
        media_type="text/html",
    )
