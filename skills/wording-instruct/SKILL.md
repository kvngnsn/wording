---
name: wording-instruct
description: >-
  Write how-to guides, tutorials, procedures, and onboarding steps. Use when a reader must complete an action correctly, with verified steps and relevant conditions.
---

# Help the reader complete the task

Write a procedure someone in the intended starting state can follow without guessing. Keep the user's requested format and level of expertise. Drafting instructions does not authorize executing their actions or changing external systems.

## Establish the starting state

Identify the desired result, necessary access or materials, relevant version or environment, and what the reader is assumed to have done already. Include prerequisites only when they affect execution. Ask about a missing detail if different answers would produce incompatible or unsafe steps; otherwise use the known path and state a limited assumption when necessary.

Use verified controls, commands, filenames, and conditions. Inspect documentation or the relevant environment when tools are available and the task calls for it. Without that access, rely on supplied steps and identify missing instructions instead of inventing a plausible interface. Do not say a procedure was tested unless it was actually run in the stated environment.

## Write the usable sequence

Give the result or purpose briefly, then order actions by their real dependencies. Put the location or necessary context before the action: “In Export, choose CSV.” Generally use one meaningful action per numbered step; combine short menu selections when they form one natural action. A single action can be one sentence.

Name exact controls when known. Explain placeholders before the reader needs to replace them. Put a consequence or warning immediately before the action it affects, especially where an overwrite, charge, submission, or deletion can occur. Distinguish required, optional, and conditional actions without treating every step as a hazard.

Provide a useful observable check where it prevents uncertainty: a saved file's location, an expected status, or the result of a command. Distinguish an expected result from a verified test result. If the process branches, state the condition and next action clearly. Include common recovery steps only when supported and relevant; do not speculate about nonexistent error messages.

Prefer one reliable path over a catalogue of alternatives. Add another method when it materially serves accessibility, a different environment, or the user's request. Use familiar language while preserving technical accuracy. Keep explanatory background beside the point where it helps, rather than burying the actions in a conceptual essay.

## Examples

Vague: “Navigate to the appropriate export functionality and proceed accordingly.”

Usable, given the interface: “Open File > Export. Choose CSV, then select the destination folder.”

Late warning: “Choose Save. Reusing the filename may overwrite the existing copy.”

Timely warning: “To keep the existing copy, enter a new filename before choosing Save.”

## Walk through the wording

Mentally follow the procedure from the stated starting state. Make one targeted revision for the first missing dependency, ambiguous action, misplaced warning, or uncertain result. Check that the reader knows where to begin and how to recognize completion. Return the guide; disclose unverified steps or blocking gaps briefly without claiming to have performed the task.
