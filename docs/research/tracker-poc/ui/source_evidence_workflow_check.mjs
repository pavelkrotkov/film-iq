import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {transform} from "esbuild";
import React from "react";
import {renderToStaticMarkup} from "react-dom/server";
import {tmdbId} from "./live_batch.js";
import {evidenceExplanation, evidenceLabel, sourceEvidenceLinks, sourceLabel} from "./source_evidence.js";

const compile = async (source, args) => {
  const {code} = await transform(source, {loader:"jsx", format:"cjs"});
  const module = {exports:{}};
  new Function("module", "exports", ...Object.keys(args), code)(module, module.exports, ...Object.values(args));
  return module.exports;
};
const kaneo = await readFile(new URL("./src.jsx", import.meta.url), "utf8");
const component = kaneo.slice(kaneo.indexOf("function SourceEvidence("), kaneo.indexOf("function DirectReviews("));
assert.ok(component.startsWith("function SourceEvidence("));
const {SourceEvidence} = await compile(`${component}\nmodule.exports.SourceEvidence = SourceEvidence;`, {React, tmdbId, evidenceExplanation, evidenceLabel, sourceEvidenceLinks, sourceLabel});
const fictional = {tmdb_id:42,status:"available",links:[{source_id:"Fictional source",url:"https://example.invalid/film",kind:"critic_selection"}]};
const renderKaneo = (id, evidence) => renderToStaticMarkup(React.createElement(SourceEvidence, {film:{fields:{"POC TMDB ID":id,"POC Evidence":evidence}}}));
assert.match(renderKaneo("42", JSON.stringify(fictional)), /Fictional source/);
assert.doesNotMatch(renderKaneo("43", JSON.stringify(fictional)), /Fictional source/);
assert.match(renderKaneo("43", JSON.stringify(fictional)), /Links are hidden until reviewed/);
assert.match(renderKaneo("42", "malformed"), /Source evidence unknown/);

const youtrack = await readFile(new URL("./youtrack.jsx", import.meta.url), "utf8");
const start = youtrack.indexOf("<h3>Source evidence</h3>");
const end = youtrack.indexOf("<h3>Direct reviews and aggregators</h3>", start);
assert.ok(start >= 0 && end > start);
const section = youtrack.slice(start, end);
const safeLink = (value) => value;
const ExternalLink = ({url,label}) => React.createElement("a", {href:url}, label);
const {Evidence} = await compile(`function Evidence({sourceEvidenceState}) { const sourceLinks = sourceEvidenceState.links; return <>${section}</>; } module.exports.Evidence = Evidence;`, {React, safeLink, ExternalLink});
const renderYouTrack = (id, evidence) => renderToStaticMarkup(React.createElement(Evidence, {sourceEvidenceState:sourceEvidenceLinks(evidence,id)}));
assert.match(renderYouTrack(42, fictional), /Fictional source/);
assert.doesNotMatch(renderYouTrack(43, fictional), /Fictional source/);
assert.match(renderYouTrack(43, fictional), /Links are hidden until reviewed/);
assert.match(renderYouTrack(42, {...fictional,tmdb_id:"bad"}), /Accepted source evidence unavailable/);
console.log("Fictional details hide source links when the saved film ID changes");
