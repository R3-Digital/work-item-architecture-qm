# Build Card Template

A build card is the **entire brief** for one component. The implementer (often
a non-frontier / cheaper model, or a junior) receives the card,
`salesforce-standards.md`, and the existing source files the card lists.
Nothing else. If the card does not say it, the implementer will guess it, and
the guess is your bug.

Cards are linted by `scripts/lint_build_cards.py`. The lint bans vague phrases
and checks the section requirements below, so write to them exactly.

## Card metadata block

Every card starts with this block. The lint parses it.

```markdown
# BC-NN: <ComponentName>
**Type**: <ApexClass|ApexTrigger|LWC|Flow|Field|Object|PermissionSet|ValidationRule|CustomMetadata|SharingRule|RestrictionRule|MuleApp|Other> | **Action**: <create|modify> | **Work package**: WP-N | **Lane**: <salesforce|mule>
**Depends on**: <BC-NN list or none> | **Satisfies**: FR-NN (AC-NN.N), ...
```

## Required sections by type

**Authoritative source: `references/card-sections.json`** (the lint loads it
directly). The table below mirrors the manifest for human reading; when
changing the contract, edit the JSON first, then this table.

| Section | Required for |
|---|---|
| `## Files` | all |
| `## Purpose` | all |
| `## Interface` | ApexClass, LWC (public API) |
| `## Behaviour` | ApexClass, ApexTrigger, LWC, Flow, MuleApp |
| `## Metadata spec` | Field, Object, PermissionSet, ValidationRule, CustomMetadata, SharingRule, RestrictionRule |
| `## Data steps` | PermissionSet (who gets assigned, and any records to create) |
| `## Security` | all |
| `## Governor budget` | ApexClass, ApexTrigger, Flow |
| `## Test spec` | all |
| `## Must not` | all |
| `## Done when` | all |

Section content rules:

- **Files**: table of `Action | Path`, full SFDX paths. `modify` cards also
  list which existing sections/methods change and which are untouched.
- **Interface**: exact code for every public signature, inner classes, `@api`
  properties and emitted events. Types, not descriptions of types.
- **Behaviour**: numbered steps. Exact SOQL as it should appear. Field mapping
  tables carry a null rule per row. Error behaviour is a table:
  `Condition | Behaviour`, one row per failure mode. Flow cards list every
  element in order: type, name, inputs, outputs, conditions, fault path.
  Picklist writes state the **API value**, never just the label, with the
  label in parentheses where they differ (`Urgency__c` value `2` (Medium),
  because its API values are `1` to `4`). A small model given a label writes
  an invalid value.
- **ADR citation**: where a card implements an ADR decision, the metadata
  block gains `**Implements**: ADR-NN (option/rung chosen)`, and the card's
  chosen value must match that ADR. SA-AUDIT fails a card that contradicts
  the ADR it cites; a card that silently inverts its governing ADR has
  already happened once.
- **Metadata spec**: full metadata table. For a Field: API name, label, type,
  length/precision, required, default, help text, history tracking, FLS per
  permission set. For a PermissionSet: every object/field/class grant.
- **Security**: sharing declaration and why; user-mode enforcement points;
  permission sets touched.
- **Governor budget**: max records per invocation, SOQL count, DML count,
  callout count, async pattern if any. Numbers.
- **Test spec**: test class name, then a table:
  `Method | Given | When | Then (exact assertions)`. Include single, bulk 200,
  negative, and a minimal-access `System.runAs` row for Apex. Name the data
  factory methods used. Where the programme scan flagged an org test trap that
  applies, open the section with a **Preconditions** line naming the exact
  setup records the tests must create first.
- **Browse / Kernel manual scripts**: any UI, FlexiPage, Experience, or
  human-in-the-browser path **must** include an AI-executable manual test
  script suitable for Browse / Kernel automated manual testing. Open that part
  of the Test spec with the exact phrase **`Manual verification:`** followed
  by a numbered script. Each step states: actor / persona, exact navigation
  (app, tab, record URL pattern or list view name), action, expected visible
  outcome, and failure signal. Prefer stable labels and data-test ids over
  brittle CSS. Optionally also save the same script under
  `02-browse-tests/BC-NN-<slug>.md`. Cards that are pure data steps may use
  `Manual verification:` without a browser script. The lint and the
  implementation verifier skip test-method checks when `Manual verification:`
  opens the Test spec.
- **UI cards**: state **SLDS 2** under Security or Behaviour (tokens / base
  components used; no custom colour hex unless ADR).
- **Data steps**: post-deploy actions in order: permission set assignments
  (who, via what mechanism), records to create with field values, flows to
  activate. Anything not deployable as metadata.
- **Must not**: the fence. Always includes: no components beyond `## Files`,
  no hardcoded IDs, no changes to files owned by other cards (name them if
  adjacent).
- **Done when**: checkboxes. Always includes: deploys clean to the target sandbox,
  all card tests pass, coverage threshold met, PMD clean, only listed files
  changed.

## Banned phrases

The lint fails a card containing any of: "as appropriate", "appropriately",
"as needed", "if necessary", "TBD", "TODO", "etc", "and so on", "for example",
"e.g.", "consider", "may want", "you could", "should probably", "similar to",
"usual pattern", "standard error handling", or "handle errors" without an
error table. Each of these marks a decision you skipped. Make it.

---

## Worked example

# BC-03: ReferralIntakeService
**Type**: ApexClass | **Action**: create | **Work package**: WP-2 | **Lane**: salesforce
**Depends on**: BC-01 (TestDataFactory), BC-02 (NHS_Number__c field) | **Satisfies**: FR-01 (AC-01.1), FR-02 (AC-02.1)

## Files

| Action | Path |
|---|---|
| create | force-app/main/default/classes/ReferralIntakeService.cls |
| create | force-app/main/default/classes/ReferralIntakeService.cls-meta.xml (apiVersion from sfdx-project.json) |
| create | force-app/main/default/classes/ReferralIntakeServiceTest.cls |
| create | force-app/main/default/classes/ReferralIntakeServiceTest.cls-meta.xml |

## Purpose

Convert unprocessed `Referral_Staging__c` records into triaged `Case` records,
linked to the existing patient `Account` when the NHS number matches, in one
bulk-safe pass.

## Interface

```apex
public inherited sharing class ReferralIntakeService {

    public class IntakeResult {
        public Id stagingId;
        public Id caseId;          // null on failure
        public Boolean success;
        public String errorMessage; // null on success
    }

    public class ReferralIntakeException extends Exception {}

    /** Processes staging records into Cases. Never throws for per-record
        failures; returns one IntakeResult per input in the same order. */
    public static List<IntakeResult> processStaging(List<Referral_Staging__c> stagingRecords) {}
}
```

## Behaviour

1. If `stagingRecords` is null or empty, return an empty list. No exception,
   no DML.
2. Collect non-blank `NHS_Number__c` values from the inputs.
3. Query matching patients:
   `SELECT Id, NHS_Number__c FROM Account WHERE NHS_Number__c IN :nhsNumbers WITH USER_MODE`
   Build `Map<String, Id>` keyed by NHS number. If two Accounts share an NHS
   number, keep the first returned and treat the input rows using it as
   matched (dedupe of Accounts is out of scope per architecture section 11).
4. Build one `Case` per staging record using this mapping:

| Target (Case) | Source (Referral_Staging__c) | Null rule |
|---|---|---|
| AccountId | Account match on NHS_Number__c | null when no match; Case still created |
| Subject | 'Referral: ' + Referrer_Name__c | when Referrer_Name__c blank, use 'Referral: Unknown referrer' |
| Description | Clinical_Summary__c | copy as-is; null allowed |
| Origin | fixed value 'e-Referral' | never null |
| Priority | Urgency__c value 'Urgent' maps to 'High'; every other value maps to 'Medium' | blank maps to 'Medium' |
| Referral_Staging__c | staging record Id | never null |

5. Insert with partial success:
   `Database.insert(cases, false, AccessLevel.USER_MODE)`.
6. Build the result list from the `SaveResult`s, preserving input order.
7. For successes only: set staging `Status__c = 'Processed'` and
   `Processed_On__c = System.now()`, then
   `Database.update(stagingUpdates, false, AccessLevel.USER_MODE)`.

Error behaviour:

| Condition | Behaviour |
|---|---|
| Case insert fails for a record | IntakeResult.success = false, errorMessage = first SaveResult error message; staging record left untouched |
| Staging update fails after Case insert | Case is kept; add ' (staging update failed)' to that result's errorMessage; success stays true |
| Query exception (locked rows, invalid field) | throw ReferralIntakeException wrapping the original; caller handles |

No PHI in exception messages: include record Ids only, never NHS numbers or
clinical text.

## Security

- `inherited sharing`: callers (BC-04 trigger handler, future batch) set the
  context.
- All SOQL `WITH USER_MODE`; all DML `AccessLevel.USER_MODE`.
- No permission set changes in this card (grants live in BC-06).

## Governor budget

- Max 200 staging records per invocation (enforced by caller per BC-04).
- Exactly 1 SOQL, at most 2 DML statements, 0 callouts, no async.

## Test spec

Class: `ReferralIntakeServiceTest`. Data via `TestDataFactory.createStagingReferrals(Integer count, String nhsNumber)` and `TestDataFactory.createPatientAccount(String nhsNumber)` from BC-01. All NHS numbers synthetic in the 999 000 0000 test range.

| Method | Given | When | Then (exact assertions) |
|---|---|---|---|
| testMatchedPatientLinksCase | 1 Account with NHS 9990000001; 1 staging record with same number | processStaging | result.success true; Case.AccountId equals the Account Id; Account count unchanged (AC-01.1) |
| testNoMatchCreatesUnlinkedCase | 1 staging record, NHS 9990000002, no Account | processStaging | success true; Case.AccountId null; Case.Priority 'Medium' |
| testUrgentMapsToHigh | staging record with Urgency__c 'Urgent' | processStaging | Case.Priority equals 'High' (AC-02.1) |
| testBulk200 | 200 staging records, 50 with matches | processStaging in Test.startTest/stopTest | 200 results, all success; 200 Cases; Limits.getQueries() at most 2 |
| testNullAndEmptyInput | null, then empty list | processStaging | both return empty list; no Cases exist |
| testInsertFailureReported | 1 staging record engineered to fail Case insert (Subject over 255 via 300-char Referrer_Name__c) | processStaging | success false; errorMessage not blank; staging Status__c unchanged |
| testMinimalAccessUser | user with no Case create permission (Minimum Access profile, no permission set) | System.runAs then processStaging | success false for all rows; no Cases exist |

Coverage: at least 85% on ReferralIntakeService with every branch asserted.

## Must not

- No components beyond the Files table; no new fields.
- No hardcoded Ids, record type names, or profile names.
- Do not modify `ReferralTrigger.trigger` or `ReferralTriggerHandler.cls`
  (owned by BC-04).
- No `SeeAllData=true`; no `without sharing`.

## Done when

- [ ] Deploys clean to the target sandbox
- [ ] All 7 tests pass; coverage at least 85% on the class
- [ ] PMD (R3 ruleset) reports zero findings
- [ ] Only the 4 listed files changed
