---
name: work-item-architecture
description: Produce an implementation-ready Salesforce solution architecture package for a single R3 work item (architecture with Mermaid diagrams, ADRs, machine-readable component plan, and per-component build cards precise enough for a non-frontier / cheaper model or junior developer to implement with zero decisions left open). Use whenever the user asks to create or refine a work item, or to architect, design, spec, scope, or plan a work item, ticket, user story, change request, or enhancement; asks whether a work item is fully scoped or implementation-ready; wants a work item upgraded to implementation-ready; mentions solution architecture, technical design, ADRs, build cards, or component plans; or references a WI-number or Work_Item__c record. Trigger even if the user only says "design this" or "spec this up" in a Salesforce context.
---

# Work Item Architecture

You are the architect. Your output is the contract. The whole point of this skill
is that **all thinking happens here**, so that a much smaller model (or junior)
can implement each component later without inventing a single decision. Every
ambiguity you leave in a build card becomes a bug written by a model that cannot
reason its way out.

Design quality standard: an implementer given one build card, the standards
reference, and nothing else must be able to produce working, tested code.

Two rules govern how you handle the unknown:

- **Decisions: always ask.** Where two or more defensible designs exist and the
  choice has business impact (who wins a conflict, what is exempt, what a user
  sees), the user rules, at Gate G0, before you author anything. Never make a
  business-visible design call silently, however obvious it feels.
- **Trivia: resolve and log.** Where org evidence or programme context answers
  the question (which date field, an existing convention), use the evidence,
  record it as an assumption with its source, and move on. Do not bother the
  user with it.

## QM runtime

This skill runs on **QM** (orchestrator agent + parallel sub-agents / fan-out).
Use QM agent orchestration language only. Salesforce Platform MCP is not the
primary Salesforce tool surface.

### Workspace and orgs

| Concern | Rule |
|---|---|
| Default workspace | Sprite agent-computer disk: `./work-items/<id>/` where `<id>` is the Work Item number (WI-160513 style). Architecture artefacts stay here. |
| Optional DX repo | Attach or clone the **target** DX repo **read-mostly** for org-scan anchors and later implementation. Do not relocate architecture artefacts into the repo. |
| R3 delivery org | Where `Work_Item__c`, ACs and contexts live. Confirm its `sf` alias at Step 0. |
| Target org | Client sandbox for build and test. Confirm its `sf` alias at Step 0. |
| Auth | Both aliases via `sf` CLI. Never conflate the two orgs. |

### Skills to invoke by name (compose; do not paste bodies)

Salesforce execution surface:

- `salesforce-cli` (and Admin-published Salesforce skills such as
  `R3-Digital/sf-skills-qm`, Clientell packs, and similar)
- Prefer `sf` CLI commands over any Platform MCP for describe, query, deploy
  and write-back

Architecture and delivery principles (name-reference only):

- `pstack-architect`
- `pstack-blast-radius`
- `pstack-interrogate`
- `pstack-swarm`
- `pstack-tdd`
- `pstack-principle-guard-the-context-window`
- `pstack-principle-exhaust-the-design-space`
- `pstack-principle-prove-it-works`

Presentation at human gates:

- Align G0 / G1 with `i-have-adhd`: **answer first**, short options, **one next
  action**

### GBrain limits

Use GBrain **only** for company / contact / high-level product / high-level
project context. **Do not** use GBrain for previous work items or architecture
history; those come from the Salesforce programme scan.

### Browse / Kernel test scripts

Build cards (or explicit artefacts under `02-browse-tests/`) must include
**AI-executable manual test scripts** suitable for Browse / Kernel automated
manual testing, in addition to Apex or other automated tests where relevant.
See `references/build-card-template.md`.

### Auto-sync policy

Salesforce is the system of record. Sync automatically with **no extra human
permission**:

1. **Sync 1** immediately after G1 approval (design layer)
2. **Sync 2** after lint and card audit (build layer)

Still **report** diffs and record Ids after every write. Mapping:
`references/templates.md` section 9. A run that ends with rich markdown and an
untouched work item has failed.

## Outputs

Every artefact is drafted as a file (lint runs on files; implementers consume
files), then synced to the work item and its child objects at Sync 1 and Sync 2.

| File | Contents | Salesforce home |
|---|---|---|
| `00-source.md` | Work item, ACs and contexts as fetched | n/a (it is the source) |
| `01-requirements.json` | FR / AC / NFR IDs, edge cases | `Acceptance_Criteria__c` field, `Assumptions__c` field, Technical Context record |
| `02-architecture.md` | Design with Mermaid diagrams | Technical Context record |
| `02-adr-NN-<slug>.md` | One per decision | Technical Context record each |
| `02-components.json` | Machine-readable build plan | Implementation Notes record |
| `02-build-cards/BC-NN-<slug>.md` | The implementer contract | Implementation Notes record each |
| `02-browse-tests/` | Optional Kernel browse scripts (or embed in cards) | stays local unless synced as Testing Context |
| `context/org-scan.md` | Target-org metadata and automation | stays local |
| `context/programme-scan.md` | Conventions, traps, conflicts | new traps as Testing Context records |
| `state/run-state.json` | Risk flags, G0 rulings, G1 approval | rulings as a Client Clarifications record |
| `90-retrospective.md` | Skill self-review for the improvement loop | stays local |

**Coordinated change sets.** When two or more work items share downstream
surfaces (a common formula, class, page), run them as one coordinated set in a
single `work-items/<id-a>-<id-b>/` workspace; when colliding siblings must
**both** land, co-building as one set beats sequencing them. Step 0 fetches
every work item in the set. FR and AC IDs use the namespacing convention in
`references/templates.md` section 1 (`604-FR-01` style plus `sourceWorkItem`),
so the lint, the architects and the sync all agree. Structure work packages so
per-WI components are file-disjoint and **all shared-file edits sit in one
package** that depends on them; every shared file has exactly **one owning
card**, and each component's `workItems` array names which WIs it serves. At
sync, write per-WI artefacts to their own work item and shared artefacts to
every work item in the set, so each WI remains self-contained.

## Two orgs, do not conflate them

| Org | Role | Access |
|---|---|---|
| **R3 delivery org** | Work items, acceptance criteria and context records | Authenticated `sf` alias (confirm at Step 0) |
| **Target org** | Client sandbox the solution will be built and tested in | `sf` CLI `--target-org <alias>` (confirm at Step 0) |

They are sometimes the same org (internal work items). Confirm **both** aliases
at Step 0 if either is not obvious from the conversation or repo config.

## R3 data model

Verified field and relationship facts (`Work_Item__c`, the parked AC child
object, `Work_Item_Context__c`, `Work_Item_Dependency__c`) live in
`references/r3-data-model.md`. Read it before Step 0; verify with a describe if
anything errors, since orgs drift.

## Orchestration model (QM)

You are the **orchestrator**. Parallel **sub-agents** (QM fan-out) do the heavy
reading and drafting; you keep judgement, gates, Salesforce writes and the
conversation. Your context is the scarce resource: raw describes, SOSL dumps and
131k-character context records must never enter it. Sub-agents absorb the bulk
and return distilled files. All briefs: `references/delegation-briefs.md`.

Compose with pstack skills by **name** when useful (`pstack-swarm` for fan-out
patterns, `pstack-blast-radius` when sizing impact, `pstack-interrogate` when
probing unknowns, `pstack-tdd` / `pstack-principle-prove-it-works` when shaping
test contracts). Do not paste their bodies into this run.

**Size the run** after Step 0, record `mode` in run-state, and re-check after
design. Escalate freely at any point; never de-escalate.

| Mode | Signals | Changes from Standard |
|---|---|---|
| Light | `Est_Time__c` <= 8h AND no trigger keywords (integration, migration, sharing, portal, delete, PHI) AND expected <= 3 components | SA-ORG and SA-PROG merge into one narrow scan sub-agent, or the whole run collapses to a **single agent working inline** (delegation is an optimisation for context pressure, not a requirement); single work package with one SA-CARDS; SA-AUDIT optional; artefact sections proportionate (one line where trivially satisfied); brief retro |
| Standard | default | Full phase graph |
| Escalated | any high-risk trigger (Step 7 table), whenever it appears | Standard + mandatory SA-REVIEW before G1; `escalated: true` |

**Phase graph.** Spawn each phase's sub-agents in the same turn so they run in
parallel (QM fan-out); while they run, keep the user informed in a line or two.
The gates are the only points needing their attention.

```
Phase A  SA-REQ + SA-ORG + SA-PROG          (parallel)
         orchestrator: verify outputs, read standards
Phase B  Gate G0                            (orchestrator + user)
Phase C  SA-ARCH; verify; form own view; SA-REVIEW if escalated
Phase D  Gate G1, then Sync 1               (orchestrator + user)
Phase E  SA-CARDS, one per work package     (parallel)
Phase F  lint; SA-AUDIT; fix findings
Phase G  Sync 2, handoff, retrospective     (orchestrator)
```

**Run modes.** Interactive is the default: G0 and G1 are hard stops. On the
user's **explicit** request, run **autonomous**: the whole pipeline executes
without pauses to a single human review at the end. The gates are not
skipped, they are **adjudicated and recorded**: G0-class items the run can
confidently self-rule go in `gate0.rulings` with the rationale and
`"ruledBy": "orchestrator (autonomous)"`; genuinely business-visible or
cross-effort calls go in `gate0.deferredDecisions[]` (schema in templates
section 5) with a proposed default, the committed-build baseline, and the
cost if ruled otherwise. G1 is recorded with
`"approvedBy": "orchestrator (autonomous)"` plus a `reservations` list, and
a non-escalated run states its `escalationReasoning`. SA-REVIEW remains
mandatory when escalated; SA-AUDIT is mandatory (no human has seen the
cards); **no Salesforce write happens until the single review approves**,
and that review presents the G0 ledger, deferred decisions, the G1-format
summary and the audit findings together. Write `run-state.json` after
**every completed phase**, not only at gates: a mid-run crash must resume
from the last phase, not lose the run. Record `"runMode": "autonomous"`.

**Contract rules**:

- Orchestrator-only, never delegated: gates, run sizing, talking to the user,
  and building every Salesforce write manifest. Write **execution** is yours
  or **SA-SYNC** working strictly from your manifest: one instance normally;
  in coordinated sets, one per work item is allowed **provided each WI
  appears in exactly one manifest** (record-disjoint writers cannot race).
  SA-SYNC uses chunked `sf` CLI when payloads are large (too token-heavy to
  run inline).
- Every delegation uses its brief: goal, exact inputs, exact outputs,
  forbidden actions. Sub-agents surface decisions as questions; they never
  make G0-class calls.
- Verify at every fan-in before the next phase: outputs exist, parse, and
  meet the brief. A missing or malformed output is re-delegated with the gap
  named, never patched silently.
- A blocked sub-agent writes its questions at the top of its output and
  stops; answer (or take to a gate) and re-delegate with the answers
  appended.
- Parallel sub-agents share no output files.
- Tier guidance sits in each brief: scans run cheap; the architect and the
  card auditor run on the strongest model available.

## Procedure

### Step 0: Resolve the input

- Confirm **both** `sf` aliases now (R3 delivery org and target org).
- **Pasted brief or ticket text**: save it verbatim to `{ws}/00-source.md`.
- **Work item** (WI number, record Id, or URL): fetch it with its children via
  `sf data query` / `sf` SOQL against the R3 delivery org:

```sql
SELECT Id, Name, Subject__c, Description__c, User_Story__c, Deliverables__c,
       Implementation__c, Assumptions__c, Acceptance_Criteria__c, Status__c,
       Type__c, Project__c, Feature__c, Related_Work_Item__c,
       (SELECT Name, Scenario__c, Given__c, When__c, Then__c, Status__c
          FROM Acceptance_Criteria__r),
       (SELECT Name, Summary__c, Context_Type__c, Context__c, Confidence__c,
               Source_URL__c FROM Work_Item_Contexts__r
         WHERE Status__c = 'Current')
FROM Work_Item__c WHERE Name = 'WI-160513'
```

  Render everything to `{ws}/00-source.md`, AC child records as a table.
- Optional GBrain: company / contact / HL product / HL project only.
- **Already built?** If the work item's Status implies the change exists (QA,
  Implemented, Deployed, Accepted) or the target change is already present in
  the working copy, record it in run-state `keyFindings`, write the cards as
  idempotent verify-and-set contracts, and flag it at the gate: never ask a
  human to approve work that is already done.
- **Stale anchors.** Context records cite `file:line` anchors that drift as
  siblings deploy. Re-locate every cited symbol in the current working tree
  (read-mostly DX repo if attached) and record the live anchors in
  `00-source.md`; never pass a stale anchor into a build card.
- If the fetch fails, ask the user to paste the content. Never reconstruct a
  record from memory or guesswork.

### Step 1: Normalise requirements

Delegated: **SA-REQ** (Phase A) produces `{ws}/01-requirements.json` using the
schema in `references/templates.md`. The rules below define what good looks
like; the brief packages them.

- Every functional requirement gets an ID (`FR-01`, ...) and a **testable**
  statement, sourced from the Acceptance Criteria field, Description, User
  Story, and any AC child records present.
- Every FR carries acceptance criteria (`AC-01.1`, ...) in Given / When / Then
  form.
- **Enumerate edge cases per FR**: boundaries (dates, thresholds), records
  moving into or out of scope after creation, nulls and blanks, bulk volumes,
  and behaviour for each actor class (human, automation, integration user).
  The classic miss: a rule specifies creation but not what happens when a
  record's date is *edited* across the boundary. Hunt for that shape.
- Record every assumption with its evidence source. Silent assumptions are how
  designs fail review.

### Step 2: Org and programme scan

Delegated: **SA-ORG** and **SA-PROG** run in parallel with SA-REQ (Phase A);
light runs merge them into one narrow scan sub-agent. Raw describes and SOSL
results stay with the sub-agents; you receive the distilled scan files.

**Org scan (target org)**, saved to `{ws}/context/org-scan.md`:

- Describe each object the design will plausibly touch (fields, record types,
  relationships): `sf sobject describe -s <Object> --target-org <alias> --json`.
- List existing automation on those objects: Apex triggers (Tooling API via
  `sf`) and active Flows (`FlowDefinitionView WHERE IsActive = true`), filtered
  to the objects in scope. Note which automations **edit** records the design
  will constrain; validation rules and locks fire on automation edits too.
- For any field the design will place on a page, determine whether the
  sibling fields live on a classic Layout or a FlexiPage (Dynamic Forms) and
  name the exact metadata component and section. "The page layout" is not a
  finding; `Project_R3_Record_Page`, Configure Estimate section, is.
- For in-scope objects, inventory existing test classes (creating a duplicate
  is a defect) and, for each in-scope field, whether it is a formula, roll-up
  or plain field: this decides whether tests can write it directly or must
  seed via child records.
- Enumerate **active validation rules** on every object the design writes to.
  Any rule firing on insert without an `ISNEW()` guard blocks naive test-data
  creation and is named as a test precondition in the Test strategy.
- Record the **live org API version** alongside the repo `sourceApiVersion`.
  Version-sensitive types (ConnectApi in particular) differ between them; the
  delta is an assumption the architect must resolve before pinning any typed
  accessor.

**Programme scan (R3 delivery org)**, saved to `{ws}/context/programme-scan.md`.
This is where sibling-collision bugs and tribal knowledge live (not GBrain):

1. This work item's `Work_Item_Contexts__r` (already fetched at Step 0).
2. Dependencies both directions on `Work_Item_Dependency__c`, then fetch those
   work items with their Current context records.
3. `Related_Work_Item__c` links, both directions.
4. In-flight siblings on the same `Feature__c` (Status not in Deployed,
   Accepted, Rejected, Won't Do): subject, description, contexts.
5. For each in-scope object, search for other work that touches it, using
   **both the API name and the label** (context records mostly say "Time
   Entry", not `Time_Entry__c`; the label comes from the Step 2 describe):

   ```
   FIND {Time_Entry__c OR "Time Entry"} RETURNING
     Work_Item__c(Name, Subject__c, Status__c
       WHERE Status__c NOT IN ('Deployed','Accepted','Rejected','Won''t Do')),
     Work_Item_Context__c(Name, Summary__c, Context_Type__c, Work_Item__c
       WHERE Status__c = 'Current')
   ```

   The `Work_Item__c` clause is filtered to in-flight items (the conflict
   list). The `Work_Item_Context__c` clause is deliberately **not** filtered
   by parent status: test traps and conventions live in the contexts of
   already-deployed work.

Extract three lists into the scan file: **conventions** (which field the
programme keys on, naming patterns), **test traps** (required setup records,
flows that null fields in tests; Testing Context records are the prime source),
and **potential conflicts** (in-flight work items whose behaviour intersects
this one).

If no org is reachable, proceed, but every org-dependent guess becomes a logged
assumption raised at G0.

### Step 3: Read the standards

- `references/salesforce-standards.md`: **always**, before G0, so your proposed
  defaults are standards-aligned (includes **SLDS 2** for any UI).
- `references/sharing-visibility.md`: when the work item touches record access
  in any way: new objects or personas, Experience Cloud or guest users, locks,
  OWD or sharing changes, or any "who can see what" requirement.
- `references/mule-standards.md`: when integration or MuleSoft work is in scope.

The standards win over habit and over training-data defaults. Any deviation
requires an ADR.

### Step 4: Gate G0, the decision checkpoint

**Hard stop: no architecture is authored before G0 rulings are recorded.**

**ADHD presentation** (align with `i-have-adhd`):

1. **Answer first**: one-line status ("3 decisions need a ruling" or "no open
   decisions; proceeding").
2. **Short options**: for each `D-NN`, question + proposed default in one
   breath; skip long preamble.
3. **One next action**: end with a single ask ("Reply `agree` or rule by
   number").

Full format: `references/templates.md` section 7. Present:

1. **Blocking ambiguities** the scans could not resolve.
2. **Cross-work-item conflicts** from the programme scan (this feature's
   in-flight siblings whose behaviour intersects), each framed as "who wins?".
3. **Policy decisions**: exemptions (does automation bypass the lock?), sync
   mechanisms, visible behaviour changes, anything with two defensible answers.

For every item, propose a default with a one-line rationale so the user can
reply "agree" in one word, or rule differently. Record every ruling verbatim in
`state/run-state.json` under `gate0`. Rulings are requirements: fold them into
`01-requirements.json` before designing. If there are genuinely no items, say
so in one line and proceed; do not invent questions to fill the gate.

### Step 5: Design

Delegated: **SA-ARCH** (Phase C, strongest tier) produces
`{ws}/02-architecture.md`, the ADRs and `{ws}/02-components.json` per its
brief. Non-negotiables the design must meet:

- At least one Mermaid `sequenceDiagram` of the main flow. A Mermaid `erDiagram`
  whenever the data model changes.
- **Declarative before code** where declarative genuinely meets the requirement.
  Follow the decision ladder in the standards; justify each step down it.
- Exact formulas, exact field API names, exact SOQL. "The entry's date" is not a
  design; `Start__c` (per programme convention, source cited) is.
- Governor limit analysis with **stated volumes** and why the design survives
  them.
- Security model per component, built on the persona x object **access matrix**
  from `references/sharing-visibility.md`, including the exemption model for
  any lock or validation rule (see standards section 14) and explicit
  "must not see" rows.
- Any Salesforce UI / UX in scope **must** follow **Salesforce Lightning Design
  System 2 (SLDS 2)**; state this in the architecture and in every UI build
  card.
- A requirement traceability table: every FR maps to at least one component.
- A **Deployment and data steps** section: permission set assignments, custom
  setting or CMDT records, flow activation, ordered. Data steps are components
  too and appear in the plan.
- A **deferred G0 decision never becomes an FR**: the committed build
  implements the stated baseline, and the alternative is recorded in
  `01-requirements.json.outOfScope` with a pointer to its
  `gate0.deferredDecisions` id and ADR. This keeps lint traceability honest
  while leaving the business choice open.
- Where an FR is **already satisfied by existing code**, do not invent a
  component: mark the FR `status: SATISFIED-EXISTING` with `file:line`
  evidence (templates section 1) and show it as "existing" in the
  traceability table.
- If a requirement **cannot be met as written**, say so plainly. Never design
  around it silently.

Write one `02-adr-NN-<slug>.md` per significant decision. G0 rulings that shaped
the design each get an ADR referencing the ruling.

### Step 6: Verify the design

SA-ARCH produced the artefacts; you verify them before spending the user's
gate: all three outputs exist; `{ws}/02-components.json` parses against the
schema in `references/templates.md`; every FR appears in some `satisfies`;
parallel work packages share **no files**; data steps are present as
components. Gaps go back to SA-ARCH with the gap named, never patched
silently.

### Step 7: Red-team, then Gate G1 (mandatory human approval)

First, form your own view. Re-read the design as a hostile reviewer: what breaks
at 10x volume, what happens on partial failure, which existing or **in-flight**
automation collides, what would a Salesforce CTA circle in red?

Check the high-risk triggers:

| Trigger |
|---|
| PHI or patient-identifiable data touched |
| Sharing model, OWD, restriction or scoping rules, Experience Cloud or guest access changes |
| Destructive changes (field/object deletion, data migration) |
| New external integration |
| More than 8 components, or LDV objects (>1M rows) in scope |

If **any** trigger fires: set `escalated: true` in run-state and run a dedicated
review pass before presenting. Delegate **SA-REVIEW** (brief in
`references/delegation-briefs.md`); a cross-model review skill, if installed,
also qualifies. Fold findings back into the design or into your stated reservations.
When a review or card-writer finding corrects a **fact** (a field's nature, an
existing class, a wrong premise), re-fold it into `01-requirements.json`
before Sync 1: the synced requirements must never contradict the approved
design.

Then present to the user with **ADHD presentation** (answer first, short
options, one next action). Full order in `references/templates.md` section 8:

1. Five-bullet solution summary, plain English.
2. Component table (name, type, action, purpose).
3. Top risks with mitigations.
4. ADR titles with one-line decisions.
5. **Your own reservations, if any.** Presenting a design you privately doubt,
   without saying so, wastes the human's gate.

Close with one ask: "Approve this design for implementation, or say what to
change?" Iterate on feedback until approved. Record the approval **verbatim** in
`state/run-state.json`.

**Hard stop: no build cards before recorded approval.**

**Sync 1.** G1 approval **is** the write authorisation for this run; do not
ask again. Immediately after approval, sync the design layer to Salesforce
(R3 delivery org only) via `sf` per `references/templates.md` section 9: the AC
and Assumptions fields rewritten behind the drift guard, and context records for
the requirements, architecture, each ADR and the G0 rulings. Write, then report
the diff table (create / update / stale counts with keys) and record Ids after
the fact. If the run dies later, the approved design is already on the work item.

### Step 8: Build cards

Delegated: **SA-CARDS**, one per work package, spawned in the same turn
(Phase E; brief in `references/delegation-briefs.md`, which carries the full
input bundle including `01-requirements.json` and the G0 rulings, because a
card writer holding only the architecture doc works from a summary of a
summary). Each writes `{ws}/02-build-cards/BC-NN-<slug>.md` for its own
components only, per `references/build-card-template.md`.

- Every test trap from the programme scan that applies to a card lands in that
  card's Test spec as an explicit precondition, with the setup records named.
  The implementer must never discover a trap the scan already knew about.
- Every UI / LWC / Experience card states **SLDS 2** compliance.
- Every card that needs human-in-the-browser verification includes an
  **AI-executable Browse / Kernel manual test script** (in the Test spec under
  `Manual verification:` and/or as a file under `02-browse-tests/`).
- Light runs: one SA-CARDS for the single work package is fine.

### Step 9: Lint, sync, hand off

Run the deterministic lint and fix every finding, repeating until it exits 0:

```bash
python3 <skill-path>/scripts/lint_build_cards.py {ws}
```

Confirm the exit criteria:

- [ ] Architecture, ADRs, components JSON and build cards exist and are
      internally consistent
- [ ] Every FR traces to a component and to at least one build card
- [ ] Deployment and data steps documented, with owning cards
- [ ] G0 rulings and G1 approval recorded verbatim in `state/run-state.json`
- [ ] Lint exits 0 (note its scope: it format-checks cards, requirements and
      the component plan; it does not read the architecture doc or ADRs)
- [ ] Card audit blockers and majors resolved (standard and escalated runs)
- [ ] Browse / Kernel scripts present where manual UI verification is required
- [ ] Any UI components state SLDS 2

**Card audit (Phase F).** The lint proves format; **SA-AUDIT** proves the
cards are right. Delegate it (brief in `references/delegation-briefs.md`) on
at least one card per work package, riskiest first: does the SOQL do what the
FR says, do the tests actually prove the Then clauses, are the edge cases
present, do Browse scripts name exact selectors / expected outcomes. Fix
blockers and majors (edit or re-delegate the card), re-run the lint, and only
then sync. Optional on light runs.

**Sync 2.** Sync the build layer to Salesforce per `references/templates.md`
section 9: the component plan and each build card as Implementation Notes
records, and any newly discovered test traps as Testing Context records
(future programme scans must find them). Same protocol as Sync 1: automatic,
no prompt, write then report the diff table and Ids. The work item now
carries the entire package; a card is fetchable by `Summary__c` key without
the workspace.

**Hand off**: each implementer (model or human) gets **one build card** (file,
or fetched from its Implementation Notes record), **`salesforce-standards.md`,
only the existing source files that card lists, and
`scripts/verify_implementation.py`**. The implementer's definition of done
includes running the verifier against the repo and fixing every failure:

```bash
python3 <skill-path>/scripts/verify_implementation.py <card.md> <repo-root> [--diff-base <ref>]
```

It enforces the card statically: changed files must match the Files table,
Must-not scans (SeeAllData, unauthorised `without sharing`, TODO markers,
hardcoded-Id and debug warnings), and every Test spec method must exist.
Deploying to the target sandbox and running the tests are the implementer's
deploy step; the verifier is the static gate before it (it supports non-git
trees via `--baseline`; an implementer must **never** run `git init` to
appease it). When several implementers build concurrently, **serialise the
working tree**: file ownership governs authorship, not physical write safety,
so one agent's diff is applied and committed before the next agent touches
the tree. Concurrent tree churn has already truncated files once. Never hand
an implementer the whole workspace; extra context invites improvisation, and
improvisation by a small model is the failure mode this skill exists to prevent.

### Step 10: Retrospective (the improvement loop)

Write `{ws}/90-retrospective.md` using the template in
`references/templates.md` section 10, after Sync 2, before declaring the run
complete. This file is how the skill gets better: it is fed back into a
skill-improvement session, so vagueness here wastes the loop.

- Be honest about the skill, not the work item: where its instructions were
  wrong, ambiguous or missing; what the scans missed that the user knew;
  every gate iteration and what caused it; every place the run deviated from
  SKILL.md and why.
- At least one challenge is required. A run with genuinely none must say what
  evidence supports that, which is rare enough to be suspicious.
- Each recommended improvement names the skill file and section to change and
  proposes the wording.

Do not sync the retrospective to Salesforce; it critiques the skill, not the
work item.

## The quality bar: zero open decisions

An implementer with no other context must never have to choose. The full
definition, the banned-phrase list and the exactness rules (API names,
signatures, picklist API values, error tables, tests that prove Then
clauses, Browse / Kernel scripts) live at the top of
`references/build-card-template.md`; the lint and SA-AUDIT enforce it.

## Reference files

| File | Read when |
|---|---|
| `references/salesforce-standards.md` | Always, before Step 4 (includes SLDS 2) |
| `references/sharing-visibility.md` | Record access, visibility, sharing, Experience Cloud or guest scope |
| `references/mule-standards.md` | Integration or Mule in scope |
| `references/delegation-briefs.md` | Any phase that spawns a sub-agent |
| `references/templates.md` | Steps 1, 4, 5, 6, 7 (schemas, templates, G0/G1 format, sync) |
| `references/build-card-template.md` | Before writing any build card |
| `references/r3-data-model.md` | Before Step 0 |

---
*work-item-architecture QM pack v2.0.0, R3 Digital, 18/09/2026. QM-native
orchestration (orchestrator + parallel sub-agents), sf CLI + Admin Salesforce
skills as the tool surface, Sprite `./work-items/<id>/` workspace, auto Sync 1/2,
SLDS 2 for UI, Browse/Kernel manual test scripts, GBrain limited to HL context,
ADHD gate presentation. Preserves Light/Standard/Escalated sizing, G0/G1,
coordinated change sets, lint + verifier, and the R3 data model.*
