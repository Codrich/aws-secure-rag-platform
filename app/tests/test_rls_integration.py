"""Database-level isolation: PostgreSQL row-level security.

These run against a real PostgreSQL+pgvector instance. They are skipped when
TEST_DATABASE_URL is unset (local runs without Docker) and execute for real
in the `integration-tests` CI job, which starts a pgvector service container.

They prove isolation independently of the application's WHERE clause: even a
query with no tenant filter returns only the session tenant's rows, and an
attempt to write another tenant's row is rejected by the policy.
"""
import os

import pytest

psycopg = pytest.importorskip("psycopg")

TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not TEST_DATABASE_URL,
    reason="TEST_DATABASE_URL not set; RLS tests run in the CI integration job",
)

DIMS = 4


def vec(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


@pytest.fixture()
def store() -> object:
    from app.rag.retrieval import VectorStore

    st = VectorStore(conninfo=TEST_DATABASE_URL or "")
    st._settings.embedding_dimensions = DIMS  # noqa: SLF001 - test setup
    st.initialize()
    with psycopg.connect(TEST_DATABASE_URL or "") as conn, conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id', 'tenant-a', true)")
        cur.execute("DELETE FROM document_chunks")
        cur.execute("SELECT set_config('app.tenant_id', 'tenant-b', true)")
        cur.execute("DELETE FROM document_chunks")
    from app.auth.permissions import Classification as C

    st.upsert_chunks(
        "tenant-a", "a.md", C.INTERNAL, [(0, "tenant A secret", [1.0, 0, 0, 0])]
    )
    st.upsert_chunks(
        "tenant-b", "b.md", C.INTERNAL, [(0, "tenant B secret", [1.0, 0, 0, 0])]
    )
    return st


def test_search_returns_only_own_tenant_rows(store: object) -> None:
    from app.auth.permissions import Role, allowed_classifications
    from app.auth.tenancy import TenantContext

    ctx = TenantContext(
        tenant_id="tenant-a",
        role=Role.READER,
        allowed_classifications=allowed_classifications(Role.READER),
    )
    results = store.search([1.0, 0, 0, 0], context=ctx)  # type: ignore[attr-defined]
    assert [r.content for r in results] == ["tenant A secret"]


def test_rls_blocks_unfiltered_query(store: object) -> None:
    """A query with NO tenant predicate still returns only the session tenant."""
    with psycopg.connect(TEST_DATABASE_URL or "") as conn, conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id', 'tenant-a', true)")
        cur.execute("SELECT content FROM document_chunks")
        rows = [r[0] for r in cur.fetchall()]
    assert rows == ["tenant A secret"]


def test_rls_returns_nothing_when_tenant_unset(store: object) -> None:
    """Fail closed: a connection that forgets to set the tenant sees no rows."""
    with psycopg.connect(TEST_DATABASE_URL or "") as conn, conn.cursor() as cur:
        cur.execute("SELECT content FROM document_chunks")
        assert cur.fetchall() == []


def test_rls_rejects_cross_tenant_write(store: object) -> None:
    with psycopg.connect(TEST_DATABASE_URL or "") as conn, conn.cursor() as cur:
        cur.execute("SELECT set_config('app.tenant_id', 'tenant-a', true)")
        with pytest.raises(psycopg.errors.Error):
            cur.execute(
                "INSERT INTO document_chunks "
                "(tenant_id, source, chunk_index, content, classification, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s::vector)",
                ("tenant-b", "evil.md", 0, "injected", "internal", vec([0, 1.0, 0, 0])),
            )


def test_identical_similarity_across_tenants_returns_only_own_rows(store: object) -> None:
    """Both tenants hold an identical vector; tenant A must still see only its own."""
    from app.auth.permissions import Role, allowed_classifications
    from app.auth.tenancy import TenantContext

    ctx = TenantContext(
        tenant_id="tenant-a",
        role=Role.READER,
        allowed_classifications=allowed_classifications(Role.READER),
    )
    results = store.search([1.0, 0, 0, 0], context=ctx, top_k=10)  # type: ignore[attr-defined]
    assert results
    assert all(r.tenant_id == "tenant-a" for r in results)
    assert not any("tenant B" in r.content for r in results)


def test_document_acl_excludes_roles_not_listed(store: object) -> None:
    from app.auth.permissions import Classification, Role, allowed_classifications
    from app.auth.tenancy import TenantContext

    store.upsert_chunks(  # type: ignore[attr-defined]
        "tenant-a",
        "admin-only.md",
        Classification.INTERNAL,
        [(0, "admin eyes only", [1.0, 0, 0, 0])],
        document_id="doc-admin",
        allowed_roles=["admin"],
    )
    reader_ctx = TenantContext(
        tenant_id="tenant-a",
        role=Role.READER,
        allowed_classifications=allowed_classifications(Role.READER),
    )
    admin_ctx = TenantContext(
        tenant_id="tenant-a",
        role=Role.ADMIN,
        allowed_classifications=allowed_classifications(Role.ADMIN),
    )
    reader_results = store.search([1.0, 0, 0, 0], context=reader_ctx, top_k=10)  # type: ignore[attr-defined]
    admin_results = store.search([1.0, 0, 0, 0], context=admin_ctx, top_k=10)  # type: ignore[attr-defined]
    assert not any(r.document_id == "doc-admin" for r in reader_results)
    assert any(r.document_id == "doc-admin" for r in admin_results)
