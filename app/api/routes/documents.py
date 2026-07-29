"""Document ingestion endpoints.

Sources resolve against a fixed synthetic corpus directory and path
traversal is rejected. Documents are written into the caller's tenant with
an explicit classification; a caller may not ingest at a classification its
role cannot itself read. Milestone 6 replaces this with the S3 -> SQS
pipeline.
"""
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_ingestion_service
from app.auth.permissions import Action
from app.auth.tenancy import TenantContext, require
from app.models.requests import IngestRequest
from app.models.responses import IngestResponse
from app.rag.ingestion import IngestionService

router = APIRouter(tags=["documents"])

CORPUS_DIR = Path("synthetic-data/documents")


@router.post("/documents/ingest", response_model=IngestResponse)
def ingest(
    body: IngestRequest,
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
    context: Annotated[TenantContext, require(Action.INGEST)],
) -> IngestResponse:
    if body.classification not in context.allowed_classifications:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Role '{context.role.value}' may not ingest "
                f"'{body.classification.value}' documents"
            ),
        )
    path = (CORPUS_DIR / body.source).resolve()
    if CORPUS_DIR.resolve() not in path.parents:
        raise HTTPException(status_code=400, detail="Invalid source path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Unknown document")
    count = service.ingest_file(
        path, tenant_id=context.tenant_id, classification=body.classification, source=body.source
    )
    return IngestResponse(source=body.source, chunks_ingested=count)
