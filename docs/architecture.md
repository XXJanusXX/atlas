# Architecture

## Trust boundaries
1. Market-data adapters provide observations, never commands.
2. Strategy modules create typed trade proposals.
3. AI providers may review proposals but cannot create orders.
4. RiskEngine is deterministic and fails closed when sizing metadata is absent.
5. PaperBroker is the only execution implementation in v0.1.
6. Ledger stores decision and execution events.

## Data flow
Market data -> normalization -> strategy -> optional AI review -> risk gate -> paper broker -> ledger -> analytics.

## Broker decision
Provider selection is deferred. Evaluate practice/demo environments, jurisdictional eligibility, symbol coverage, market-data rights, API availability, costs and operational complexity before selection.

## Non-goals for v0.1
- No live trading or leverage.
- No AI-generated code execution.
- No AI ability to modify risk limits.
- No withdrawal or account-management functions.
