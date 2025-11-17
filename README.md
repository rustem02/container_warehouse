# Container Warehouse API

Тестовое задание: REST API для учёта контейнеров и зон хранения.

## Стек

- Python, Django, Django REST Framework
- PostgreSQL
- WebSocket (Django Channels)
- Swagger-документация (/docs)
- Docker + docker-compose

## Запуск через Docker

```bash
cp .env.example .env
docker-compose up --build
```

## После запуска:

API: http://localhost:8000/api/
Список контейнеров: GET http://localhost:8000/api/containers/
Swagger: http://localhost:8000/docs/
WebSocket: ws://localhost:8000/ws/containers/


# Примеры запросов
## Создать зону

POST /api/zones/

```
{
  "name": "Zone A",
  "capacity": 10,
  "type": "cold"
}
```
## Создать контейнер

POST /api/containers/
```
{
  "number": "C-1001",
  "type": "standard",
  "zone_id": 1
}
```

Если зона переполнена → HTTP 400, {"detail": "Zone Overloaded"}.

## Обновить статус контейнера (отгрузка)

PATCH /api/containers/1/
```
{
  "status": "shipped"
}
```

При этом current_load зоны уменьшится на 1.

## Разместить контейнер в зону

POST /api/zones/1/assign/
```
{
  "container_id": 1
}
```

## WebSocket события

Подключиться к ws://localhost:8000/ws/containers/


```
{
  "event": "created",
  "data": {
    "id": 1,
    "number": "C-1001",
    "status": "stored",
    "zone_id": 1
  }
}
```