#!/bin/bash
set -e

# Ожидание готовности базы данных (параметры берутся из переменных окружения)
if [ -n "$POSTGRES_HOST" ]; then
  echo "Ожидание базы данных $POSTGRES_HOST:$POSTGRES_PORT..."
  while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
    sleep 1
  done
  echo "База данных готова!"
fi

# Применение миграций
echo "Применение миграций..."
python manage.py migrate --noinput

# Запуск основной команды (например, runserver)
exec "$@"