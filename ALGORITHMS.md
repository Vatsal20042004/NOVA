# Algorithms

## Product Ranking

Products are ranked by a weighted score used for “ranked” listing and relevance-style ordering:

```
score = 0.5 * popularity_norm + 0.3 * rating_norm + 0.2 * recency
```

- **popularity_norm**: `purchase_count / max(purchase_count)` over active products (0–1).
- **rating_norm**: `average_rating / 5.0` (0–1).
- **recency**: For PostgreSQL, `max(0, 1 - (now - created_at) / (30 days))` so newer products score higher with a 30-day decay. On SQLite, ranking falls back to ordering by `purchase_count`, then `average_rating`, then `created_at`.

Implementation: `ProductService.get_ranked_products()` builds an SQL `ORDER BY` with this score (PostgreSQL) or component order (SQLite) and applies `LIMIT`, so the full catalog is not loaded into memory.

## Product Search

- **PostgreSQL**: Full-text search with `to_tsvector('english', name || ' ' || description)` and `plainto_tsquery('english', query)`. The filter is `ts_vector @@ ts_query`.
- **SQLite**: Fallback to `ILIKE` on `name` and `description` (OR of both).

## Recommendations

### Co-occurrence (“Users who bought X also bought Y”)

- **Matrix**: For each product pair that appears in the same (completed) order, we increment a co-occurrence count. Stored and refreshed in Redis per product as `cooccurrence:{product_id}` and rebuilt by a Celery task.
- **Per-user**: For a user, we take their purchased product set, aggregate co-occurrence scores for other products (excluding already purchased), and return the top-K by score. Implemented with a heap for top-K. Result is cached as `recommendations:{user_id}`.
- **Per-product (similar / also-bought)**: For a product, we read its co-occurrence map and return the top-K other products by count. Same heap-based top-K and cache.

### Content-based fallback (same category)

When co-occurrence data is missing for a product (e.g. new or rarely bought), similar products are computed by **same category**: other active products that share at least one category with the given product, ordered by `purchase_count`. This powers “similar products” and “also bought” when the co-occurrence matrix has no entries for that product.

### Matrix rebuild (scheduled)

The co-occurrence matrix is rebuilt by a **Celery Beat** task (`update_recommendation_matrix`) every hour. The task scans completed orders, counts product pairs per order, and writes per-product maps to Redis under `cooccurrence:{product_id}` with a 24-hour TTL. Run the worker with Beat so the schedule is applied:

```bash
celery -A app.workers.celery_app beat -l info
celery -A app.workers.celery_app worker -l info
```

### Future directions

- Richer content-based signals (attributes, tags).
- Collaborative filtering or embedding-based recommendations for scale.
