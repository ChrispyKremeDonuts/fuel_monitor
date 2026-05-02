# Fuel Monitor

A REST API for monitoring fuel storage tanks across locations. Tracks volume readings, computes daily sales from consecutive readings, and provides weekly running averages.

**Stack:** Python 3.11, Django 4.2, Django REST Framework, PostgreSQL 15, Docker, pytest

---

## Setup

Requires Docker. No local Python or Postgres setup needed.

```bash
# Build images and start the PostgreSQL + Django containers in the background
docker-compose up -d

# Create the database tables from the Django migration files
docker-compose exec web python manage.py migrate

# Run the test suite inside the running web container
docker-compose exec web pytest tanks/tests/ -v
```

The API is available at `http://localhost:8000/api/`.

---

## Resetting the database

To wipe all data and start fresh:

```bash
# Stop containers and delete the database volume
docker-compose down -v

# Rebuild and restart
docker-compose up -d

# Re-apply migrations
docker-compose exec web python manage.py migrate
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/locations/` | List / create locations |
| GET/PATCH/DELETE | `/api/locations/{id}/` | Retrieve / update / delete location |
| GET | `/api/locations/{id}/tanks/` | All tanks at a location |
| GET/POST | `/api/tanks/` | List / create tanks |
| GET/PATCH/DELETE | `/api/tanks/{id}/` | Retrieve / update / delete tank |
| GET/POST | `/api/tank-volumes/` | List / create volume readings |
| GET/PATCH/DELETE | `/api/tank-volumes/{id}/` | Retrieve / update / delete reading |

**Filtering on `/api/tank-volumes/`:**
- `?tank_id=1` — readings for a specific tank
- `?date=2023-01-02` — readings on a specific date

