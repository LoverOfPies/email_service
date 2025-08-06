# email_service

Сервис для отправки писем на почту.

## Описание
email_service — это сервис, предназначенный для отправки электронных писем с использованием шаблонов Jinja2. 
Он интегрируется с RabbitMQ для обработки сообщений и PostgreSQL для хранения данных.

## Установка и запуск
1. Установите зависимостей:
   ```bash
   uv sync
   ```

2. Запустите сервис:
   ```bash
   python src/main.py
   ```

## Структура проекта
<pre>
.
├── .gitignore
├── README.md
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── database/
│   │   ├── __init__.py
│   │   ├── postgres.py
│   │   ├── rabbit.py
│   │   └── models/
│   │       ├── __init__.py
│   │       └── email_data.py
│   ├── service/
│   │   ├── __init__.py
│   │   ├── email_sender.py
│   │   ├── service.py
│   │   └── templates/
│   │       ├── base.html
│   │       └── (другие шаблоны)
│   └── settings/
│       ├── __init__.py
│       ├── app.py
│       ├── postgres.py
│       ├── prometheus.py
│       └── rabbit.py
└── uv.lock
</pre>


## Конфигурация
1. Скопируйте файл `.env.example` в `.env`:
   ```bash
   cp docker/.env.example .env
   ```
2. Отредактируйте файл `.env`, указав необходимые параметры.

## Тестирование
1. Установите зависимости для разработки:
   ```bash
   uv sync --dev
   ```
2. Запустите тесты:
   ```bash
   pytest tests/
   ```
