from time import time

from src.services.storage import (
    get_s3_download_url,
    get_s3_object_url,
    get_site_object_key,
)


def get_mock_site(
    site_id: int,
    title: str = "Мой тестовый сайт",
    prompt: str = "Сделай красиво",
) -> dict:
    version = int(time() * 1000)

    html_key = get_site_object_key(site_id, "index.html")
    screenshot_key = get_site_object_key(site_id, "index.png")

    view_url = f"{get_s3_object_url(html_key)}?v={version}"
    download_url = get_s3_download_url(html_key)
    screenshot_url = f"{get_s3_object_url(screenshot_key)}?v={version}"

    return {
        "id": site_id,
        "title": title,
        "prompt": prompt,
        "created_at": "2023-10-25T10:00:00Z",
        "updated_at": "2023-10-25T10:00:00Z",
        "view_html_url": view_url,
        "download_html_url": download_url,
        "screenshot_url": screenshot_url,
        "urlPath": "",
    }
