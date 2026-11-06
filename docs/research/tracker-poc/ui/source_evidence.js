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

// A source field is not a verified release year or proof that its value is unchanged.
export function sourceYearLabel(rawEvidence, currentId, year) {
  if (typeof year !== "string" || !/^[1-9][0-9]{3}$/.test(year) || Number(year) < 1800 || Number(year) > 2200) return null;
  try {
    const evidence = JSON.parse(rawEvidence);
    const {status, links} = sourceEvidenceLinks(evidence, currentId);
    const validLink = (link) => {
      if (![link.entry_id, link.revision_id].every((value) => typeof value === "string" && value.trim())) return false;
      const url = new URL(link.url);
      return ["http:", "https:"].includes(url.protocol) && !url.username && !url.password;
    };
    return status === "available" && links.length && links.length === evidence.links.length && links.every(validLink)
      ? `Source-listed year ${year} (source field; verify identity and edits)`
      : null;
  } catch { return null; }
}

export function kaneoCardYear(film, currentId) {
  return film.fields["POC Year"] || film.live?.year ||
    sourceYearLabel(film.fields["POC Evidence"], currentId, film.fields["POC Source Year"]) || "UNKNOWN YEAR";
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
