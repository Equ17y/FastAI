import asyncio
from pathlib import Path

import aioboto3

from src.env_settings import settings

FILES_TO_UPLOAD = {
    "index.html": "text/html",
    "index.png": "image/png",
}


async def upload_file(s3_client, file_path: Path, content_type: str) -> None:
    with file_path.open("rb") as file:
        await s3_client.put_object(
            Bucket=settings.aws.bucket_name,
            Key=file_path.name,
            Body=file,
            ContentType=content_type,
            ContentDisposition="inline",
        )

    print(f"Загружено: {file_path.name} (Content-Type: {content_type}, Content-Disposition: inline)")


async def main() -> None:
    session = aioboto3.Session()

    async with session.client(
        "s3",
        endpoint_url=settings.aws.endpoint_url,
        aws_access_key_id=settings.aws.access_key.get_secret_value(),
        aws_secret_access_key=settings.aws.secret_key.get_secret_value(),
    ) as s3_client:
        for filename, content_type in FILES_TO_UPLOAD.items():
            await upload_file(
                s3_client,
                Path(filename),
                content_type,
            )


if __name__ == "__main__":
    asyncio.run(main())
