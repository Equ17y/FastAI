# FastAI

## Репозиторий для бэкенд-разработчиков.

Инструкции и справочная информация по разворачиванию локальной инсталляции собраны
в документе [CONTRIBUTING.md](./CONTRIBUTING.md).

## Схемы архитектуры

- [Декомпозиция бэкенда по подсистемам](schemes/decomposition.png)
- [Локальная инсталляция бэкенда](schemes/local_installation.png)
- [Prod инсталляция бэкенда](schemes/prod_installation.png)


*Проверка игнорирования .env (STORY-428)*

## Настройка переменных окружения

> **ВАЖНО:** Никогда не коммитьте файл `.env` с реальными ключами в репозиторий! Он уже добавлен в `.gitignore`.

Для локального запуска проекта необходимо настроить переменные окружения:

1. Скопируйте файл-шаблон `example.env` и переименуйте копию в `.env`:
   ```bash
   cp example.env .env
    ```

  *(В Windows PowerShell используйте: `copy example.env .env`)*

2. Откройте файл `.env` в любом текстовом редакторе и замените значения-заглушки на ваши реальные ключи API.

3. Убедитесь, что файл `.env` **не попадает** в коммиты (он уже добавлен в `.gitignore`).

### Необходимые переменные и где их взять:

| Переменная | Описание | Где взять |
|------------|----------|-----------|
| `DEBUG` | Режим отладки (`true` или `false`) | Установите `true` для разработки, `false` для продакшена |
| `SECRET_KEY` | Секретный ключ приложения | Сгенерируйте любую случайную строку (например, через `openssl rand -hex 32`) |
| `DEEPSEEK__API_KEY` | API-ключ для генерации HTML-кода | [Официальный DeepSeek](https://platform.deepseek.com/) или альтернативы: [BotHub](https://bothub.chat/), [VseGPT](https://vsegpt.ru/) |
| `DEEPSEEK__BASE_URL` | URL API DeepSeek | `https://api.deepseek.com/v1` (по умолчанию) или URL вашей альтернативной инсталляции |
| `DEEPSEEK__MODEL` | Название модели DeepSeek | `deepseek-chat` (по умолчанию) |
| `DEEPSEEK__MAX_CONNECTIONS` | Максимальное количество подключений к DeepSeek | Целое положительное число (например, `5`) |
| `DEEPSEEK__TIMEOUT` | Таймаут запроса к DeepSeek в секундах | Целое положительное число (например, `30`) |
| `UNSPLASH__API_KEY` | Access Key для поиска изображений в Unsplash | [Unsplash Developers](https://unsplash.com/developers) — создайте Demo App и скопируйте Access Key |
| `UNSPLASH__MAX_CONNECTIONS` | Максимальное количество подключений к Unsplash | Целое положительное число (например, `5`) |
| `UNSPLASH__TIMEOUT` | Таймаут запроса к Unsplash в секундах | Целое положительное число (например, `30`) |
| `AWS__ENDPOINT_URL` | Адрес S3 API MinIO | Для локального MinIO: `http://127.0.0.1:9000` |
| `AWS__ACCESS_KEY` | Логин для подключения к S3 | Для локального MinIO соответствует `MINIO_ROOT_USER` |
| `AWS__SECRET_KEY` | Пароль для подключения к S3 | Для локального MinIO соответствует `MINIO_ROOT_PASSWORD` |
| `AWS__BUCKET_NAME` | Название S3-бакета | Например, `fastai-sites` |
| `AWS__CONNECT_TIMEOUT` | Таймаут подключения к S3 в секундах | Положительное целое число, например `5` |
| `AWS__READ_TIMEOUT` | Таймаут чтения из S3 в секундах | Положительное целое число, например `30` |
| `AWS__MAX_CONNECTIONS` | Максимальное количество одновременных подключений к S3 | Положительное целое число, например `10` |


### Настройка S3

Настройки S3 объединены в группу `AWS` и задаются в файле `.env`.

Пример конфигурации для локального MinIO:

```env
AWS__ACCESS_KEY=minioadmin
AWS__SECRET_KEY=minioadmin123
AWS__ENDPOINT_URL=http://127.0.0.1:9000
AWS__BUCKET_NAME=fastai-sites
AWS__CONNECT_TIMEOUT=5
AWS__READ_TIMEOUT=30
AWS__MAX_CONNECTIONS=10
```

Все перечисленные настройки группы `AWS` обязательны.

Для локального MinIO учётные данные соответствуют друг другу следующим образом:

```text
MINIO_ROOT_USER     == AWS__ACCESS_KEY
MINIO_ROOT_PASSWORD == AWS__SECRET_KEY
```

API локального MinIO работает на порту `9000`. Веб-интерфейс MinIO работает отдельно на порту `9001`.


### Получение API-токенов:

#### DeepSeek (или альтернативы)
1. Зарегистрируйтесь на [platform.deepseek.com](https://platform.deepseek.com/) (или [BotHub](https://bothub.chat/) / [VseGPT](https://vsegpt.ru/) для оплаты из РФ).
2. Пополните баланс (достаточно ~1$ или ~10 рублей для тестов).
3. Перейдите в раздел **API Keys** и создайте новый ключ.
4. Скопируйте ключ и вставьте его в `.env` в переменную `DEEPSEEK__API_KEY`.

#### Unsplash
1. Зарегистрируйтесь на [unsplash.com](https://unsplash.com/).
2. Перейдите в [Unsplash Developers](https://unsplash.com/developers).
3. Нажмите **Your apps** → выберите **New Application** → примите условия.
4. Скопируйте **Access Key** и вставьте его в `.env` в переменную `UNSPLASH__API_KEY`.

---

## Быстрый старт

```bash
1. Клонируйте репозиторий
git clone <url-репозитория>
cd FastAI

2. Создайте виртуальное окружение и установите зависимости
uv sync

3. Настройте переменные окружения
cp example.env .env
# Отредактируйте .env, вставив реальные ключи API

4. Запустите сервер разработки
uv run fastapi dev src/main.py

5. Откройте в браузере
http://127.0.0.1:8000 — основной сайт
http://127.0.0.1:8000/docs — Swagger-документация API
```


