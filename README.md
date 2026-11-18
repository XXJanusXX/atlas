# ATLAS

AI-assisted quantitative Forex research and paper-trading platform.

**Initial operating mode: simulation only.** This repository intentionally contains no live broker adapter and no live-order capability.

## Initial baseline
- Virtual starting equity: USD 100
- Universe: provider-supported major, minor and exotic FX instruments, filtered by metadata, quote freshness, spread and liquidity
- Broker/provider: undecided; adapters remain provider-neutral
- AI: hybrid multi-model analysis, advisory only
- Execution: internal paper broker only

## Safety boundary
The strategy and AI layers can propose trades. A deterministic risk engine validates them. Only the internal paper broker can simulate orders. Do not add live credentials or live execution code to this release.

## Development setup
Requires Python 3.11+ (Python 3.13 is the target environment).

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
pytest
ruff check .
```

## Initial engineering priorities
1. Provider-neutral market-data contracts and instrument discovery.
2. Deterministic strategy interfaces and historical replay.
3. Contract-aware sizing and fail-closed risk controls.
4. Paper execution with spread, slippage, fees and rollover.
5. Append-only, hash-linked ledger and reconciliation.
6. AI review as advisory-only, with model/version provenance.
