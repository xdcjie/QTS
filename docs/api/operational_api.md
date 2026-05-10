# Operational API

## Runtime Commands

- `POST /operations/runtime/pause`
- `POST /operations/runtime/resume`

Headers:

- `X-QTS-Operator`: required permission hook.
- `Idempotency-Key`: optional command idempotency key.

Response:

```json
{"state": "paused"}
```

## Kill Switches

`POST /operations/kill-switches`

Request:

```json
{"scope": "global", "scope_id": null, "reason": "operator halt"}
```

Scopes are `global`, `account`, `strategy`, and `broker`.

## Errors

Operational errors use `{code, message, detail}`. Internal exception details and secrets are not
returned in public error payloads.
