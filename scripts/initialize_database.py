"""Create the schema, row-security policy and runtime role.

Runs under the administrative connection (ADMIN_DATABASE_URL). The runtime
role it provisions is NOSUPERUSER NOBYPASSRLS - without that, PostgreSQL
exempts the connecting role from row-level security entirely.
"""
from app.core.config import get_settings
from app.rag.schema import assert_no_rls_bypass, initialize_schema


def main() -> None:
    settings = get_settings()
    initialize_schema(
        settings.admin_database_url,
        dimensions=settings.embedding_dimensions,
        app_role=settings.app_db_role,
        app_password=settings.app_db_password,
    )
    print(
        "Schema initialized: pgvector extension, document_chunks table, "
        "indexes, tenant_isolation policy."
    )
    rolsuper, rolbypassrls = assert_no_rls_bypass(settings.database_url)
    if rolsuper or rolbypassrls:
        raise SystemExit(
            f"FATAL: runtime role '{settings.app_db_role}' can bypass row-level security "
            f"(rolsuper={rolsuper}, rolbypassrls={rolbypassrls}). Refusing to continue."
        )
    print(f"Runtime role '{settings.app_db_role}' verified: no row-security bypass.")


if __name__ == "__main__":
    main()
