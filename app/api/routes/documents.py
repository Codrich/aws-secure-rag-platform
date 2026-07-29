"""Document ingestion endpoints.

Phase 1-2: synchronous ingestion of files from the synthetic corpus only -
sources are resolved against a fixed directory and path traversal is
rejected. Phase 3 replaces this with the S3 -> SQS pipeline.
"""
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_ingestion_service
from app.models.requests import IngestRequest
from app.models.responses import IngestResponse
from app.rag.ingestion import IngestionService

router = APIRouter(tags=["documents"])

CORPUS_DIR = Path("synthetic-data/documents")


@router.post("/documents/ingest", response_model=IngestResponse)
def ingest(
    body: IngestRequest,
    service: Annotated[IngestionService, Depends(get_ingestion_service)],
) -> IngestResponse:
    path = (CORPUS_DIR / body.source).resolve()
    if CORPUS_DIR.resolve() not in path.parents:
        raise HTTPException(status_code=400, detail="Invalid source path")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Unknown document")
    count = service.ingest_file(path, source=body.source)
    return IngestResponse(source=body.source, chunks_ingested=count)
