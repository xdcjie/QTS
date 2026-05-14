# Runtime Boundary Naming

Runtime-facing names must identify the boundary they own. A class name should
let a reviewer tell whether it manages lifecycle, maps provider payloads,
handles transport callbacks, transforms data, routes runtime messages, owns
mutable state, or writes artifacts.

| Term | Owns | Must Not Own |
| --- | --- | --- |
| `Source` | Runtime-visible market-data lifecycle: subscribe, unsubscribe, degradation, callback delivery, and source state. | Provider raw payload parsing, order execution, account mutation. |
| `Adapter` | Mapping an external provider or broker shape into internal domain models. | Runtime actor state, broker connection lifecycle, account mutation. |
| `Transport` | External SDK/network connection and callback ingress. | Runtime actors, strategy APIs, account/order state mutation. |
| `Pipeline` | Pure data processing such as bar aggregation or normalization steps. | Mailboxes, actor refs, broker connections, account/order state. |
| `Flow` | Runtime orchestration that routes normalized events into actors or queues. | Provider raw payload parsing or network connection ownership. |
| `Actor` | Mutable state processed serially through mailbox messages. | Direct cross-actor business method calls. |
| `Sink` | Runtime event output to logs, files, metrics, streams, or stores. | Domain state mutation. |
| `ReportWriter` | Final artifact and manifest serialization. | Runtime state transitions or account/order mutation. |

Replay and fake terminology is source- or test-specific and must not appear in
`qts.data.live`. Replay market data belongs under `qts.data.sources` or
`qts.data.historical` depending on whether the class owns subscription lifecycle
or file/catalog parsing. Test fakes belong under `tests/support`.

Guardrails enforce the highest-risk parts of this vocabulary:

- no `Replay*` classes in `qts.data.live`;
- no `Fake*` classes in production `qts.data`;
- no runtime actor imports from `*pipeline*` modules;
- no runtime actor imports from `*transport*` modules.
