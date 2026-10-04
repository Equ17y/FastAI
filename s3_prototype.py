import asyncio
from pathlib import Path

import aioboto3

from src.env_settings import settings


async def upload_html(file_path: Path) -> None:
    session = aioboto3.Session()

    async with session.client(
        "s3",
        endpoint_url=settings.aws.endpoint_url,
        aws_access_key_id=settings.aws.access_key.get_secret_value(),
        aws_secret_access_key=settings.aws.secret_key.get_secret_value(),
    ) as s3:
        with file_path.open("rb") as file:
            await s3.put_object(
                Bucket=settings.aws.bucket_name,
                Key=file_path.name,
                Body=file,
                ContentType="text/html",
                ContentDisposition="inline",
            )

    print(f"Загружено: {file_path.name}")


async def main() -> None:
    await upload_html(Path("index.html"))


if __name__ == "__main__":
    asyncio.run(main())
