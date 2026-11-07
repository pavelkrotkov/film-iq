import React from "react";
import {reviewDirectorNames} from "./direct_reviews.js";

// The matching review field is already stored on the tracker record.
export function ReviewDirectorEvidence({raw, filmId, title, query}) {
  const names = reviewDirectorNames(raw, filmId, title);
  if (!names.length || (query && !names.some((name) => name.toLowerCase().includes(query.toLowerCase())))) return null;
  return <small>Director names in review identity evidence: {names.join(", ")}. Film identity not independently verified; sources may disagree.</small>;
}
