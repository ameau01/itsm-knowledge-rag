"""
Qdrant client wrapper: collection setup, payload indexes, upsert, and the dense / sparse /
hybrid searches. Both the retriever arms and the ingest pipeline go through this.
"""

from __future__ import annotations

from qdrant_client import QdrantClient, models

from config import settings

DENSE = "dense"
SPARSE = "sparse"
# Indexed filter fields (UI filters + root_cause_id for eval); all keyword.
_INDEX_KEYS = ("family", "priority", "sla_tier", "env_region", "applications", "root_cause_id")


class QdrantOps:
    def __init__(self, url: str | None = None, api_key: str | None = None,
                 collection: str | None = None, client: QdrantClient | None = None) -> None:
        if client is not None:
            self.client = client
        elif settings.qdrant_local:                       # embedded on-disk, no server
            self.client = QdrantClient(path=str(settings.local_vector_db_path))
        else:                                             # server (docker compose / remote)
            self.client = QdrantClient(
                url=url or settings.qdrant_url, api_key=api_key or settings.qdrant_api_key,
                check_compatibility=False)  # query API is stable across these minor versions
        self.collection = collection or settings.qdrant_collection

    def ensure_collection(self, dim: int) -> None:
        if self.client.collection_exists(self.collection):
            return
        self.client.create_collection(
            self.collection,
            vectors_config={DENSE: models.VectorParams(size=dim, distance=models.Distance.COSINE)},
            sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        for key in _INDEX_KEYS:
            self.client.create_payload_index(self.collection, key, models.PayloadSchemaType.KEYWORD)

    def upsert(self, points: list[models.PointStruct], batch: int = 128) -> None:
        for i in range(0, len(points), batch):
            self.client.upsert(self.collection, points[i:i + batch], wait=True)

    def count(self) -> int:
        return self.client.count(self.collection, exact=True).count

    def search_dense(self, dense_vec, k, query_filter=None):
        return self.client.query_points(
            self.collection, query=dense_vec, using=DENSE, limit=k,
            query_filter=query_filter, with_payload=True).points

    def search_sparse(self, sparse_vec, k, query_filter=None):
        return self.client.query_points(
            self.collection, query=sparse_vec, using=SPARSE, limit=k,
            query_filter=query_filter, with_payload=True).points

    def search_hybrid(self, dense_vec, sparse_vec, k, query_filter=None, prefetch=None):
        pf = prefetch or k * 4
        return self.client.query_points(
            self.collection,
            prefetch=[
                models.Prefetch(query=dense_vec, using=DENSE, limit=pf, filter=query_filter),
                models.Prefetch(query=sparse_vec, using=SPARSE, limit=pf, filter=query_filter),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=k, with_payload=True).points
