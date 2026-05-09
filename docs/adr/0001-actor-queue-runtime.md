# ADR 0001: Actor + Queue Runtime

## Decision

Use Actor as the architectural abstraction and Queue as mailbox implementation.

## Rationale

- Actor boundaries clarify state ownership.
- Mailboxes preserve local order.
- Account and order state can be serialized by key.
- Strategies, accounts, and brokers can run concurrently.

## Consequence

Actors communicate by messages. Direct business method calls across actors are forbidden.
