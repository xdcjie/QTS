# ADR 0002: Instrument + ContractSpec Model

## Decision

Use unified `Instrument` and `ContractSpec` abstractions for stocks, futures, and options.

## Rationale

Avoid three separate systems. Keep product differences in specs, valuation, margin, and risk models.
