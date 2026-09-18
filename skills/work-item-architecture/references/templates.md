# Templates and Schemas

Copy these exactly. Consistent shapes are what let downstream tooling (and
downstream models) consume the artefacts without interpretation.

## Contents

1. `01-requirements.json` schema
2. `02-architecture.md` template
3. ADR template (`02-adr-NN-<slug>.md`)
4. `02-components.json` schema
5. `state/run-state.json` shape
6. Reviewer sub-agent brief (moved to delegation-briefs.md)
7. Gate G0 presentation format (decision checkpoint)
8. Gate G1 presentation format
9. Salesforce sync mapping (Sync 1 and Sync 2)
10. Retrospective template (`90-retrospective.md`)

---

## 1. `01-requirements.json` schema

```json
{
  "workItem": {
    "id": "WI-00042",
    "title": "Referral intake automation",
    "source": "00-source.md",
    "fetchedFrom": "Work_Item__c a0X... | pasted",
    "date": "17/07/2026"
  },
  "functionalRequirements": [
    {
      "id": "FR-01",
      "sourceWorkItem": "WI-00042",
      "status": "ACTIVE",
      "statement": "An inbound referral staging record with a matching NHS number links to the existing Patient account instead of creating a duplicate.",
      "acceptanceCriteria": [
        { "id": "AC-01.1", "given": "a staging record whose NHS number matches one Account", "when": "intake processing runs", "then": "the created Case is parented to that Account and no new Account exists" }
      ],
      "edgeCases": [
        "record's date edited across the boundary after creation (into and out of scope)",
        "blank/null key field",
        "bulk load of 200 in one transaction",
        "edit performed by automation or integration user rather than a human"
      ],
      "priority": "must"
    }
  ],
  "nonFunctionalRequirements": [
    { "id": "NFR-01", "category": "volume", "statement": "500 referrals/day, peak batch of 200 in one transaction" }
  ],
  "assumptions": [
    { "id": "AS-01", "statement": "NHS number is stored on Account in NHS_Number__c and is unique per patient", "basis": "org scan | inferred", "riskIfWrong": "duplicate patients" }
  ],
  "outOfScope": ["..."],
  "openQuestions": []
}
```

Rules: every FR testable, every FR has at least one AC, `edgeCases` is present
per FR (boundaries, moves in/out of scope, nulls, bulk, non-human actors),
priorities are must / should / could, `openQuestions` is empty by the time
design starts (ruled at G0 or converted to logged assumptions).

**Coordinated sets** use ONE namespacing convention, no local inventions: the
FR ID is `<suffix>-FR-NN` where `<suffix>` is the shortest numeric suffix that
distinguishes the WIs in the set (WI-160604 in a 604/610/606 set gives
`604-FR-01`), and `sourceWorkItem` carries the full WI number. Single-WI runs
keep plain `FR-NN`. `status` defaults to `ACTIVE`; mark could-priority FRs
that ship unimplemented as `DEFERRED` or `RESOLVED-NOT-IMPLEMENTED`, and FRs
already satisfied by existing code as `SATISFIED-EXISTING` with a mandatory
`evidence` field citing the current artefact and line (`"evidence":
"Portal_ProjectDetailController.cls:148 already SELECTs Est_Time__c;
Portal_User.permissionset:205 grants it"`). The lint exempts all three
statuses from build-card coverage while still rejecting unknown IDs.

A **deferred G0 decision never becomes an FR**: the committed build
implements the stated baseline, and the alternative lives in `outOfScope`
with a pointer to its `gate0.deferredDecisions` id and its ADR.

## 2. `02-architecture.md` template

```markdown
# {id}: Solution Architecture

## Solution overview
(5 to 10 sentences, plain English. What exists after this ships and why this shape.)

## Requirement traceability
| FR | Satisfied by (components) |
|---|---|

## Component inventory
| Name | Type | New/Modified | Purpose |
|---|---|---|---|

## Data model changes
(Fields/objects table with full metadata, plus Mermaid erDiagram if any change.)

## Process and sequence
(Mermaid sequenceDiagram of the happy path. Add one per major flow if several.)

## Security model
(Persona x object access matrix with Read/Edit/None and explicit "must not see"
rows, covering human, automation, integration, and external/guest actors. Then
per component: sharing mechanism chosen and why, CRUD/FLS, permission sets,
exemptions. Method and mechanism tables: references/sharing-visibility.md.
Any UI states Salesforce Lightning Design System 2 (SLDS 2).)

## Integration points
| System | Direction | Protocol/Auth | Contract | Failure behaviour |
|---|---|---|---|---|

## Governor limit analysis
(Stated volumes, limits at risk, why the design holds. Numbers, not adjectives.)

## Test strategy
(What proves each acceptance criterion, and where: Apex test, MUnit, Browse/Kernel
manual script. Include org-specific test preconditions surfaced by the programme
scan. UI paths require AI-executable Manual verification scripts.)

## Deployment and data steps
(Ordered, post-deploy: permission set assignments and who receives them, custom
setting / CMDT records to create, flows to activate, data migration steps.
Each step names the build card that owns it.)

## Assumptions and open risks
(Everything from requirements assumptions plus org-scan gaps. Flag any made blind.)

## Risks and mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|

## Out of scope
```

## 3. ADR template

File: `02-adr-NN-<slug>.md`

```markdown
# ADR-NN: <Title as a decision, e.g. "Apex service, not record-triggered Flow, for intake matching">

**Status**: proposed | accepted (set accepted only after G1)

## Context
(2 to 5 sentences. The forces in play, including the standards rung skipped if any.)

## Options considered
1. Option A: one-line description. Pros / cons.
2. Option B: ...

## Decision
(One paragraph. What was chosen and the deciding factor.)

## Consequences
(What gets easier, what gets harder, what the implementer inherits.)
```

## 4. `02-components.json` schema

```json
{
  "workItem": { "id": "WI-00042", "title": "Referral intake automation" },
  "components": [
    {
      "name": "ReferralIntakeService",
      "type": "ApexClass",
      "action": "create",
      "purpose": "Match staging records to patients and create triaged Cases",
      "dependsOn": ["TestDataFactory", "NHS_Number__c"],
      "satisfies": ["FR-01", "FR-02"],
      "workItems": ["WI-00042"],
      "buildCard": "02-build-cards/BC-03-referral-intake-service.md"
    }
  ],
  "workPackages": [
    {
      "id": "WP-1",
      "title": "Data model and permissions",
      "componentNames": ["NHS_Number__c", "Referral_Coordinator"],
      "sharedFiles": [],
      "canRunInParallel": true,
      "lane": "salesforce",
      "riskNote": "none"
    }
  ]
}
```

Allowed `type` values: `ApexClass`, `ApexTrigger`, `LWC`, `Flow`, `Field`,
`Object`, `PermissionSet`, `ValidationRule`, `CustomMetadata`, `SharingRule`,
`RestrictionRule`, `MuleApp`, `Other`. Allowed `action`: `create`, `modify`.
Allowed `lane`: `salesforce`, `mule`.

Invariants the architect verifies: every FR appears in some `satisfies`; every
component has a `buildCard` path (filled by Step 7); parallel work packages
share no files. In coordinated sets: `workItems` names every WI a component
serves (it drives the per-WI sync fan-out of that component's card), and every
shared file has exactly **one owning card**; all other cards name it under
Must not.

## 5. `state/run-state.json` shape

```json
{
  "workItemId": "WI-00042",
  "status": "scoping | awaiting-g0 | designing | awaiting-g1 | approved | cards-complete",
  "mode": "light | standard | escalated",
  "escalated": false,
  "escalationTriggers": [],
  "gate0": {
    "rulings": [
      { "id": "D-01", "question": "Does the Close Won flow bypass the lock?", "proposed": "Yes, via Bypass permission granted to the automation context", "ruling": "Agreed, proposal accepted", "ruledBy": "user | orchestrator (autonomous)", "date": "17/07/2026" }
    ],
    "deferredDecisions": [
      { "id": "D-04", "question": "Merge order across the five sibling WIs claiming portalProjectDetailPage", "proposedDefault": "Build this WI first, rebase column siblings, then button siblings", "committedBuild": "Baseline behaviour with no speculative scope", "costIfRuledOtherwise": "Rebase effort on two siblings", "status": "DEFERRED" }
    ]
  },
  "escalationReasoning": "Required when escalated is false: why no trigger applies",
  "keyFindings": ["Change already present in working copy; Status QA"],
  "gate1": {
    "approved": true,
    "approvedBy": "user",
    "verbatim": "Yes, approved. Go ahead but keep the queue name as agreed.",
    "reservations": [],
    "date": "17/07/2026",
    "iterations": 2
  },
  "lint": { "lastExit": 0, "date": "17/07/2026" }
}
```

The `verbatim` and `ruling` fields are exactly what the user said (or, in
autonomous mode, the orchestrator's recorded adjudication with `approvedBy`
set to `orchestrator (autonomous)`). Conditions inside an approval ("go ahead
but...") are requirements: fold them into the artefacts before the next step.
Write this file after **every completed phase**, not only at gates, so a
crashed run resumes from the last phase.

## 6. Reviewer sub-agent brief

Moved to `references/delegation-briefs.md` (SA-REVIEW), alongside the other
six sub-agent briefs. This section number is retained so existing
cross-references stay valid.

## 7. Gate G0 presentation format (decision checkpoint)

Present before any architecture is authored. Align with `i-have-adhd`:

1. **Answer first** (one line): "N decisions need a ruling" or "No open
   decisions; proceeding to design."
2. **Short options**: number every item `D-NN` under three headings; keep each
   item to question + proposed default + one-line cost-if-wrong.
3. **One next action**: end with a single ask only.

Headings:

1. **Blocking ambiguities**: the scans could not resolve these.
2. **Cross-work-item conflicts**: in-flight siblings whose behaviour intersects
   this work item. Frame each as "who wins?" with the concrete collision
   scenario spelled out.
3. **Policy decisions**: exemptions, sync mechanisms, visible behaviour
   changes; anything with two defensible answers and business impact.

For each item give: the question in one sentence; the options; **a proposed
default with a one-line rationale**; the cost if the ruling goes the other way
later. Close with exactly one next action: "Reply with rulings by number, or
`agree` to accept all proposals." Record rulings verbatim in run-state
`gate0.rulings`, then fold them into `01-requirements.json` before designing.

If the scans surface no items, state that in one line and move on. Do not
invent questions to justify the gate.

## 8. Gate G1 presentation format

Align with `i-have-adhd`: **answer first** (one-line design stance), then the
ordered detail, then **one next action**.

Present in this exact order:

1. **Solution summary**: five bullets, plain English, no jargon the sponsor
   would not use.
2. **Component table**: name, type, action, purpose.
3. **Top risks**: with mitigations, worst first.
4. **ADRs**: title plus one-line decision each.
5. **Reservations**: your own doubts, reviewer minors, and assumptions made
   blind. "None" only if true.

Close with one ask only: "Approve this design for implementation, or say what
to change?" Iterate until approved; record verbatim per section 5. G1 approval
authorises Sync 1 and Sync 2 automatically (no second permission prompt).

## 9. Salesforce sync mapping (Sync 1 and Sync 2)

Salesforce is the system of record; files are working copies. Two sync points:
**Sync 1** after G1 approval (design layer), **Sync 2** after lint and audit
(build layer). **Both are automatic: no extra human permission is sought.** G1
approval authorises every write in the run; the user sees a post-write report
(diff table of create / update / mark-stale with keys, plus record Ids), not a
prompt. Writes go to the **R3 delivery org only** via **`sf` CLI** (compose
with `salesforce-cli` / Admin-published Salesforce skills by name). This skill
never writes to the target org. Salesforce Platform MCP is not the primary
write path. Sub-agents never write except **SA-SYNC** from the orchestrator's
manifest; the orchestrator may execute small syncs itself.

**Drift guard** (protects the two fields the sync replaces,
`Acceptance_Criteria__c` and `Assumptions__c`): before writing, re-query the
current value and compare it with the Step 0 snapshot in `00-source.md`.

- Unchanged, or already a previous `[WIA]` block: replace.
- Changed by someone else mid-run: do **not** clobber. Keep their text, append
  the new `[WIA]` block beneath it, and flag the conflict prominently in the
  sync report for the user to reconcile.

Context records need no guard: they are keyed, additive, and stale-marked,
never deleted.

**Field formats.** `Assumptions__c` is a Rich Text field (confirmed by
rendering behaviour; the simplified describe cannot show the htmlFormatted
flag): write HTML line breaks (`<br>`), never raw newlines, or the block
renders as a wall of text. `Acceptance_Criteria__c` and
`Work_Item_Context__c.Context__c` are plain long text: raw newlines are
correct there. Drift-guard comparison on the rich text field strips tags and
collapses whitespace before comparing, or every save looks like drift.

**Chunked `sf` CLI writes.** Salesforce strips trailing whitespace on every
long-text save, so when a 131k `Context__c` is appended in chunks via anonymous
Apex, a chunk boundary landing on a newline silently loses it. Never split a
chunk on whitespace: end each chunk mid-token and let the next chunk complete
it. Generated anonymous Apex uses **single-quoted** string literals with Apex
escaping; never emit `json.dumps` output directly into Apex, because its
double-quoted literals do not compile.

**Read-only runs and prior partial syncs.** A run told not to write still
reconciles what it sees. If prior `WIA |` context records or rewritten AC /
Assumptions blocks exist and diverge from this run's artefacts (a dead
earlier run, for instance), note the divergence in `00-source.md` and in the
sync report the next writing run will produce; never silently trust or
silently discard them.

**Write manifest and channel.** The orchestrator builds a manifest for each
sync: one row per write with artefact file, target work item, `Summary__c`
key, `Context_Type__c`, and (for guarded fields) the Step 0 snapshot value.
Execution is the orchestrator's, or a single **SA-SYNC** sub-agent handed the
manifest verbatim; SA-SYNC is worth it when the payload set is large
(coordinated sets duplicate shared cards across every WI), because embedding
dozens of large payloads by hand is clerical work, not judgement, and burns
orchestrator context.

**Verify after any error.** A timed-out or errored `create` may still have
committed. Before any retry, requery by `Summary__c` key (or re-read the
field) and only create what is genuinely absent; otherwise update. Duplicate
context records poison future programme scans.

**Acceptance criteria** sync to the `Acceptance_Criteria__c` **field** on the
work item (the child object is parked: creation requires a `User_Story__c`
parent, which the team is not using; see the data model note in SKILL.md).

- Replace the field content with a dated block:

  ```
  [WIA] Acceptance criteria, synced DD/MM/YYYY
  FR-01: <statement>
    AC-01.1: Given <...> When <...> Then <...>
    AC-01.2: ...
  FR-02: ...
  ```

- The field holds 32,768 characters. If the full set will not fit, keep the FR
  headings and AC one-liners in the field and state that the full detail is in
  the `WIA | REQ` context record (which always carries it anyway).
- `Assumptions__c` on the work item is replaced with the run's assumption list
  under a dated `[WIA]` header.

**Everything else** syncs to `Work_Item_Context__c`, one record per artefact,
keyed by `Summary__c` so re-runs update instead of duplicating:

| Artefact | Context_Type__c | Summary__c key | Sync |
|---|---|---|---|
| `01-requirements.json` | Technical Context | `WIA \| REQ \| <subject>` | 1 |
| `02-architecture.md` | Technical Context | `WIA \| ARCH \| <subject>` | 1 |
| Each ADR | Technical Context | `WIA \| ADR-NN \| <title>` | 1 |
| G0 rulings | Client Clarifications | `WIA \| G0 \| rulings DD/MM/YYYY` | 1 |
| `02-components.json` | Implementation Notes | `WIA \| PLAN \| component plan` | 2 |
| Each build card | Implementation Notes | `WIA \| BC-NN \| <component>` | 2 |
| Browse/Kernel script (if separate file) | Testing Context | `WIA \| BROWSE \| BC-NN` | 2 |
| Each new test trap | Testing Context | `WIA \| TRAP \| <short name>` | 2 |

Field values on every synced record: `Context__c` = the full artefact
(markdown or JSON; the 131k limit is ample), `Source_Type__c` = 'AI
Generated', `Status__c` = 'Current', `Confidence__c` = 'Verified' (a human
approved at G1; traps found only by scan are 'Likely').

Upsert algorithm:

1. `SELECT Id, Summary__c FROM Work_Item_Context__c WHERE Work_Item__c = :wi
   AND Summary__c LIKE 'WIA |%'`
2. Match on the key prefix up to the second pipe (`WIA | ADR-01 |`). Match:
   update `Context__c` and set `Status__c` = 'Current'. No match: create.
3. Existing `WIA |` records whose artefact no longer exists in this run: set
   `Status__c` = 'Stale', never delete.

## 10. Retrospective template (`90-retrospective.md`)

Fixed schema; written at Step 10; fed back into a skill-improvement session.

```markdown
# {id}: Skill Retrospective
**Date**: DD/MM/YYYY | **Skill version**: x.y.z | **Model**: <model>
**G0 items**: N | **G1 iterations**: N | **Lint iterations**: N |
**Components**: N | **Cards**: N | **Escalated**: yes/no

## Context
(3 to 6 sentences: the work item, its shape, anything atypical about the run.)

## Challenges
(Numbered. At least one; a claim of none needs stated evidence. Cover: skill
instructions that were wrong, ambiguous or missing; scan misses the user had
to correct; gate feedback and what caused each iteration; deviations from
SKILL.md and why; friction in sync or handoff.)

## Recommended improvements
(Numbered. Each names the skill file and section to change and proposes the
wording. Improvements without a target location are observations, not
recommendations.)
```
