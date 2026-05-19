# Runtime Value Model Boundaries

This audit covers the M5-3 runtime DTO/value-object set. The invariant is that
domain execution state has one internal model, while adapter, runtime, API, and
reporting payloads exist only when they describe a real boundary.

## Boundary Rules

- Domain models do not import API, reporting, broker adapter, or runtime sink
  payloads.
- Broker adapter payloads translate inward at the adapter boundary before
  reaching `OrderManager`.
- Runtime results describe orchestration or persistence outcomes; they do not
  replace domain order or execution state.
- Reporting artifacts serialize outward from runtime/domain state through
  writer-owned payload methods.
- A mode-specific DTO with the same fields and meaning as a shared DTO is a
  mirror and must be removed rather than aliased.

## Concept Map

| Class | Concept | Package | Boundary role | Direction | Decision | Conversion owner | Mirror decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `RuntimeOrderResult` | Runtime order submission outcome and permission evidence. | qts.runtime.order_result | runtime result | runtime -> reporting | keep | `RuntimeOrderResult.to_evidence()` centralizes event/report evidence payloads. | Not interchangeable with `OrderProcessingResult`; it can represent permission blocks without a domain order transition. |
| `OrderProcessingResult` | Domain order transition output emitted after applying one execution report. | qts.domain.orders.value_objects | domain model | domain -> runtime | keep | `OrderManager.process_report()` owns construction; downstream runtime actors consume the typed result. | Not a runtime submission result; it requires an `Order` and optional validated fills. |
| `ExecutionReport` | Normalized domain execution report accepted by `OrderManager`. | qts.domain.orders.value_objects | domain model | adapter -> domain | keep | Broker adapters and `normalize_broker_execution_report()` convert adapter reports before domain processing. | Canonical internal execution report; broker-specific report classes must translate into it. |
| `IbkrExecutionReport` | IBKR adapter callback shape after raw callback parsing and before domain normalization. | qts.execution.adapters.ibkr_order_execution | broker adapter payload | adapter -> domain | keep | `IbkrOrderExecutionAdapter.normalize_execution_report()` maps IBKR status and fill fields to `ExecutionReport`. | Boundary-specific because it uses broker status semantics and is quarantined/resolved inside the IBKR adapter. |
| `RuntimeEventWriteResult` | Shared metadata returned when a runtime event is appended. | qts.runtime.sinks.base | runtime result | runtime internal | keep | Runtime event sinks return this shared value object with sequence/hash metadata. | Canonical write metadata for runtime sinks. |
| `WrittenRuntimeEvent` | Former broker-sink write metadata with the same meaning as `RuntimeEventWriteResult`. | qts.runtime.sinks.broker_runtime | mirror | removed | remove | Removed; callers use `RuntimeEventWriteResult`. | Interchangeable mirror of shared append metadata, so it is not retained. |
| `RuntimeManifest` | Shared manifest fields emitted by backtest, paper, and live/broker runtime reports. | qts.reporting.base | reporting artifact | runtime -> reporting | keep | `RuntimeManifest.from_payload()` and `RuntimeManifest.to_payload()` centralize manifest conversion. | Canonical shared manifest base, not a mode-specific artifact wrapper. |
| `LiveReportManifest` | Former paper/live broker report write result name containing manifest path, payload, and shared runtime manifest. | qts.reporting.live | reporting artifact | removed | remove | Renamed by the report-naming lane; broker-capable report code owns the retained writer result. | Removed as live-only naming debt; no alias is retained. |
| `BacktestArtifacts` | Backtest artifact writer finalization result with paths, rows, and hashes. | qts.reporting.backtest | reporting artifact | runtime -> reporting | keep | `BacktestArtifactWriter.finalize()` owns construction from artifact writers and manifest path. | Distinct from report manifests because it summarizes concrete artifact files, not shared manifest schema. |

## Merge/Delete Decisions

`WrittenRuntimeEvent` was the only interchangeable mirror found in this audit.
It carried sequence/hash append metadata already represented by
`RuntimeEventWriteResult`; the broker runtime sink now returns the shared value object
directly and exports no alias.

No other audited class is interchangeable:

- `RuntimeOrderResult` records runtime permission and direct-submit rejection
  evidence, including cases where no domain order transition exists.
- `OrderProcessingResult` is the domain result of processing a normalized
  execution report.
- `IbkrExecutionReport` is retained only as an adapter-local payload before
  normalization into `ExecutionReport`.
- The former `LiveReportManifest` name is removed by the report-naming lane
  rather than retained as an alias; the broker-capable report
  manifest remains a writer result, while `RuntimeManifest` is the shared schema
  embedded in report artifacts.
- `BacktestArtifacts` summarizes concrete backtest artifact files and is not a
  manifest schema mirror.
