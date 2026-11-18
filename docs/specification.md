# Technical Specification v0.1

## Account
- Base currency: USD
- Initial virtual equity: 100.00
- Cash, realised P&L, unrealised P&L and equity remain separate ledger concepts.

## Universe
- Major, minor and exotic FX instruments.
- "All" means instruments returned by the selected provider that pass metadata, quote freshness, spread and liquidity checks.
- Provider symbol coverage and trading conditions are not assumed identical.

## Strategy contract
A strategy emits a typed proposal with instrument, side, reference entry, stop, optional target, timestamp, strategy ID and rationale.

## AI contract
AI output is structured advice only. It cannot place, amend or cancel orders. Model disagreement is recorded. AI confidence is not a calibrated probability unless empirically validated.

## Risk
Initial simulation defaults: 0.25% equity risk per trade, 0.75% aggregate open risk, 1% daily loss stop, 2% weekly loss stop, maximum three open positions, leverage disabled. These are test guardrails, not optimality claims.
Sizing requires contract specifications, pip/tick value, account-currency conversion, minimum units and increments. Missing data causes rejection.

## Paper execution
- Buy fills at ask; sell fills at bid.
- Configurable slippage, commissions and rollover/swap.
- Stops and targets trigger against executable bid/ask.
- Order lifecycle is idempotent and reconciled.
- Partial fills and gaps are explicit simulation scenarios.

## Evidence
Persist market snapshot, quote timestamp, strategy version, config hash, model metadata, risk decision, order state, fill, costs and ledger hash chain.

## Acceptance
- No route from AI layer to execution.
- No live adapter exists in v0.1.
- Invalid/stale quotes rejected.
- Missing sizing metadata rejected.
- Risk limits enforced in deterministic tests.
- Simulated fills account for spread and slippage.
- Ledger reconciliation has no unexplained difference.
