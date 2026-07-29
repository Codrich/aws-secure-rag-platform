"""Tenant isolation and misuse cases (ADR 0002).

These verify the application layer: identity is resolved server-side, cannot
be asserted by the caller, and reaches the retrieval query. Database-level
enforcement (row-level security) is verified separately against a real
PostgreSQL instance in app/tests/test_rls_integration.py.
"""
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from httpx import Response

from app.api.dependencies import get_rag_service
from app.auth.permissions import Classification, Role, allowed_classifications
from app.auth.tenancy import TenantContext
from app.main import app
from app.rag.service import RagService
from app.tests.conftest import ADMIN_A_HEADERS, TENANT_A_HEADERS, TENANT_B_HEADERS, make_bedrock

client = TestClient(app)


def make_rag_with_spy() -> tuple[RagService, MagicMock]:
    embeddings = MagicMock()
    embeddings.embed.return_value = [0.1]
    store = MagicMock()
    store.search.return_value = []
    return RagService(bedrock=make_bedrock(), embeddings=embeddings, store=store), store


def post_query(
    headers: dict[str, str], payload: dict[str, object] | None = None
) -> tuple[Response, MagicMock]:
    service, store = make_rag_with_spy()
    app.dependency_overrides[get_rag_service] = lambda: service
    try:
        response = client.post(
            "/v1/query", json=payload or {"question": "What is the policy?"}, headers=headers
        )
    finally:
        app.dependency_overrides.pop(get_rag_service)
    return response, store


# --- identity resolution ---------------------------------------------------


def test_missing_tenant_header_is_unauthorized() -> None:
    response, _ = post_query({})
    assert response.status_code == 401


def test_unknown_tenant_is_forbidden() -> None:
    response, _ = post_query({"X-Tenant-Id": "tenant-evil", "X-Tenant-Role": "reader"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Unknown tenant"


def test_unknown_role_is_forbidden() -> None:
    response, _ = post_query({"X-Tenant-Id": "tenant-a", "X-Tenant-Role": "superuser"})
    assert response.status_code == 403


# --- misuse: caller attempts to assert its own identity --------------------


def test_tenant_id_in_request_body_is_rejected() -> None:
    response, _ = post_query(
        TENANT_A_HEADERS, {"question": "What is the policy?", "tenant_id": "tenant-b"}
    )
    assert response.status_code == 422


def test_retrieval_uses_header_identity_not_payload() -> None:
    response, store = post_query(TENANT_A_HEADERS)
    assert response.status_code == 200
    passed_context = store.search.call_args.kwargs["context"]
    assert passed_context.tenant_id == "tenant-a"


def test_different_tenants_produce_different_retrieval_scope() -> None:
    _, store_a = post_query(TENANT_A_HEADERS)
    _, store_b = post_query(TENANT_B_HEADERS)
    assert store_a.search.call_args.kwargs["context"].tenant_id == "tenant-a"
    assert store_b.search.call_args.kwargs["context"].tenant_id == "tenant-b"


# --- classification-based authorization ------------------------------------


def test_reader_scope_excludes_confidential_and_restricted() -> None:
    _, store = post_query(TENANT_A_HEADERS)
    allowed = store.search.call_args.kwargs["context"].allowed_classifications
    assert Classification.CONFIDENTIAL not in allowed
    assert Classification.RESTRICTED not in allowed
    assert Classification.INTERNAL in allowed


def test_admin_scope_includes_all_classifications() -> None:
    _, store = post_query(ADMIN_A_HEADERS)
    allowed = store.search.call_args.kwargs["context"].allowed_classifications
    assert allowed == frozenset(Classification)


def test_reader_may_not_invoke_generate() -> None:
    response = client.post("/v1/generate", json={"prompt": "hi"}, headers=TENANT_A_HEADERS)
    assert response.status_code == 403


def test_ingest_above_role_classification_is_forbidden() -> None:
    """An ingestor may not write documents it could never read back."""
    response = client.post(
        "/v1/documents/ingest",
        json={"source": "employee_security_policy.md", "classification": "restricted"},
        headers={"X-Tenant-Id": "tenant-a", "X-Tenant-Role": "ingestor"},
    )
    assert response.status_code == 403
    assert "may not ingest" in response.json()["detail"]


def test_reader_may_not_ingest_at_all() -> None:
    response = client.post(
        "/v1/documents/ingest",
        json={"source": "employee_security_policy.md", "classification": "internal"},
        headers=TENANT_A_HEADERS,
    )
    assert response.status_code == 403


def test_ingest_writes_into_callers_tenant() -> None:
    from app.api.dependencies import get_ingestion_service

    service = MagicMock()
    service.ingest_file.return_value = 3
    app.dependency_overrides[get_ingestion_service] = lambda: service
    try:
        response = client.post(
            "/v1/documents/ingest",
            json={"source": "employee_security_policy.md", "classification": "internal"},
            headers={"X-Tenant-Id": "tenant-b", "X-Tenant-Role": "ingestor"},
        )
    finally:
        app.dependency_overrides.pop(get_ingestion_service)
    assert response.status_code == 200
    assert response.json()["chunks_ingested"] == 3
    assert service.ingest_file.call_args.kwargs["tenant_id"] == "tenant-b"


# --- the SQL actually carries the filters ----------------------------------


def test_search_sql_filters_by_tenant_and_classification() -> None:
    from app.rag.retrieval import VectorStore

    cursor = MagicMock()
    cursor.fetchall.return_value = []
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.__enter__.return_value = conn

    with patch("app.rag.retrieval.psycopg.connect", return_value=conn):
        store = VectorStore(conninfo="postgresql://ignored/ignored")
        ctx = TenantContext(
            tenant_id="tenant-a",
            role=Role.READER,
            allowed_classifications=allowed_classifications(Role.READER),
        )
        store.search([0.1, 0.2], context=ctx)

    executed = [call.args for call in cursor.execute.call_args_list]
    set_config_sql, set_config_params = executed[0]
    assert "set_config('app.tenant_id'" in set_config_sql
    assert set_config_params == ("tenant-a",)

    search_sql, search_params = executed[1]
    assert "WHERE tenant_id = %s AND classification = ANY(%s)" in search_sql
    assert "tenant-a" in search_params
    assert sorted(search_params[2]) == ["internal", "public"]
