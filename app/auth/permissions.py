"""Role-based access control mapping.

Cognito groups map to roles; roles map to allowed actions. Document-level
authorization (Phase 4) additionally filters retrieval results by the
requester's allowed document classifications.
"""
from enum import StrEnum


class Role(StrEnum):
    READER = "reader"
    INGESTOR = "ingestor"
    ADMIN = "admin"


class Action(StrEnum):
    QUERY = "query"
    GENERATE = "generate"
    INGEST = "ingest"


ROLE_PERMISSIONS: dict[Role, frozenset[Action]] = {
    Role.READER: frozenset({Action.QUERY}),
    Role.INGESTOR: frozenset({Action.QUERY, Action.INGEST}),
    Role.ADMIN: frozenset({Action.QUERY, Action.GENERATE, Action.INGEST}),
}


def is_allowed(role: Role, action: Action) -> bool:
    return action in ROLE_PERMISSIONS.get(role, frozenset())
