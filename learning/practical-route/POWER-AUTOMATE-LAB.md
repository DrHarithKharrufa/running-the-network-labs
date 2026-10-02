# Build the same review outcome in Microsoft Power Automate

Edition RTN-2026-10-03. This is a complete **cloud-flow construction and acceptance guide**, not a tenant export or a claim of cloud execution. The author package includes no tenant, connection or approval-recipient credentials. Use a development environment and your own test account as the approval recipient. The manual-trigger route below uses synthetic monitoring and device observations; moving to a live monitor is a separate acceptance step.

The outcome is the same as the n8n route: a validated event, an owned asset, preserved evidence, one durable case identity and an explicit human decision. The mechanisms differ. Here SharePoint holds the teaching journal and Approvals supplies the human decision. The exercise does not change a device, send a security containment command or prove incident recovery.

## Prerequisites and ownership

You need a Power Automate cloud-flow entitlement, permission to create a flow in the selected environment, a SharePoint development site where you can create lists, and access to the SharePoint and Approvals connectors under your organisation's data policies. Confirm the actual connector classification and entitlement in your tenant. Microsoft 365 ownership does not imply entitlement to every HTTP connector, custom connector or AI Builder feature. Approvals also depends on the environment's supported Dataverse/approval setup; ask the environment administrator to establish it if the action cannot initialise.

Record the environment ID, flow owner, co-owner/recovery owner, SharePoint site/list IDs, connection owners, policy restrictions and the date tested. Use test data. Do not put passwords in Compose actions or export files. For production, replace personal lifecycle dependencies with your organisation's supported service ownership and connection model.

## Create two lists with these internal column names

Create the columns using the exact names first, before changing display labels. Use the default `Title` column as the human-readable label.

**RTNAssets**:

| Column | Type / initial row |
| --- | --- |
| SensorKey | Single line of text; enforce unique values; `sensor-r1-eth2` |
| AssetId | Single line; `r1` |
| InterfaceId | Single line; `eth2` |
| OwnerUPN | Single line; your own tenant test account |
| OperState | Choice `up`, `down`, `unknown`; set `down` |
| EvidenceRevision | Number, zero decimal places; `1` |
| EvidenceScope | Single line; `synthetic SharePoint fixture` |

**RTNCases**:

| Column | Type |
| --- | --- |
| EventKey | Single line; **enforce unique values** |
| Fingerprint | Multiple lines, plain text |
| SensorKey, AssetId, InterfaceId, OwnerUPN | Single line each |
| EventStatus | Choice `Down`, `Up` |
| EventSequence | Number, zero decimal places |
| ObservedUTC | Date/time |
| State | Choice `RECEIVED`, `AWAITING_REVIEW`, `REVIEWED`, `DISMISSED`, `FAILED`, `STALE` |
| Evidence, Summary, DecisionNote | Multiple lines, plain text |
| ApprovalId | Single line |
| DecidedUTC | Date/time |

The single-line columns have SharePoint limits. The event schema below limits identifiers to 64 characters. Keep execution data bounded; do not put raw packet captures, secrets or unbounded configurations into a list item.

## Construct the flow in this order

Create an **Instant cloud flow**, trigger **Manually trigger a flow**, with one Text input named **Event JSON**. In trigger settings enable concurrency control with degree **1** for this teaching flow. This serialises this flow's admissions; the unique EventKey also protects against duplicate list creation. It does not create a transaction across SharePoint and Approvals.

Use the action names below before entering expressions, because expression references depend on them. Expressions shown omit the designer's outer `@`; enter them in its Expression editor. Dynamic-content selections avoid guessing generated trigger input names.

1. **Parse event** — Data Operations → Parse JSON. Content: select the trigger's **Event JSON** token. Schema: paste `workflows/event-schema.json`. The allowed sensor is deliberately one fixture. The contract needs five fields: `event_id`, `sensor_id`, `status`, `observed_at` (Unix seconds), `sequence` (nonnegative integer).
2. **Event** — Compose with `body('Parse_event')`. All later expressions refer to this normalised object. Add a Condition that checks identifier lengths 1–64, sensor equals `sensor-r1-eth2`, status is Down or Up, sequence is nonnegative and at most 9007199254740991, and observation is not more than 30 seconds in the future. Do not rely solely on every JSON Schema keyword being enforced identically by every connector/runtime. For a timestamp, Compose **Observed UTC** with `addSeconds('1970-01-01T00:00:00Z', int(outputs('Event')?['observed_at']))`; failure goes to the validation-failure branch. Compare `ticks(outputs('Observed_UTC'))` with `ticks(addSeconds(utcNow(),30))`.
3. **Event key** — Compose: `concat('manual:', outputs('Event')?['event_id'])`. This prefix identifies the authenticated manual test source. A live receiver must derive the source identity from authenticated context, not an event-supplied producer label.
4. **Fingerprint** — Compose: `string(createArray(outputs('Event')?['event_id'], outputs('Event')?['sensor_id'], outputs('Event')?['status'], outputs('Event')?['observed_at'], outputs('Event')?['sequence']))`. This is a canonical comparison string for these typed values, **not a cryptographic hash**. Do not call it a signature.
5. **Find existing case** — SharePoint Get items, RTNCases. Filter Query expression: `concat('EventKey eq ', decodeUriComponent('%27'), replace(outputs('Event_key'), decodeUriComponent('%27'), decodeUriComponent('%27%27')), decodeUriComponent('%27'))`. Top Count 2. The quote escaping is required even for a teaching ID. If more than one row returns, stop and investigate the uniqueness setting.
6. **Duplicate condition** — If `length(body('Find_existing_case')?['value'])` equals 1, compare the stored Fingerprint to `outputs('Fingerprint')`. Equal: finish with that item's ID and current State; do not create another approval. Unequal: terminate Failed with “event ID reused with different content”. A duplicate of a FAILED or RECEIVED case is a request for investigation/resumption, not an automatic new effect.
7. **Age and ordering** — For a new ID, get RTNCases for this exact SensorKey with `State ne 'STALE'`, ordering `EventSequence desc`, Top Count 1. Escape the SensorKey as above. If the new observation is older than five minutes, or sequence is no greater than the highest admitted sequence, create a STALE row with no approval and terminate successfully as “stale observation recorded”. Excluding STALE rows prevents an old event with an unusually large sequence from blocking later valid events. An empty result has no prior admitted sequence. Treat a future observation as invalid. The single-flow concurrency setting protects this comparison only while all writers obey it; do not add another writer without a stronger concurrency design.
8. **Create case** — For a fresh event, create one RTNCases row: Title `Network review: r1 eth2`; EventKey, Fingerprint, SensorKey, EventStatus, EventSequence, ObservedUTC from the preceding actions; State `RECEIVED`. Retain its numeric **ID** in all later updates. If a unique-key conflict occurs, re-read the existing row and compare Fingerprint; do not disable uniqueness. If the create response is lost, reconcile by EventKey before retrying.
9. **Find asset** — Get items from RTNAssets with the exact SensorKey filter, Top Count 2. Require exactly one row and a nonempty OwnerUPN. Update the case's owner/asset/interface fields from this trusted fixture. Do not accept these fields from the alert. Compose **Evidence** as an object containing AssetId, InterfaceId, OperState, EvidenceRevision, `collected_at: utcNow()`, and EvidenceScope. This is fixture evidence; the word “collected” does not turn it into a live device observation.
10. **Build deterministic summary** — Compose text combining the event's reported state with the fixture's OperState and “Cause is not established. Compare peer state and recent authorised changes.” Update the case: Evidence as the string form of the evidence object, Summary, State `AWAITING_REVIEW`. Read the item back and verify its EventKey/State before requesting review.
11. **Request review** — Approvals → **Start and wait for an approval**, type **Approve/Reject – First to respond**. Title includes the case ID. Assigned to: the trusted OwnerUPN from Find asset; for this exercise that is your own test account. Details include the event, actual evidence scope, summary and link to the SharePoint item. State explicitly: **Approve means continue investigation; Reject means dismiss this review request. Neither authorises a device change.** Set a bounded timeout (for example `PT1H` for a lab). Choose connector retry settings deliberately and retain the approval ID when available.
12. **Decision condition** — If the returned Outcome is `Approve`, update State to `REVIEWED`; if `Reject`, update to `DISMISSED`. Store the connector-returned responder identity, response time and comments in DecisionNote and DecidedUTC. Read the case back. Do not use an identity supplied in the original event as the reviewer. Timeout or connector failure leaves the case awaiting review or marks a separate failed review state; it must not imply approval.

The combined Start-and-wait action has an important recovery limit: if execution is lost around approval creation, the case may be waiting while the approval exists. Inspect the run and approval centre before creating another. A more advanced design separates Create approval from Wait for approval, persists the returned ApprovalId, and resumes by that ID; it still needs reconciliation if creation succeeds but the ID write fails. Do not advertise exactly-once approval delivery.

## Failure paths and optional AI

Group validation, case creation/enrichment and approval into separate **Scope** actions. For each scope, add a failure scope using **Configure run after** for failed/timed-out/skipped states where appropriate. Before a case exists, record the run ID and validation reason in the run history or an approved failure journal. After creation, update that exact item to `FAILED` with the stage and a redacted error reference; if the journal write itself fails, the flow must remain failed and the operator must inspect run history. Do not include tokens or full connector response bodies in the list.

For a bounded AI exercise, insert an **AI Builder prompt** after deterministic evidence creation and before review, using only the synthetic Evidence object. Ask for a possible explanation, one next check and the supplied evidence identifier. Add a 600-character output limit at the receiving step and a human-review label; retain the deterministic summary if the connector times out, lacks capacity or returns unusable text. Check AI Builder entitlement/capacity and the environment's data policy first. An accepted schema or evidence ID does not establish the explanation's truth. Give the prompt no device action or approval authority.

## Acceptance transcript to complete in your tenant

Create a new current event with a unique ID and sequence. Generate its JSON locally using the course's example; paste it into the trigger. Retain the flow run URL/ID and redacted case row for every step.

| Test | Required observation |
| --- | --- |
| Down event | Exactly one case with mapped owner and explicit synthetic evidence; approval assigned to your test account. |
| Approve | Case becomes REVIEWED, connector-returned responder and time stored. No device action. |
| Duplicate after completion | Original item and state reused; no second approval. |
| Same ID, different status | Failed conflict; original evidence and decision unchanged. |
| New Up event | New observation; does not silently rewrite the earlier decision. |
| Unknown sensor / missing owner | Stop before review; no guessed target or recipient. |
| Old or out-of-order event | STALE record without approval. |
| SharePoint unavailable or denied | Flow fails visibly; no claimed durable case. |
| Approval timeout / Reject | No approval inferred from timeout; Reject records DISMISSED. |
| Optional AI unavailable | Deterministic evidence still reaches review. |
| Interrupted run | Inspect case State and approval history; resume deliberately without duplicating approval. |

Export your tested flow as a solution with connection references where your environment supports it. Document the actual internal column names, schema, environment variables and connection mapping. Redact tenant identifiers in public examples and export no secrets. This package supplies a **construction blueprint**, not a prevalidated tenant-specific solution ZIP; an importable export must come from the environment in which these connectors were actually accepted.

## Replace the manual source

For live monitoring, choose an authenticated **When an HTTP request is received** trigger or an approved connector/queue integration, confirm its licence and set caller restrictions. Microsoft's HTTP-trigger OAuth support and rollout vary by cloud/environment; verify availability in your tenant. Retain source identity and a stable source event ID. Replace RTNAssets' simulated observation with a qualified read-only evidence service or supported connector. A cloud flow cannot reach the course's loopback server directly; do not expose that server to the Internet as a shortcut. Use an approved gateway/custom connector/service boundary with authenticated HTTPS, permissions and operational ownership, then repeat the failure tests with the actual PRTG or other monitor.

Primary references checked 26 September 2026: [cloud flow types](https://learn.microsoft.com/en-us/power-automate/flow-types), [approvals](https://learn.microsoft.com/en-us/power-automate/get-started-approvals), [HTTP-trigger OAuth](https://learn.microsoft.com/en-us/power-automate/oauth-authentication), [AI Builder](https://learn.microsoft.com/en-us/power-automate/use-ai-builder), [licensing FAQ](https://learn.microsoft.com/en-us/power-platform/admin/power-automate-licensing/faqs), [SharePoint connector](https://learn.microsoft.com/en-us/connectors/sharepointonline/). Record the designer/connector behaviour actually observed; screenshots or a plan alone are not acceptance evidence.
