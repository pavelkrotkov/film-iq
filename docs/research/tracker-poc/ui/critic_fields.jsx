import React from "react";

export function criticScore(score) {
  return score === null || score === undefined || score === "" ? "Unknown" : score;
}

// These tracker fields carry no source or review provenance.
export function CriticFields({score, summary}) {
  return <section>
    <p>Critic score (source not recorded): {criticScore(score)}.</p>
    {summary && <p>Critic summary (source not recorded): {summary}</p>}
  </section>;
}
