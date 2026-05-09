# Configuration

Runtime config should be externalized under `configs/` and environment variables.

Do not commit real credentials.

Commit:

- `.env.example`
- `configs/paper.ibkr.example.yaml`
- `configs/live.ibkr.example.yaml`

IBKR paper and live profiles must keep market data and order execution settings
separate. Each profile should model at least:

- market data connection host, port, client ID, and source ID
- order execution connection host, port, client ID, broker ID, and account ID
- environment mode: `paper` or `live`
- risk limit profile selected for that environment
- credentials or secret references loaded from environment variables

Do not commit:

- `.env`
- `configs/paper.ibkr.yaml`
- `configs/live.ibkr.yaml`
- broker credentials

Live mode must fail closed if required live settings are missing or if paper
account/client identifiers are supplied by mistake. Error messages must not
print credentials or raw secret values.
