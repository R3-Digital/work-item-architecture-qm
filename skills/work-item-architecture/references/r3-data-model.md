# R3 Data Model (verified against the org)

Read before Step 0. Field and relationship facts for the R3 delivery org.

**`Work_Item__c`**: `Name` (WI number), `Subject__c`, `Description__c`,
`User_Story__c` (long text), `Deliverables__c`, `Implementation__c`,
`Assumptions__c`, `Status__c`, `Type__c`, `Project__c`, `Feature__c`,
`Related_Work_Item__c` (self-lookup). The `Acceptance_Criteria__c` **field**
(long text) is legacy.

**Acceptance criteria live in the `Acceptance_Criteria__c` field** (long text,
32k) on the work item, for now. An `Acceptance_Criteria__c` child object
exists (Scenario / Given / When / Then at 255 chars each, Status, via
`Acceptance_Criteria__r`), but creating records requires a `User_Story__c`
parent, which is more overhead than the team wants today. The field is the
working store until that changes; when it does, only section 9 of
`references/templates.md` and this paragraph need editing. If child records
exist on a work item, read them as source material at Step 0; never create
them.

**`Work_Item_Context__c`** is the knowledge layer. Fields: `Summary__c`
(255, required), `Context__c` (131k long text), `Context_Type__c` (required:
Technical Context / Implementation Notes / Root Cause Analysis / Client
Clarifications / Testing Context), `Confidence__c` (Verified / Likely /
Unverified), `Source_Type__c` (includes AI Generated), `Source_URL__c`,
`Status__c` (Current / Stale / Draft). Read via `Work_Item_Contexts__r`.

**`Work_Item_Dependency__c`**: `Blocker_Work_Item__c` and
`Blocked_Work_Item__c` (both required), `Dependency_Type__c` (Hard / Soft),
`Status__c`, `Description__c`.

Verify with a describe if anything errors; orgs drift.
