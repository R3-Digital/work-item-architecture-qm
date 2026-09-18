# Salesforce Standards (R3 Digital)

Design and build standards for all Salesforce work items. The architect designs
within these; every build card inherits them. Deviations require an ADR.

## Contents

1. Decision ladder
2. Naming conventions
3. Data model
4. Apex
5. Triggers
6. Flows
7. Lightning Web Components (SLDS 2)
8. Security
9. Governor limits and scale
10. Integration touchpoints
11. Testing
12. Healthcare and regulated data
13. Metadata hygiene
14. Locks, validation rules and automation exemptions

---

## 1. Decision ladder

Work down this ladder. Stop at the first rung that genuinely meets the
requirement, including its NFRs. Each step further down needs an ADR explaining
why the rung above failed.

1. **Standard platform feature or configuration** (validation rules, page
   layouts, dynamic forms, approval processes, duplicate rules)
2. **Record-triggered Flow** (before-save for same-record field updates;
   after-save for related records and subflow orchestration)
3. **Screen Flow** for guided user interaction
4. **Apex** (complex logic, bulk data shaping, callouts, anything Flows do
   badly at volume)
5. **LWC** for custom UI standard components cannot deliver
6. **External processing / MuleSoft** when logic belongs outside the org

"Genuinely meets" includes maintainability. A 60-element Flow with nested loops
does not genuinely meet anything; that is rung 4 wearing a costume.

## 2. Naming conventions

| Artefact | Convention | Example |
|---|---|---|
| Object | PascalCase, singular, no abbreviations | `Referral_Staging__c` |
| Field | PascalCase, meaning obvious without the description | `Triage_Priority__c` |
| Apex class | PascalCase + role suffix | `ReferralIntakeService`, `ReferralSelector`, `ReferralTriggerHandler`, `ReferralIntakeServiceTest` |
| Trigger | ObjectName + `Trigger` | `ReferralTrigger` |
| Flow | `<Object> - <Type> - <Purpose>` | `Referral - RTF After - Route to Team` |
| LWC | camelCase, purpose-led | `referralTriageBoard` |
| Permission set | `<Persona or Feature>` PascalCase | `Referral_Coordinator` |
| Custom metadata | `<Domain>_Setting__mdt` | `Intake_Setting__mdt` |

Every component carries a description. Blank descriptions fail review.

## 3. Data model

- Prefer fields on an existing object over a new object. A new object needs an
  ADR covering reporting, sharing and licence impact.
- Every new field's build card states: API name, label, type, length/precision,
  required, default, help text, history tracking, and FLS per permission set.
- Picklists: restricted value sets unless integration demands otherwise; define
  the values and the default in the card. Anywhere a picklist is written,
  specify the **API value**, not the label; labels and values differ on
  existing fields (`Urgency__c` labels Critical to Low over API values `4` to
  `1`).
- Relationships: master-detail only when cascade delete and roll-ups are
  wanted behaviours; otherwise lookup with an explicit orphan rule.
- No formula chains deeper than 2 levels; move to Flow or Apex instead.
- Record types only for genuinely different processes or layouts, not as a
  status field substitute.

## 4. Apex

- **Bulkified always.** Every path assumes 200 records. No SOQL or DML inside
  loops, ever.
- Structure by role: `*Service` (business logic, static entry points),
  `*Selector` (all SOQL for an object), `*TriggerHandler` (trigger routing).
  One class, one job.
- Sharing declaration is explicit on every class: `with sharing` by default,
  `inherited sharing` for shared libraries, `without sharing` only with an ADR
  naming the reason.
- Database access runs in user mode: `WITH USER_MODE` in SOQL,
  `AccessLevel.USER_MODE` on `Database` methods. Manual describe-based FLS
  checks only where user mode is unavailable.
- No hardcoded IDs, URLs or credentials. Use Custom Metadata, Custom Labels,
  and Named Credentials.
- Exceptions: define a custom exception per service where callers must react;
  never swallow with an empty catch; every catch either rethrows, returns a
  structured failure, or logs through the org's logging mechanism (name it in
  the architecture; introducing one needs an ADR).
- Partial-success DML (`Database.insert(records, false)`) only when the design
  says survivors should commit; otherwise all-or-nothing and let it throw.
- Async: `Queueable` over `@future`; `Batchable` above ~10k records or
  heavy callout fan-out; Platform Events for fire-and-forget decoupling.
  State the chosen pattern and chaining limits in the card.
- API version: read `sourceApiVersion` from `sfdx-project.json` and use it in
  all `-meta.xml` files. Do not invent a version. **Reconcile it against the
  live org API version before pinning version-sensitive types** (ConnectApi
  member shapes change between versions; a type valid at 67 may not exist at
  58). Record any delta as an assumption and resolve it in the design, not at
  build time.
- Code must pass the R3 PMD ruleset clean (see `r3-sf-setup`). Cards may not
  waive PMD findings.

## 5. Triggers

- One trigger per object. The trigger contains routing only; all logic lives in
  the handler class.
- Handler exposes per-context methods (`beforeInsert(List<SObject>)`, ...) and
  is unit-testable without DML tricks.
- A bypass switch (hierarchy Custom Setting or custom permission) exists so data
  loads can run with automation off. The card states its API name.
- Order of execution conflicts with existing Flows on the same object are the
  architect's problem, not the implementer's: the org scan (Step 2) feeds this,
  and the architecture document states the intended ordering.

## 6. Flows

- Entry conditions on every record-triggered Flow. No entry conditions, no
  deploy.
- Before-save for same-record field updates; after-save only when touching
  other records or invoking actions.
- One record-triggered Flow per object per context where practical; where more
  exist, trigger order is set explicitly and documented.
- Fault paths on every DML, action and subflow element. The fault behaviour
  (log, notify, rethrow to user) is stated per element in the build card.
- Bulk-safe by construction: no DML or queries inside loops; collect then
  commit once.
- Subflows for logic used more than once. Hard limit of ~25 elements per flow
  before you split it; beyond that, reconsider the ladder (rung 4).
- Every element has a meaningful name and description. `Decision_1` fails
  review.
- Build cards for Flows specify each element in order: type, name, inputs,
  outputs, conditions, fault path. A Flow card an implementer must "interpret"
  is a failed card.

## 7. Lightning Web Components (SLDS 2)

- New UI is LWC. No new Aura.
- Data access order: Lightning Data Service / `@wire` adapters first; imperative
  Apex only when wires cannot express it; Apex reads are `cacheable=true`
  unless the card says why not.
- Errors surface to the user (toast or inline) with a reduceErrors-style
  utility; never console-only.
- **Salesforce Lightning Design System 2 (SLDS 2) is mandatory** for every
  new or modified Salesforce UI surface (LWC, FlexiPage placements, Experience
  Cloud themes touched by this work). Use SLDS 2 styling hooks and design
  tokens; no hardcoded colours or pixel soup. State SLDS 2 explicitly in the
  architecture and in every UI build card.
- Accessibility: keyboard reachable, labels on inputs, aria on custom
  interactions (SLDS 2 patterns).
- Component card states: public API (`@api` properties), events emitted
  (names and payloads), wires/Apex used, and the target (record page, app page,
  quick action, flow screen).

## 8. Security

- **Record visibility has its own reference**: any work touching sharing, OWD,
  Experience Cloud, guests, or "who sees what" follows
  `sharing-visibility.md` and produces the persona x object access matrix it
  defines, including explicit "must not see" rows.
- Access is granted through **permission sets and permission set groups**,
  never through profile edits. Each card lists the exact permission set changes.
- Keeping assignment in sync with membership defaults to **User Access
  Policies**; a manual or scheduled sync process needs an ADR explaining why
  not.
- Principle of least privilege: new fields default to no access; grants are
  explicit per permission set.
- **Never author an FLS grant for a Required field**: required fields are
  implicitly FLS-readable and Salesforce rejects `fieldPermissions` entries
  for them. If a value renders blank for an external user, diagnose in order
  (record sharing, query projection, LWC binding) before assuming FLS; the
  `RAID_Log__c.Status__c` mis-diagnosis cost an entire ADR and card.
- Sharing: state the model per object touched (OWD, role, sharing rules,
  manual/Apex managed). Apex managed sharing needs an ADR.
- Callouts use Named Credentials with external credentials; no endpoint
  strings or secrets in code, metadata, or custom settings.
- Guest user and Experience Cloud paths get their own security review row in
  the architecture whenever in scope.

## 9. Governor limits and scale

- The architecture states expected volumes: records/day, peak per transaction,
  total object size at 12 months.
- Per-card governor budget: max records in, SOQL count, DML count, CPU-risk
  notes, callout count. The implementer codes to the budget, not to hope.
- Selective SOQL only on large objects: filter on indexed fields; flag any
  planned full scans.
- LDV (>1M rows on a touched object): the design addresses skinny
  tables/indexes/archival explicitly, and the run is escalated (see SKILL.md
  risk triggers).

## 10. Integration touchpoints

- Direction, protocol, auth, payload contract and **failure behaviour** are
  stated per integration point in the architecture. "It calls the API" is not
  a design.
- Inbound to Salesforce: prefer platform-native (REST with external client
  apps / Connected App + JWT, Platform Events, Change Data Capture) before
  middleware polling.
- Outbound: Named Credential + Queueable callout with retry/backoff policy
  stated; callouts never run in triggers directly.
- Idempotency: every inbound write path defines its external ID / dedupe key.
- Anything beyond a single point-to-point call goes through the MuleSoft
  standards (`mule-standards.md`).

## 11. Testing

- New code: **85% coverage minimum per class**, and every logical branch
  asserted, not just executed. Coverage without assertions is decoration.
- `Assert` class with failure messages; no bare `System.assert(true)`.
- Test data through a `TestDataFactory` (create it as a component if the org
  lacks one); `@TestSetup` for shared data; **never** `SeeAllData=true`.
- Every service test suite includes: single record, bulk 200, negative/error
  path, and a `System.runAs` minimal-access user test proving FLS/sharing
  behaviour.
- **Negative tests must be non-vacuous**: a test must fail for the intended
  reason. A "different account excluded" assertion that passes because a
  `without sharing` platform subquery (NetworkMember and friends) cannot be
  seeded in test context proves nothing; keep the filter in the
  always-executed SOQL and provide an injectable `@TestVisible` seam for the
  unseedable dependency.
- Callouts mocked with `HttpCalloutMock`; async exercised inside
  `Test.startTest()/stopTest()`.
- **Org test preconditions**: some orgs have automation that sabotages naive
  test data (a flow that nulls a required field unless a settings record
  exists). The programme scan surfaces these; every affected build card's Test
  spec names the required setup records explicitly. An implementer must never
  meet a known trap unwarned.
- Flows: acceptance criteria that a Flow satisfies are proven either by Apex
  tests on the records the Flow produces or by documented manual test scripts
  in the card; the card states which.

## 12. Healthcare and regulated data

R3 delivers into health and life sciences. Assume regulated data until proven
otherwise.

- Identify PHI / patient-identifiable fields explicitly in the data model
  section. Touching them escalates the run (SKILL.md risk triggers).
- No real patient data in tests, fixtures, sample payloads, debug logs, or
  build card examples. Synthetic data only, and obviously synthetic.
- No PHI in log messages, exception messages, or outbound analytics.
- Field-level encryption (Shield) implications are stated when PHI fields are
  added: filterability, formula and integration constraints.
- Data retention or deletion requirements from the work item are treated as
  FRs with their own components, not footnotes.

## 13. Metadata hygiene

- Only the components listed in `02-components.json` change. Drive-by fixes are
  new work items.
- Descriptions on every object, field, class, flow, and permission set.
- No deprecated tech in new work: no Workflow Rules, no Process Builder, no
  Aura, no `@future` where Queueable serves.
- Destructive changes (deleting fields/objects) are their own work package,
  never bundled silently with feature work, and always escalate the run.
- **Data steps are components.** Permission set assignments, custom setting or
  CMDT records, and flow activation are not deployable metadata; they are
  listed in `02-components.json` (type `Other`), owned by a build card, and
  appear in the architecture's Deployment and data steps section. A design
  that "just works after deploy" without them is incomplete.

## 14. Locks, validation rules and automation exemptions

Any rule that blocks edits or deletes (a period lock, a status freeze, a
validation rule, a before-delete trigger) constrains **every actor**, not just
the human it was written for. Flows, Apex, and integrations run as the
triggering user, so they hit the same wall.

- The design **names every actor class** that edits the constrained records:
  humans (which personas), record-triggered automation, scheduled/batch jobs,
  integration users. The org scan's automation list is the checklist.
- For each actor class, the design states **lock wins or actor wins**. This is
  a business decision, so it is a G0 item, never a silent default.
- The standard exemption mechanism is a **custom permission**
  (`Bypass_<Domain>_Lock`) checked via `$Permission` in validation rule
  formulas and `FeatureManagement.checkPermission` in Apex, granted through a
  dedicated permission set. Assigning it to the automation-running context is
  a data step. A hierarchy custom setting kill-switch is acceptable for
  org-wide emergency bypass; an ADR picks between them.
- Boundary edges are specified, not implied: editing an already-locked record,
  and moving a record's key date or status **into or out of** the locked
  window, each have a stated outcome and a test.
- User-facing features that prompt edits (screens, modals, quick actions) are
  checked against the lock at design time: never ship a UI that demands an
  action the rule then rejects. If a sibling work item owns that UI, the
  conflict goes to G0.
