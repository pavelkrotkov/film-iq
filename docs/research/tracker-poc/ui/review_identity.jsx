import React from "react";

// The caller validates the source evidence before it reaches this component.
export function ReviewIdentity({ evidence }) {
  return <>
    <p>Page title: {evidence.source_page_title}; source title: {evidence.input_title}; directors: {evidence.source_directors.join(", ")}.</p>
    {typeof evidence.source_year === "number" ? <p>Source-listed year: {evidence.source_year}.</p> : <p>Source year unknown.</p>}
    <p>{evidence.identity_caveat} {evidence.details_note}</p>
  </>;
}
