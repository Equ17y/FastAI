import asyncio
import webbrowser
from pathlib import Path

from html_page_generator import AsyncDeepseekClient, AsyncPageGenerator, AsyncUnsplashClient

from src.env_settings import settings


async def main():
    print(" Запуск прототипа генерации сайта...")

    deepseek_key = settings.deepseek.api_key.get_secret_value()
    deepseek_base_url = settings.deepseek.base_url
    deepseek_model = settings.deepseek.model
    unsplash_key = settings.unsplash.api_key.get_secret_value()

    print(f"DeepSeek Base URL: {deepseek_base_url}")
    print(f"DeepSeek Model: {deepseek_model}")

    prompt = (
        "Сделай современный одностраничный сайт (лендинг) для уютной кофейни "
        "с названием 'Morning Brew'. Добавь красивые фотографии кофе и интерьера."
    )

    print(f"\nОтправляем промпт:\n{prompt}\n")
    print("Начинается генерация (это может занять 10-40 секунд)...\n")

    try:
        async with (
            AsyncUnsplashClient.setup(unsplash_key, timeout=settings.unsplash.timeout),
            AsyncDeepseekClient.setup(
                deepseek_key,
                deepseek_base_url,
                deepseek_model,
            ),
        ):
            generator = AsyncPageGenerator(debug_mode=True)

            async for chunk in generator(prompt):
                print(chunk, end="", flush=True)

            safe_title = (
                generator.html_page.title.replace(" ", "_").replace(":", "")
                if generator.html_page.title
                else "generated_site"
            )
            output_file = Path(f"{safe_title}.html")

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(generator.html_page.html_code)

            print("\n\nГенерация завершена успешно!")
            print(f"Файл сохранен: {output_file.absolute()}")

            print("Открываю сайт в браузере...")
            webbrowser.open(output_file.absolute().as_uri())

    except Exception as e:
        print(f"\nПроизошла ошибка при генерации: {e}")


if __name__ == "__main__":
    asyncio.run(main())
