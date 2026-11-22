# LA-01 · Publish a source-verified legal research brief

**Owner** · Pending confirmation · [Task checklist](checklist.json) · [Delivery guide](https://github.com/aispanda/Reusable-Delivery/blob/082e01d50eb65f518b1b4e3415584af57b08faaa/new/START.md)

**Outcome** · As a legal researcher, I want to turn a focused legal question into a source-verified brief so that a reader can check the authorities and see where the evidence is incomplete.

**Scope** · One research question, one defined jurisdiction and cutoff date, a brief with citations, and an evidence record for review. Each project chooses its own sources, tools, and publication destination. Keep private records and review evidence in authorized storage.

**Operations** · Start from an agreed question. Gather and verify the relevant authorities, record gaps, have a separate reviewer check the brief against the sources, and publish the approved version. Reopen affected checks if a source or material claim changes before publication.

**Acceptance** · Pending decision by the project owner. All criteria start as proposed defaults for the adopter to confirm. All scenario runs start as NOT RUN. Record actual review, acceptance, and release decisions separately.

## Requirements and verification

[Acceptance criteria and verification scenarios](scenarios.json) cover citation traceability, evidence gaps, and safe and accurate publication. Use the [private results schema](https://github.com/aispanda/Reusable-Delivery/blob/082e01d50eb65f518b1b4e3415584af57b08faaa/templates/results.schema.json) to record observations against the tested revision. Record a builder and a different tester. Keep real case material and evidence in restricted storage.

## Quick start

1. Copy this folder into your workspace. Replace the story ID if needed and confirm the owner, question, jurisdiction, cutoff date, audience, and allowed sources in your own copy. Use a restricted record for non-public details.
2. Confirm the scenario wording and the publication destination. Assign one executor per task. Start with LA-01.1 and follow the checklist dependencies. Record the evidence behind each task result and identify the next eligible task.
3. Use the [research brief](../../templates/research-brief.md) and [evidence packet](../../templates/evidence-packet.md) if you copied the full Legal-AI repository. If you copied this folder alone, capture the question, jurisdiction, cutoff date, reader, source scope, claim, source citation, pinpoint, verification status, and outstanding gaps in your own notes.
4. Publish the approved brief only after independent verification and the owner's release decision. Read it back as the intended reader and confirm its version and citations.

**Next** · LA-01.1. The project owner confirms the scope and names the researcher and independent reviewer.

## Execution notes for adopters

- **Route** · NEW for each new research assignment. Check for an existing story before creating one.
- **Guide revision** · Use the pinned guide above. The starter draws on the agreement, privacy, story, execution, states, platform, automation, review, and publication modules at that revision, plus the scenario and checklist definitions.
- **Automation decision** · Pending with the adopting project owner. Revisit after manual verification and before any batch implementation. The starter requires no implementation.
