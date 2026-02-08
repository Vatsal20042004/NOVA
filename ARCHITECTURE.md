# Architecture

## Overview

The system is a monolithic API with clear service boundaries. The backend is built with FastAPI and uses PostgreSQL as the primary store, Redis for cache and distributed locking, and Celery for background work.

```
Client --> React Frontend (optional) --> FastAPI API --> Services
                                                             --> PostgreSQL
                                                             --> Redis
                                                             --> Celery
```

## Request Flow

1. Requests hit FastAPI and are routed by prefix (`/api/v1/auth`, `/api/v1/products`, etc.).
2. Middleware adds request IDs and CORS. Dependencies handle auth (JWT), rate limiting (Redis), and DB sessions.
3. Route handlers call service classes (AuthService, ProductService, OrderService, InventoryService, RecommendationService, PaymentService). Services contain business logic and use the shared async DB session and cache.
4. For writes (e.g. order creation), the order service validates products, then calls the inventory service to reserve stock inside the same transaction. Reservations use dual locking (PostgreSQL + Redis).

## Concurrency and Locking

- **Inventory reservation**: The primary lock is PostgreSQL `SELECT ... FOR UPDATE` on the inventory row. A secondary Redis lock (`SETNX` with TTL) is acquired per product to protect against oversell across instances. Lock keys are ordered by `product_id` in bulk operations to avoid deadlocks.
- **Optimistic locking**: The `inventory` table has a `version` column. An alternative path `reserve_with_optimistic_lock()` uses a conditional update on version for environments where pessimistic locking is less desirable.
- **Cache**: Redis is used in a cache-aside pattern. Product and recommendation data are stored with TTLs. If Redis is unavailable, the app skips cache and continues with the database.

## Cache Keys

- `product:{id}` – product payload
- `recommendations:{user_id}` – list of recommended product IDs
- `cooccurrence:{product_id}` – co-occurrence counts for a product
- `lock:inventory:{product_id}` – distributed lock for reservation
- `rate:user:{user_id}` / `rate:anon:*` – rate limit counters
- `cart:{user_id}` – cart hash

## Celery

- **Broker/backend**: Redis. Tasks are defined in `app.workers.tasks`.
- **Tasks**: Order confirmation email, payment retry (exponential backoff), recommendation matrix rebuild, low-stock checks and alerts, inventory cache sync.
- **Beat schedule**: Recommendation matrix rebuild every hour; low-stock check daily. Configured in `app.workers.celery_app`.

## Services (logical)

| Service | Responsibility |
|---------|----------------|
| Auth | Registration, login, JWT issue/refresh, password hashing (Argon2) |
| Product | CRUD, search (full-text on PostgreSQL, ILIKE on SQLite), ranking, featured |
| Order | Create (with idempotency), list, cancel, status updates, payment confirmation |
| Inventory | Reserve, release, confirm, restock; dual locking and optional optimistic path |
| Payment | Simulated charge and retry logic |
| Recommendation | Co-occurrence matrix, per-user and per-product recommendations, cache |

See [ALGORITHMS.md](ALGORITHMS.md) for ranking and recommendation formulas.
