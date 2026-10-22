from src.env_settings import settings


def get_site_object_key(site_id: int, filename: str) -> str:
    """Формирует путь к файлу конкретного сайта в S3."""
    if site_id < 1:
        raise ValueError("site_id должен быть положительным")

    return f"sites/{site_id}/{filename}"


def get_s3_object_url(object_name: str) -> str:
    endpoint_url = str(settings.aws.endpoint_url).rstrip("/")
    return f"{endpoint_url}/{settings.aws.bucket_name}/{object_name}"


def get_s3_download_url(object_name: str) -> str:
    object_url = get_s3_object_url(object_name)
    return f"{object_url}?response-content-disposition=attachment"


async def upload_html_to_s3(
    s3_client,
    html_code: str,
    site_id: int,
) -> None:
    object_key = get_site_object_key(site_id, "index.html")

    await s3_client.put_object(
        Bucket=settings.aws.bucket_name,
        Key=object_key,
        Body=html_code.encode("utf-8"),
        ContentType="text/html",
        ContentDisposition="inline",
    )


async def upload_screenshot_to_s3(
    s3_client,
    screenshot: bytes,
    site_id: int,
) -> None:
    object_key = get_site_object_key(site_id, "index.png")

    await s3_client.put_object(
        Bucket=settings.aws.bucket_name,
        Key=object_key,
        Body=screenshot,
        ContentType="image/png",
        ContentDisposition="inline",
    )
