# email_service
Сервис для отправки писем на почту

### Структура проекта
<pre>
.
├── .gitignore
├── README.md
├── pyproject.toml
├── uv.lock
└── <b>src/</b>
    ├── __init__.py
    ├── main.py
    ├── <b>database/</b>
    │   ├── __init__.py
    │   ├── postgres.py
    │   └── rabbit.py
    ├── <b>service/</b>
    │   ├── __init__.py
    │   ├── app_logger.py
    │   ├── email_sender.py
    │   ├── models.py
    │   └── service.py
    └── <b>settings/</b>
        ├── __init__.py
        ├── app.py
        ├── postgres.py
        ├── prometheus.py
        └── rabbit.py
</pre>
