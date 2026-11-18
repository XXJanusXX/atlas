# Implementation Roadmap

## M0 — Scaffold and governance
Repository, environment, architecture decisions, safety invariants, CI and test conventions.

## M1 — Market-data foundation
Provider-neutral adapter, instrument discovery, normalized quotes/candles, freshness checks, market calendar and replay fixtures.

## M2 — Quantitative research
Baseline trend/momentum/mean-reversion strategies, event-driven backtester, walk-forward and out-of-sample evaluation.

## M3 — Risk and paper execution
Contract-aware sizing, currency conversion, exposure limits, spread/slippage/commission/swap model, paper order state machine.

## M4 — AI advisory
Grok and OpenAI adapters, strict structured outputs, independent reviews, disagreement tracking, prompt/version provenance.

## M5 — Ledger and observability
Append-only event ledger, daily reconciliation, dashboard, alerts and session reports.

## M6 — Validation
Historical replay, paper sessions, stress tests, data outages, market gaps, duplicate events, partial fills and recovery tests.

## M7 — Readiness review
Independent code, security, statistical and operational review. This milestone does not automatically authorise live trading.
