"""Shared FastAPI dependencies. Overridden in tests."""
from app.clients.bedrock import BedrockService
from app.rag.embeddings import EmbeddingService
from app.rag.ingestion import IngestionService
from app.rag.retrieval import VectorStore
from app.rag.service import RagService


def get_bedrock_service() -> BedrockService:
    return BedrockService()


def get_vector_store() -> VectorStore:
    return VectorStore()


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


def get_rag_service() -> RagService:
    return RagService(
        bedrock=get_bedrock_service(),
        embeddings=get_embedding_service(),
        store=get_vector_store(),
    )


def get_ingestion_service() -> IngestionService:
    return IngestionService(
        embeddings=get_embedding_service(),
        store=get_vector_store(),
    )
