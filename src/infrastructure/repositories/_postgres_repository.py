"""PostgreSQL repository for historical data - FUTURE.

⚠️ DEFERRED: PostgreSQL persistence is not in scope for v2.0

This file is a placeholder for future implementation when the
system is stable and requires historical data storage.

Reference:
- docs/03-ADRs.md: ADR-007 (Persistencia PostgreSQL Diferida)
- docs/01-SRS.md: Section 5.2 (Future Requirements)

TODO: Implement when required (Phase 2+)
"""


class PostgresRepository:
    """
    PostgreSQL repository for historical pick data.
    
    ⚠️ DEFERRED - Not in scope for v2.0
    
    Future features:
    - Store all sent picks
    - Pick resolution (won/lost)
    - Yield calculations
    - Analytics dashboard
    
    Reference:
    - ADR-007 in docs/03-ADRs.md
    - Section 5.2 in docs/01-SRS.md
    """
    
    def __init__(self):
        raise NotImplementedError(
            "PostgresRepository is DEFERRED (ADR-007). "
            "Not in scope for v2.0."
        )
