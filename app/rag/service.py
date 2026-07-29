"""RAG orchestration: authorize -> retrieve -> ground -> generate -> cite."""
from app.auth.tenancy import TenantContext
from app.clients.bedrock import BedrockService
from app.core.config import get_settings
from app.core.logging import get_logger
from app.models.responses import Citation, QueryResponse
from app.rag.embeddings import EmbeddingService
from app.rag.prompting import SYSTEM_PROMPT, build_user_prompt
from app.rag.retrieval import VectorStore

logger = get_logger(__name__)

NO_CONTEXT_ANSWER = (
    "I cannot answer that from the available documents. "
    "The knowledge base has no relevant content for this question."
)


class RagService:
    def __init__(
        self,
        bedrock: BedrockService,
        embeddings: EmbeddingService,
        store: VectorStore,
    ) -> None:
        self._bedrock = bedrock
        self._embeddings = embeddings
        self._store = store
        self._settings = get_settings()

    def query(
        self, question: str, context: TenantContext, top_k: int | None = None
    ) -> QueryResponse:
        embedding = self._embeddings.embed(question)
        chunks = self._store.search(embedding, context=context, top_k=top_k)

        if not chunks:
            # Authorized-but-empty and unauthorized are indistinguishable to the
            # caller: no model call, and no signal about other tenants' content.
            logger.info("query_no_context", tenant_id=context.tenant_id, retrieved=0)
            return QueryResponse(
                request_id="",
                answer=NO_CONTEXT_ANSWER,
                citations=[],
                model_id=self._settings.bedrock_model_id,
                input_tokens=0,
                output_tokens=0,
                latency_ms=0,
            )

        prompt = build_user_prompt(question, chunks)
        result = self._bedrock.invoke(prompt, system=SYSTEM_PROMPT)
        citations = [
            Citation(source=c.source, chunk_index=c.chunk_index, score=round(c.score, 4))
            for c in chunks
        ]
        logger.info(
            "query_answered",
            tenant_id=context.tenant_id,
            role=context.role.value,
            retrieved=len(chunks),
            request_id=result.request_id,
        )
        return QueryResponse(
            request_id=result.request_id,
            answer=result.text,
            citations=citations,
            model_id=result.model_id,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            latency_ms=result.latency_ms,
        )
