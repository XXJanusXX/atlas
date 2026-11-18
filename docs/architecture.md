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

## Time handling
All persisted event timestamps are timezone-aware UTC. The timezone service resolves country
and capital references to IANA timezone identifiers, supports multiple zones for countries
that span timezones, and converts UTC timestamps for local presentation and scheduling.
Market-session rules use the timezone of the relevant financial centre or provider rather
than assuming the national capital is the trading venue. Naive timestamps are rejected.

## Broker decision
Provider selection is deferred. Evaluate practice/demo environments, jurisdictional eligibility, symbol coverage, market-data rights, API availability, costs and operational complexity before selection.

## Non-goals for v0.1
- No live trading or leverage.
- No AI-generated code execution.
- No AI ability to modify risk limits.
- No withdrawal or account-management functions.
