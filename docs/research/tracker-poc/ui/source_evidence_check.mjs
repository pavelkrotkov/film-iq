import assert from "node:assert/strict";
import { evidenceExplanation, evidenceLabel, sourceLabel } from "./source_evidence.js";

assert.equal(evidenceLabel("critic_selection"), "Critic selection or ballot");
assert.equal(evidenceLabel("award_outcome"), "Award outcome");
assert.equal(evidenceLabel("registry_selection"), "Registry selection");
assert.equal(evidenceLabel("unknown"), "Evidence type unknown (source label: unknown)");
assert.equal(evidenceLabel(null), "Evidence type unknown");
assert.match(evidenceExplanation([{ kind: "critic_selection" }, { kind: "award_outcome" }]), /do not establish an individual film review/);
const unknownSource = { source_id: "Synthetic publisher", kind: "unrecognized" };
assert.equal(sourceLabel(unknownSource), "Synthetic publisher");
assert.equal(evidenceLabel(unknownSource.kind), "Evidence type unknown (source label: unrecognized)");
assert.equal(evidenceLabel("<script>"), "Evidence type unknown (source label: <script>)");
assert.match(evidenceExplanation([unknownSource]), /not established/);
assert.match(evidenceExplanation([]), /not established/);
console.log("Evidence labels do not invent individual reviews");
