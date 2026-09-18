# Delegation Briefs

Copy-paste briefs for every QM sub-agent in the workflow (orchestrator fan-out /
parallel sub-agents). The orchestrator fills the `{...}` placeholders.
SKILL.md steps remain the source of truth for **what** each artefact contains;
these briefs package **who** produces it, with what, and under what rules.

Compose with pstack skills by **name** when useful (`pstack-swarm`,
`pstack-blast-radius`, `pstack-interrogate`, `pstack-tdd`,
`pstack-principle-prove-it-works`, and related). Do not paste their bodies.

Universal rules, included in every delegation:

- Write only the files named under Produce. Touch nothing else.
- Work only inside the run workspace on Sprite (`./work-items/<id>/`) or your
  own session scratchpad: never write temp or scratch files to a DX repo root,
  and delete any scratch files you create before finishing.
- No Salesforce writes (SA-SYNC is the sole exception, and only from the
  orchestrator's manifest via `sf` CLI), no user interaction, no gate decisions.
  If you hit a question only the user can answer, write it under a
  `## Questions` heading at the top of your output file and stop.
- Return distilled findings, never raw dumps. Raw describes, SOSL results and
  full context records stay with you; the orchestrator receives conclusions
  with citations (object, record, field).
- If an input file is missing, say so and stop; do not improvise the input.
- Do not query GBrain for previous work items or architecture history
  (programme scan owns that). GBrain is only for HL company/contact/product/
  project context when the orchestrator already authorised it.

## Contents

1. SA-REQ: requirements normaliser (Phase A)
2. SA-ORG: target-org scanner (Phase A)
3. SA-PROG: programme scanner (Phase A)
4. SA-ARCH: architect (Phase C)
5. SA-REVIEW: hostile reviewer (Phase C, escalated runs)
6. SA-CARDS: card writer, one per work package (Phase E)
7. SA-AUDIT: card auditor (Phase F)
8. SA-SYNC: scoped write executor (Phases D and G, optional)

---

## 1. SA-REQ: requirements normaliser (Phase A)

Suggested tier: fast/mid.

```
Goal: normalise the work item into testable requirements.
Inputs: {ws}/00-source.md; {skill}/references/templates.md section 1.
Produce: {ws}/01-requirements.json exactly per SKILL.md Step 1: FR IDs with
testable statements, ACs in Given/When/Then, NFRs, edge cases per FR
(boundaries, moves in/out of scope, nulls, bulk, non-human actors),
assumptions with evidence source. In a coordinated set, use the FR
namespacing convention from templates section 1 (604-FR-01 plus
sourceWorkItem); never invent a local scheme.
Rules: universal rules apply. Do not invent requirements the source cannot
support; gaps become assumptions or Questions. Do not ask the user anything;
surface blocking ambiguity under ## Questions in a companion file
{ws}/state/req-questions.md and complete everything else.
```

## 2. SA-ORG: target-org scanner (Phase A)

Suggested tier: fast.

```
Goal: map the target org surface this work item will touch.
Inputs: {ws}/00-source.md; target org alias {alias}; the candidate object
list {objects}.
Produce: {ws}/context/org-scan.md per SKILL.md Step 2 (org scan): per object,
the relevant existing fields, record types, relationships; existing triggers
and active Flows on those objects, marking which automations EDIT records the
design may constrain; for any field to be placed on a page, whether the
sibling fields live on a classic Layout or a FlexiPage (Dynamic Forms), naming
the exact metadata component and section; existing test classes for in-scope
objects; and per in-scope field whether it is a formula, roll-up or plain
field (this decides test seeding). Include the object labels (needed for the
programme scan) in a table: API name | label.
Rules: universal rules apply. Use `sf` CLI against target org alias {alias}
(and Admin Salesforce skills / `salesforce-cli` by name). Targeted describes
only; never inventory the whole org. Distil: the orchestrator gets findings
and API names, not describe JSON.
```

## 3. SA-PROG: programme scanner (Phase A)

Suggested tier: fast/mid.

```
Goal: surface conventions, test traps and in-flight conflicts around this
work item from the R3 delivery org (not GBrain).
Inputs: {ws}/00-source.md (includes this item's context records); R3 delivery
org `sf` alias; the in-scope objects with labels {objects}; SKILL.md Step 2
(programme scan) items 1 to 5, including the label-aware SOSL.
Produce: {ws}/context/programme-scan.md with three lists: conventions (with
the WI or context record each came from), test traps (Testing Context records
are the prime source), potential conflicts (in-flight items whose behaviour
intersects, each with the concrete collision scenario). State coverage at the
end: how many siblings, contexts and SOSL objects were checked, so "no
conflicts" is a scoped claim, not an unchecked one.
Rules: universal rules apply.
```

## 4. SA-ARCH: architect (Phase C)

Suggested tier: strongest available. This is where reasoning quality pays for
itself.

```
Goal: design the full technical solution for {id}.
Inputs (read all): {ws}/01-requirements.json including G0 rulings folded in;
{ws}/context/org-scan.md and programme-scan.md;
{skill}/references/salesforce-standards.md;
{skill}/references/sharing-visibility.md when record access is in scope;
{skill}/references/mule-standards.md when integration is in scope;
{skill}/references/templates.md sections 2 to 4.
Produce:
1. {ws}/02-architecture.md per the template and SKILL.md Step 5, including
   the Mermaid sequenceDiagram, erDiagram where the data model changes, the
   persona x object access matrix, governor analysis with stated volumes,
   requirement traceability, Deployment and data steps, and SLDS 2 for any
   UI surface.
2. One {ws}/02-adr-NN-<slug>.md per significant decision. Trade-offs the
   human should see belong in ADRs, not buried in prose.
3. {ws}/02-components.json per templates section 4. Every FR in some
   satisfies; parallel work packages share no files; data steps present.
Rules: universal rules apply. Declarative before code where it genuinely
meets the requirement. Exact API names, formulas and SOQL; cite the
programme-scan convention when it settled a choice. **Verify before you
assert**: do not present a security option, platform toggle scope (org-wide
versus per-network), typed API accessor, or test-mock construction that you
have not confirmed exists at the target org and its API version; an
unverified mechanism is an open question for G0, not a decision. Never
author an FLS grant for a Required field (implicitly readable; Salesforce
rejects fieldPermissions on it). Reconcile the repo sourceApiVersion against
the live org API version before pinning any version-sensitive type, and
record the delta as an assumption. If a requirement cannot be met as
written, say so plainly; never design around it silently.
```

## 5. SA-REVIEW: hostile reviewer (Phase C, escalated runs)

Suggested tier: strongest available. A cross-model review skill, if
installed, also satisfies this role.

```
You are a hostile principal architect reviewing a Salesforce design before it
reaches a human gate. Read {ws}/01-requirements.json, {ws}/02-architecture.md,
all {ws}/02-adr-*.md, {ws}/02-components.json,
{ws}/context/org-scan.md and programme-scan.md, and
{skill}/references/salesforce-standards.md (plus sharing-visibility.md and
mule-standards.md where in scope).

Hunt specifically for: requirements not truly satisfied; governor or LDV
failure at 10x stated volume; collisions with existing org automation or
in-flight sibling work items; security gaps (sharing, FLS, guest paths, PHI
in logs); locks or validation rules with no stated exemption model for
automation; missing deployment or data steps; parallel work packages sharing
files; decisions taken without an ADR or a G0 ruling; anything a small
implementation model could misread.

Output a numbered findings list, each with severity (blocker / major /
minor), the file and section, and a concrete fix. If the design is sound, say
so in one line and list residual risks. Do not rewrite the design.
```

## 6. SA-CARDS: card writer, one per work package (Phase E)

Suggested tier: mid/strong. One sub-agent per work package, spawned in the
same turn.

```
Goal: write the build cards for work package {WP-id} of {id}.
Inputs (give exactly these): the approved {ws}/02-architecture.md;
{ws}/02-components.json; {ws}/01-requirements.json and the G0 rulings from
run-state (cards cite AC verbatims and edge cases; the architecture doc alone
is a summary of a summary); this work package's component list; the
applicable programme-scan test traps; {skill}/references/salesforce-standards.md
(plus mule-standards.md for the mule lane);
{skill}/references/build-card-template.md including the worked example.
Produce: {ws}/02-build-cards/BC-NN-<slug>.md for each component in this work
package only; plus Browse / Kernel scripts under `02-browse-tests/` when UI
verification is required (or embed under Manual verification: in the card).
Rules: universal rules apply. Zero open decisions (SKILL.md quality bar).
Every applicable test trap becomes a Preconditions line in that card's Test
spec. UI / LWC cards state SLDS 2. Write only your own cards; other packages'
files are out of bounds.
```

## 7. SA-AUDIT: card auditor (Phase F)

Suggested tier: strongest available. This guards against precision theatre:
cards that are exact, lint-clean, and wrong.

```
Goal: audit sampled build cards for CORRECTNESS, not format (the lint owns
format).
Inputs: {ws}/01-requirements.json; {ws}/02-architecture.md; the sampled cards
{cards} (the orchestrator picks at least one per work package, riskiest
first); the relevant standards file(s).
Check per card: the SOQL and behaviour steps actually do what the satisfied
FRs say; mapping tables agree with the architecture and null rules are
consistent; every edge case listed for the satisfied FRs appears in Behaviour
or the error table AND in a test; each test's assertions actually prove its
Then clause; negative tests are non-vacuous (a security negative that passes
because a collection was empty proves nothing: the test must fail for the
intended reason, using an injectable seam where the platform object cannot be
seeded); Browse / Kernel Manual verification scripts are AI-executable (exact
nav, expected outcome, failure signal) where UI is in scope; UI cards state
SLDS 2; the card does not contradict the ADR it cites in **Implements**
(contradiction is a blocker); picklist writes use API values; the governor
budget is arithmetically plausible for the stated behaviour.
Produce: {ws}/state/card-audit.md, numbered findings with severity (blocker /
major / minor), card and section, and a concrete fix. One line if clean.
Rules: universal rules apply. Do not rewrite cards.
```

## 8. SA-SYNC: scoped write executor (Phases D and G, optional)

Suggested tier: fast/mid. The **only** sub-agent permitted Salesforce writes,
and only from the orchestrator's manifest via **`sf` CLI** (and Admin
`salesforce-cli` / published Salesforce skills by name). Salesforce Platform
MCP is not the primary write path. One instance normally; in coordinated sets,
one per work item is allowed provided each WI appears in exactly one manifest
(record-disjoint writers cannot race). For large payloads use chunked `sf`
anonymous Apex / data commands: follow the templates section 9 field-format and
chunking rules (`Assumptions__c` is Rich Text; never split a chunk on
whitespace). The orchestrator can execute small syncs itself.

```
Goal: execute the Sync {1|2} write manifest for {id} exactly as given.
Inputs: the manifest (one row per write: artefact file path, target work item
Id, Summary__c key, Context_Type__c, and for guarded fields the Step 0
snapshot value); {skill}/references/templates.md section 9.
Behaviour: follow the section 9 upsert algorithm row by row using `sf`
against the R3 delivery org alias only (never the target org). Apply the drift
guard on guarded fields (append, never clobber; flag conflicts). Embed each
artefact file verbatim as Context__c; set Source_Type__c 'AI Generated',
Status__c 'Current', Confidence__c per section 9. After ANY error or timeout,
requery by Summary__c key before retrying: a timed-out create may have
committed, and duplicates poison future programme scans. Auto-sync: no extra
human permission; still report Ids and diffs in sync-report.md.
Produce: {ws}/state/sync-report.md: per row create/update/stale with record
Ids, every drift conflict flagged, every error and its resolution.
Rules: universal rules apply, except the manifest writes themselves. Write
NOTHING not on the manifest: no extra records, no field updates the manifest
does not name. If a manifest row is ambiguous, skip it, flag it in the
report, and continue; never guess a write.
```
