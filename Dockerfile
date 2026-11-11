FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin libgdal-dev libgeos-dev libproj-dev binutils netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# RUN pip install --no-cache-dir GDAL==$(gdal-config --version)

# Переменные для сборки Python-пакетов, которым нужны заголовки GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Poetry
ENV POETRY_VERSION=2.4.1 \
    POETRY_HOME=/opt/poetry \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR /app

# Сначала зависимости — для эффективного кеширования слоёв
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-ansi

# Затем код проекта
COPY . .

# Копирование и настройка прав на выполнение entrypoint-скрипта
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Установка ENTRYPOINT и сохранение исходного CMD
ENTRYPOINT ["/entrypoint.sh"]

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]