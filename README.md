## Информационная система анализа тональности (Sentiment Analysis)

Этот проект — **веб‑приложение** для анализа тональности **русского текста** с логированием результатов в **PostgreSQL**.
Пользователь вводит текст на странице, сервер обращается к **Hugging Face Inference API** (модель RuBERT), сохраняет результат в базе и возвращает ответ в браузер.

### Что делает программа
- **Принимает текст** от пользователя (через веб‑страницу или REST API).
- **Определяет тональность**: `NEUTRAL`, `POSITIVE` или `NEGATIVE`.
- **Возвращает уверенность** модели (score 0..1).
- **Логирует каждый запрос** в таблицу `analysis_logs` (текст, метка, score, timestamp).

### Как это работает (коротко)
1. Frontend (`templates/index.html`) отправляет AJAX‑запрос `POST /predict` с JSON `{ "text": "..." }`.
2. Backend (`app.py`) валидирует входные данные через Pydantic (`schemas.py`).
3. Сервер вызывает Hugging Face Inference API через `hf_client.py`, используя **секретный** токен `HF_TOKEN` из переменных окружения.
4. Результат сохраняется в PostgreSQL через SQLAlchemy (`models.py`, `database.py`), миграции управляются Alembic (`alembic/`).
5. Сервер возвращает JSON с меткой тональности, score и временем логирования.

### Используемые технологии
- **Backend**: FastAPI (`app.py`), Uvicorn
- **HTTP клиент**: `httpx` (вызов Hugging Face)
- **База данных**: PostgreSQL
- **ORM**: SQLAlchemy 2.x
- **Миграции**: Alembic
- **Frontend**: HTML + Tailwind CSS (CDN) + Vanilla JS (динамический вывод результата без перезагрузки)

### Структура проекта (основные файлы)
- `app.py` — FastAPI приложение (роуты, CORS, security headers)
- `hf_client.py` — вызов Hugging Face Inference API (**читает `HF_TOKEN` только на сервере**)
- `schemas.py` — Pydantic модели запроса/ответа
- `models.py` — SQLAlchemy модели (таблица `analysis_logs`)
- `database.py` — подключение к БД + зависимость `get_db`
- `templates/index.html` — интерфейс (textarea + кнопка + спиннер + вывод результата)
- `alembic/` + `alembic.ini` — миграции БД
- `docker-compose.yml` / `Dockerfile` — контейнеризация (опционально, но удобно)

### Переменные окружения и конфигурация
1. Скопируйте `.env.example` в `.env`
2. Заполните:
   - `DATABASE_URL` — строка подключения к PostgreSQL
   - `HF_TOKEN` — токен Hugging Face (создать: `https://huggingface.co/settings/tokens`)
   - `ALLOWED_ORIGINS` — список разрешённых origin для CORS (через запятую)

Важно:
- **Никогда не коммитьте `.env`** (там секреты).
- `HF_TOKEN` **не должен быть в коде и не должен уходить в браузер**.

### Запуск через Docker (рекомендуется)
1. Создайте `.env` (см. выше)
2. Запустите:
```bash
docker compose up --build
```
3. Откройте `http://localhost:8000`

`docker-compose.yml` поднимает PostgreSQL и API; при старте API выполняется `alembic upgrade head`.

### Запуск локально (без Docker)
1. Установите зависимости:
```bash
pip install -r requirements.txt
```
2. Поднимите PostgreSQL и укажите корректный `DATABASE_URL` в `.env`
3. Примените миграции:
```bash
alembic upgrade head
```
4. Запустите сервер:
```bash
uvicorn app:app --reload
```
5. Откройте `http://localhost:8000`

### API
#### `POST /predict`
Тело запроса:
```json
{ "text": "Ваш текст..." }
```
Ответ:
```json
{ "sentiment_label": "POSITIVE", "score": 0.93, "timestamp": "2026-05-05T..." }
```

### Безопасность (важные замечания)
- **Секреты**: `HF_TOKEN` хранится только на сервере в env (`.env`), не вставляется в HTML/JS.
- **CORS**: разрешайте только нужные домены через `ALLOWED_ORIGINS`. Пустое значение означает, что CORS‑middleware не включён (безопасный дефолт).
- **Security headers**: включены CSP, X‑Frame‑Options, nosniff и др.  
  Текущий CSP разрешает `https://cdn.tailwindcss.com` для фронтенда; если захотите максимальную жёсткость — **самостоятельно хостите CSS/JS** и уберите CDN из CSP.

