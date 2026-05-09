# Auth and Permissions

Initial local development may run without auth, but API boundaries should be designed for future auth.

Potential permission scopes:

- Read accounts
- Manage strategies
- Submit/cancel orders
- Read risk
- Admin runtime

Never expose secrets, broker credentials, or raw environment values through API responses.
