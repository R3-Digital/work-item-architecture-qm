# MuleSoft Standards (R3 Digital)

Read when a work item includes integration or MuleSoft scope. The architect
designs within these; Mule-lane build cards inherit them.

## Contents

1. API-led connectivity
2. Spec first
3. Project structure and naming
4. Error handling
5. DataWeave
6. Reliability and async
7. Security
8. Observability
9. Testing
10. Build card expectations (Mule lane)

---

## 1. API-led connectivity

- Three layers: **Experience** (channel-shaped), **Process** (orchestration),
  **System** (one per backend, owns that backend's quirks).
- Pragmatism beats dogma: a simple point integration may justify a single
  System API. Skipping a layer is fine **with an ADR**; collapsing all three
  into one app is not.
- Reuse before build: check Exchange for an existing asset covering the
  backend first, and say in the architecture that you checked.

## 2. Spec first

- Every API has a RAML or OAS specification published to Exchange **before**
  implementation. The spec is the contract; the build card links or embeds it.
- Breaking changes bump the major version; old versions get a stated
  deprecation window.
- Examples in the spec use synthetic data only (see Security).

## 3. Project structure and naming

| Artefact | Convention | Example |
|---|---|---|
| App name | `<domain>-<layer>-api` | `referral-sys-api`, `intake-prc-api` |
| Flow name | `<verb>-<resource>-flow` | `get-referral-by-id-flow` |
| Property files | per environment, encrypted secure properties | `config-prod.yaml` |
| Global elements | in `global.xml`, not scattered | |

- No secrets in code or plain properties: Mule secure properties or the
  platform secrets manager, and the key never leaves the deployment pipeline.
- Environment-specific values (URLs, client IDs, timeouts) are properties,
  never literals in flows.

## 4. Error handling

- One global error handler per app; flows add local handlers only for
  flow-specific recovery.
- Standard error payload on every failure:
  `{ "errorCode": string, "message": string, "correlationId": string, "timestamp": ISO-8601 }`.
  No stack traces or backend internals leave the app.
- HTTP status mapping is explicit in the card:

| Condition | Status |
|---|---|
| Validation / bad request | 400 |
| Auth failure | 401 / 403 |
| Not found | 404 |
| Backend timeout | 504 |
| Backend down / connector error | 502 |
| Unhandled | 500 |

## 5. DataWeave

- Transformations reused anywhere live in `.dwl` files under
  `src/main/resources/dwl/`, not inline.
- Null-safe by default (`default`, `if ... else`, safe navigation); a mapping
  table in the build card defines the null rule per field.
- Comment the **intent** of non-obvious mappings, not the mechanics.
- No business logic hidden in transformations that the architecture describes
  as living elsewhere.

## 6. Reliability and async

- Async decoupling through Anypoint MQ (cross-app) or VM queues (in-app only).
  The card states which, plus DLQ name and redelivery policy.
- Retries: Until Successful or connector reconnection with **bounded** attempts
  and exponential backoff; the numbers (attempts, initial delay, multiplier)
  are in the card, not chosen by the implementer.
- Consumers are idempotent: the card names the idempotency key and the
  duplicate-handling behaviour.
- Timeouts are explicit on every outbound connector; no library defaults.

## 7. Security

- Minimum policy set on every managed API: client ID enforcement plus rate
  limiting; external-facing APIs add OAuth 2.0 (client credentials or JWT) and
  TLS 1.2+.
- mTLS where the counterparty supports it for system-to-system healthcare
  traffic.
- **No PHI in logs, error payloads, or spec examples.** Healthcare payload
  fields carrying patient identifiers are named in the card so logging can
  mask them.

## 8. Observability

- Structured JSON logging with a `correlationId` propagated end to end
  (accept inbound `X-Correlation-Id`, generate when absent, and return it).
- Log at flow start, flow end, and every error; payload logging is off in
  production paths unless the card says otherwise, and never for PHI fields.
- Health/ping endpoint on every app.

## 9. Testing

- MUnit coverage of every flow's happy path, each mapped error condition, and
  the retry/backoff behaviour where practical.
- Backend calls mocked in MUnit; no live endpoints in CI.
- Contract conformance: responses validate against the published spec.

## 10. Build card expectations (Mule lane)

A Mule-lane build card additionally states, exactly:

- App name, layer, and target deployment (CloudHub 2.0 / RTF), vCore or
  replica sizing assumption
- The API spec (embedded or linked) and the operations in scope
- Connector list with versions and configuration property names
- Field mapping tables per transformation with null rules
- Error mapping table (condition, status, errorCode)
- Queue/exchange names, DLQ, redelivery and backoff numbers
- Properties added per environment file, with sample (synthetic) values
- MUnit test list with Given / When / Then per test
