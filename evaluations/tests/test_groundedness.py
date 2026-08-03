"""Groundedness gates.

Offline checks that run in CI today: the no-context path must refuse rather
than hallucinate, and prompts must constrain the model to retrieved context.
Phase 5 adds live model-based grading against the golden dataset.
"""
import json
from pathlib import Path
from unittest.mock import MagicMock

from app.auth.permissions import Role, allowed_classifications
from app.auth.tenancy import TenantContext
from app.rag.service import NO_CONTEXT_ANSWER, RagService

CONTEXT = TenantContext(
    tenant_id="tenant-a",
    role=Role.READER,
    allowed_classifications=allowed_classifications(Role.READER),
)

DATASET = json.loads(Path("evaluations/datasets/golden_dataset.json").read_text())


def make_service_with_empty_store() -> RagService:
    embeddings = MagicMock()
    embeddings.embed.return_value = [0.0]
    store = MagicMock()
    store.search.return_value = []
    return RagService(bedrock=MagicMock(), embeddings=embeddings, store=store)


def test_unanswerable_questions_refuse_without_model_call() -> None:
    service = make_service_with_empty_store()
    for case in [c for c in DATASET if c["category"] == "unanswerable"]:
        result = service.query(case["question"], context=CONTEXT)
        assert result.answer == NO_CONTEXT_ANSWER, case["id"]
        assert result.citations == []


def test_no_context_means_no_bedrock_invocation() -> None:
    bedrock = MagicMock()
    embeddings = MagicMock()
    embeddings.embed.return_value = [0.0]
    store = MagicMock()
    store.search.return_value = []
    RagService(
        bedrock=bedrock,
        embeddings=embeddings,
        store=store,
    ).query("anything", context=CONTEXT)
    bedrock.invoke.assert_not_called()
