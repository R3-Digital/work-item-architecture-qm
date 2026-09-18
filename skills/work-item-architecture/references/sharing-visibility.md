# Sharing and Visibility Architecture (R3 Digital)

Read when the work item touches record access in any way: new objects, new
personas, Experience Cloud, "who can see/edit what" requirements, locks,
reports crossing teams, or any OWD/sharing change. Object and field security
alone (CRUD/FLS) is covered in `salesforce-standards.md` section 8; this file
is the **record visibility** decision space.

Two different questions, never conflate them:

- **Object and field security** (profiles baseline, permission sets, FLS):
  what a user may *do* with records they can see.
- **Record sharing**: *which* records they can see at all.

## Contents

1. Design method
2. Mechanism selection tables
3. Experience Cloud and external access
4. Implicit sharing
5. Performance and LDV
6. Decision rules: ADR, G0 and escalation triggers
7. Testing visibility
8. Build card implications

---

## 1. Design method

Work these five steps, in order, and record the result in the architecture
document's Security model section.

1. **Access matrix first.** Build a persona x object table from the
   requirements: Read / Edit / None per persona, including automation and
   integration users, and an explicit row for who must **not** see records.
   "Must not see" lines are requirements with FR IDs, not footnotes.
2. **Set the baseline.** OWD per object, internal and external separately.
   Most restrictive default that any persona needs; external never looser than
   internal. Changing an existing OWD is an escalation trigger.
3. **Grant back up the ladder.** Open access with the cheapest adequate
   mechanism, in this order: role hierarchy, sharing rules (owner-based then
   criteria-based), teams, groups, share sets (external), manual sharing,
   Apex managed sharing. Each step down the ladder needs a reason.
4. **Subtract and filter sparingly.** Restriction rules to hide records that
   sharing would otherwise show; scoping rules only to change the default
   lens, never as security. Both are org-limited per object, so treat them as
   scarce.
5. **Verify.** Check implicit sharing side effects, licence fit, performance
   at stated volumes, and that every matrix cell is proven by a test.

## 2. Mechanism selection tables

**Baseline and object/field layer**

| Mechanism | Use for | Traps |
|---|---|---|
| Organization-Wide Defaults (internal + external) | The floor per object | External OWD must be equal or more restrictive; OWD changes trigger full recalculation |
| Profiles | Login policy, defaults, one per user; baseline only | Grant no access via profiles in new work; use Minimum Access as base |
| Permission Sets | The primary grant vehicle: object, field, user and custom permissions | Additive only; cannot subtract |
| Permission Set Groups | Persona bundles of permission sets | Muting inside a PSG is the only subtractive permissions tool; recalc delay after edits |
| Object / Field Permissions (CRUD / FLS) | What a persona may do and which fields exist for them | FLS does not hide records; enforce in code via user mode |
| User Permissions (system) | View All Data, Modify All Data, View All Fields, Manage Users | View All / Modify All (object or org level) are architecture decisions: ADR always |
| Custom Permissions | Feature gates and bypass switches checked in formulas, Flows and Apex | Grant via a dedicated permission set; document holders as a data step |
| User Access Policies | Automate PS / PSG / group / queue assignment on user lifecycle events | This is the default answer to "keep assignment in sync with membership"; manual sync processes need an ADR explaining why not UAP |

**Record sharing layer (grants)**

| Mechanism | Use for | Traps |
|---|---|---|
| Role Hierarchy | Vertical, manager-sees-reports access | Custom objects can disable Grant Access Using Hierarchies; deep hierarchies with many small roles hurt recalc |
| Sharing Rules (owner-based, criteria-based) | Lateral grants to roles, roles-and-subordinates, groups | Grant-only; criteria-based rules evaluate on record save, not continuously |
| Public Groups | Grant targets and rule building blocks | Nested and churning groups slow sharing recalculation |
| Personal Groups | User-owned convenience lists | Never part of an architecture; do not design on them |
| Account / Opportunity / Case Teams | Per-record collaborative access with roles | Team membership is data, not metadata; state how teams are populated |
| Enterprise Territory Management | Geography / segment based account access | Heavy machinery; ADR before introducing it |
| Manual Sharing | Ad hoc, user-initiated exceptions | Manual shares are deleted when record owner changes; never design a process on manual sharing |
| Apex Managed Sharing | Programmatic grants no declarative tool can express | Custom rowCause survives owner change; needs an ADR, recalculation handling and tests |
| Compliant Data Sharing (Health Cloud / FSC) | Participant-role based collaboration on regulated records | Additive per enabled object; the natural fit for care team visibility in Health Cloud work |

**Subtract and filter layer**

| Mechanism | Use for | Traps |
|---|---|---|
| Restriction Rules | Hide a subset of records a user could otherwise see (the only record-level subtract) | Small per-object active limit (2 on most editions, 5 on the top ones); supported on custom objects plus a short standard list (tasks, events, contracts, timesheets); test interaction with View All |
| Scoping Rules | Default working set in lists, search and reports | **Not security**: records stay reachable by Id and via APIs; never satisfy a "must not see" requirement with a scoping rule |

## 3. Experience Cloud and external access

- **Licence drives the toolset.** Customer Community licences have no roles:
  record access comes from **Share Sets** (records related to the user's
  account or contact) and sharing to the site's groups. Customer Community
  Plus and Partner licences have roles: sharing rules, external role
  hierarchy and super user access apply.
- **External Account Hierarchy** gives roll-up visibility across related
  external accounts (parent distributor sees child dealers) without minting a
  role per account.
- **Account Relationships and Account Relationship Data Sharing Rules** share
  records laterally between partner accounts in channel models; use when two
  external organisations must see each other's records.
- **Guest users** are their own regime: guest OWD is locked private, access
  comes only from guest sharing rules (criteria-based, read-only), and records
  created by guests should be reassigned on creation. Any guest-facing scope
  gets its own row in the access matrix and its own tests.
- External sharing model must be enabled deliberately; state internal and
  external OWD side by side in the architecture.

## 4. Implicit sharing

Built-in behaviour that designs forget and audits find:

- Access to a child (case, opportunity, contact) grants read access to its
  parent account; account access grants access to children per the account
  owner's settings.
- Experience Cloud users get implicit access to their own contact and its
  account.
- Implicit sharing cannot be switched off; design around it, and check it does
  not quietly satisfy or violate a matrix cell.

## 5. Performance and LDV

- **Ownership skew**: keep any single owner (including integration users and
  queues) under roughly 10,000 records per object, or plan for it explicitly.
- **Parent skew**: tens of thousands of children under one account slows
  sharing recalculation and locks.
- Group and role churn recalculates sharing; bulk membership changes during
  business hours can lock the org. For large migrations, plan **deferred
  sharing calculation** and state it in Deployment and data steps.
- OWD changes on large objects are change-window events, not casual deploys.

## 6. Decision rules: ADR, G0 and escalation triggers

Always an **ADR**: OWD change; View All / Modify All grant; `without sharing`
Apex; Apex managed sharing; territory management; restriction rule
introduction; external sharing model enablement.

Always a **G0 question** (business, not technical): which personas see which
records, any "must not see" boundary, partner-to-partner visibility, whether
managers see subordinates' records, and who is exempt from any lock.

Always **escalate the run** (SKILL.md triggers): OWD or sharing model changes,
restriction or scoping rules, and any Experience Cloud or guest access change.

## 7. Testing visibility

- One `System.runAs` test per persona in the access matrix, asserting both
  positive access and **negative** ("must not see" proven by an empty query
  result or a QueryException, run as that user).
- Test sharing behaviour after owner change for any design touching manual or
  team sharing.
- Guest and Experience personas get their own runAs rows; licence-specific
  behaviour cannot be inferred from internal tests.

## 8. Build card implications

- Sharing rules, restriction rules, scoping rules and sharing settings are
  **deployable metadata**: type `SharingRule` or `RestrictionRule` in
  `02-components.json`, specified in a `## Metadata spec` (full criteria,
  shared-to target, access level).
- Group membership, team population, manual shares, UAP activation order and
  deferred-recalc toggles are **data steps** owned by a card and listed in
  Deployment and data steps.
- Every card whose component reads or writes shared data states the sharing
  context it runs in and which matrix rows its tests prove.
