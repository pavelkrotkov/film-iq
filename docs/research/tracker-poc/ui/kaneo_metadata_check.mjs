import assert from "node:assert/strict";
import {metadataChanges, storedMetadata} from "./kaneo_metadata.js";

const fields = [
  {id: "year", name: "POC Year", type: "number"},
  {id: "genre", name: "POC Genre", type: "text"},
  {id: "source", name: "POC Source Year", type: "number"},
];
const rows = [{fieldId: "year", value: "2001"}, {fieldId: "genre", value: "Drama"}, {fieldId: "source", value: "1999"}];
const baseline = storedMetadata(fields, rows);
const both = {year:true, genre:true};
assert.deepEqual(metadataChanges(baseline, {year: "2001", genre: "Drama"}, both), []);
assert.deepEqual(metadataChanges(baseline, {year: "", genre: ""}, both), [
  {fieldId: "year", value: "", name: "POC Year"},
  {fieldId: "genre", value: "", name: "POC Genre"},
]);
assert.deepEqual(metadataChanges(storedMetadata(fields, []), {year: " 2002 ", genre: "Comedy"}, both), [
  {fieldId: "year", value: "2002", name: "POC Year"},
  {fieldId: "genre", value: "Comedy", name: "POC Genre"},
]);
assert.throws(() => metadataChanges(baseline, {year: "10000", genre: "Drama"}, both), /Release year/);
assert.throws(() => metadataChanges(baseline, {year: "2001", genre: "  "}, both), /Genre/);
const refreshed = storedMetadata(fields, [{fieldId: "year", value: "2003"}, {fieldId: "genre", value: "Comedy"}]);
assert.deepEqual(metadataChanges(refreshed, {year: "2001", genre: "Drama"}, {year:false, genre:false}), [], "unrelated synopsis edits must not overwrite refreshed metadata");
assert.deepEqual(metadataChanges(refreshed, {year: "", genre: "Drama"}, {year:true, genre:false}), [{fieldId: "year", value: "", name: "POC Year"}], "an explicit clear updates only the touched field");
assert.equal(storedMetadata([], rows).year.editable, false);
assert.throws(() => metadataChanges(storedMetadata([], rows), {year:"2002", genre:"Drama"}, {year:true, genre:false}), /POC Year is unavailable/);
assert.deepEqual(metadataChanges(storedMetadata([], rows), {year:"2002", genre:"Drama"}, {year:false, genre:false}), []);
assert.equal(storedMetadata([...fields, fields[0]], rows).year.editable, false);
assert.equal(storedMetadata(fields, [...rows, rows[0]]).year.editable, false);
assert.equal(storedMetadata(fields, [{fieldId: "year", value: "bad"}]).year.editable, false);
assert.equal(storedMetadata([{...fields[0], type: "text"}], []).year.editable, false);
console.log("Kaneo stored metadata edits, clears and source-field preservation passed");
