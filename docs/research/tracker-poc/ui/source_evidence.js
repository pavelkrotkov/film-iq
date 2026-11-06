const labels = {
  critic_selection: "Critic selection or ballot",
  award_outcome: "Award outcome",
  registry_selection: "Registry selection",
  institutional_selection: "Institutional selection",
};

// Imported evidence belongs to its original supplied ID, which can be edited.
export function sourceEvidenceLinks(evidence, currentId) {
  if (!evidence || !Number.isSafeInteger(evidence.tmdb_id) || evidence.tmdb_id <= 0 ||
      !["available", "unknown"].includes(evidence.status) || !Array.isArray(evidence.links)) {
    return {status: "unknown", links: []};
  }
  if (evidence.tmdb_id !== currentId) return {status: "mismatch", links: []};
  return {status: evidence.status, links: evidence.status === "available" ? evidence.links.filter((item) => item && typeof item === "object") : []};
}

export function evidenceLabel(kind) {
  if (Object.hasOwn(labels, kind)) return labels[kind];
  return typeof kind === "string" && kind ? `Evidence type unknown (source label: ${kind})` : "Evidence type unknown";
}

export function sourceLabel(item) {
  return item?.source_id || "Source";
}

export function evidenceExplanation(links) {
  return links.length && links.every((item) => Object.hasOwn(labels, item?.kind))
    ? "Selection and award records do not establish an individual film review. Other reviews may exist."
    : "These links identify source evidence; an individual review is not established.";
}
