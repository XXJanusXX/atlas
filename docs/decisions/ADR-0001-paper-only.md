# ADR-0001: Paper-only execution for v0.1

Status: Accepted

Decision: The first release contains only an internal paper broker. There is no live broker adapter, live endpoint configuration, or live order path.

Rationale: Provider choice is unresolved. The initial objective is to validate normalized market data, strategy behavior, risk controls, accounting and reproducibility without exposing capital.

Consequences: Provider selection can proceed independently of the core domain model. Provider-specific execution semantics must not leak into strategy or risk modules.
