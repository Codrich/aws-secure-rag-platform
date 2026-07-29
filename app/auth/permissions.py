"""Role-based access control and data classification.

Roles map to allowed actions and to the document classifications a caller
may retrieve. Classification filtering happens inside the retrieval query
(ADR 0002), so content a caller cannot access is never fetched.
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


class Classification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


ROLE_PERMISSIONS: dict[Role, frozenset[Action]] = {
    Role.READER: frozenset({Action.QUERY}),
    Role.INGESTOR: frozenset({Action.QUERY, Action.INGEST}),
    Role.ADMIN: frozenset({Action.QUERY, Action.GENERATE, Action.INGEST}),
}

ROLE_CLASSIFICATIONS: dict[Role, frozenset[Classification]] = {
    Role.READER: frozenset({Classification.PUBLIC, Classification.INTERNAL}),
    Role.INGESTOR: frozenset(
        {Classification.PUBLIC, Classification.INTERNAL, Classification.CONFIDENTIAL}
    ),
    Role.ADMIN: frozenset(Classification),
}


def is_allowed(role: Role, action: Action) -> bool:
    return action in ROLE_PERMISSIONS.get(role, frozenset())


def allowed_classifications(role: Role) -> frozenset[Classification]:
    return ROLE_CLASSIFICATIONS.get(role, frozenset())
