import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {transform} from "esbuild";
import React from "react";
import {renderToStaticMarkup} from "react-dom/server";
import {filterFilms} from "./film_filters.js";
import {field, filterYoutrackFilms} from "./youtrack_filters.js";
import {encodeStoredGenres, liveGenreOnlyMatch, storedGenreDisplay} from "./stored_genres.js";

const values = ["Drama", encodeStoredGenres(["Drama", "Comedy, dark"]), "filmiq-genres-v1:broken", null, encodeStoredGenres([])];
const kaneo = values.map((value, id) => ({id:String(id), title:`Fictional ${id}`, status:"to-do", fields:{"POC Genre":value}}));
const youtrack = values.map((value, id) => ({id:String(id), idReadable:`FILMPOC-${id + 1}`, summary:`Fictional ${id}`, customFields:[{name:"FilmIQ Genre", value}]}));
const filterK = (genre) => filterFilms(kaneo, {query:"", genre}).map((film) => film.id);
const filterY = (genre) => filterYoutrackFilms(youtrack, {query:"", genre}).map((film) => film.id);
assert.deepEqual(filterK("Drama"), ["0", "1"]);
assert.deepEqual(filterY("Drama"), ["0", "1"]);
assert.deepEqual(filterK("Comedy, dark"), ["1"]);
assert.deepEqual(filterY("Comedy, dark"), ["1"]);
assert.deepEqual(filterK("Comedy"), [], "genre matching must not use substrings");
assert.deepEqual(filterY("comedy, dark"), [], "genre matching must not change case");
assert.equal(storedGenreDisplay(null), null);
assert.equal(storedGenreDisplay(encodeStoredGenres([])), "No stored genres");
assert.equal(storedGenreDisplay("filmiq-genres-v1:broken"), "Stored genres invalid");
for (const stored of ["Drama", null, encodeStoredGenres([]), "filmiq-genres-v1:broken"]) {
  const source = {genres:["Comedy"]};
  const k = {...kaneo[0],fields:{"POC Genre":stored},live:source};
  const y = {...youtrack[0],customFields:[{name:"FilmIQ Genre",value:stored}],live:source};
  assert.equal(filterFilms([k],{query:"",genre:"Comedy"}).length,1);
  assert.equal(filterYoutrackFilms([y],{query:"",genre:"Comedy"}).length,1);
  assert.equal(liveGenreOnlyMatch(stored,source.genres,"Comedy"),true);
}
assert.equal(liveGenreOnlyMatch("Comedy",["Comedy"],"Comedy"),false,"stored match needs no source-only explanation");
assert.equal(liveGenreOnlyMatch(null,null,"Comedy"),false,"missing live metadata remains unknown");
assert.equal(liveGenreOnlyMatch(null,["Comedy",null],"Comedy"),false,"malformed live metadata is not represented as evidence");
assert.equal(liveGenreOnlyMatch(null,"Comedy","Comedy"),false);
assert.equal(liveGenreOnlyMatch(null,["Comedy"],""),false);

// Render the actual two card expressions, not a separate example component.
for (const name of ["src.jsx","youtrack.jsx"]) {
  const source = readFileSync(new URL(name,import.meta.url),"utf8");
  const line = source.split("\n").find((value) => value.includes("liveGenreOnlyMatch(") && value.includes("genre match:"));
  assert.ok(line,`${name} must explain live-only matches`);
  const {code} = await transform(`function Card({item,genre,cacheFixture}) { const metadata=item.live; return <>${line.trim()}</>; } module.exports=Card;`,{loader:"jsx",format:"cjs"});
  const module={exports:{}};
  new Function("module","exports","React","field","liveGenreOnlyMatch",code)(module,module.exports,React,field,liveGenreOnlyMatch);
  const item = name === "src.jsx" ? {...kaneo[0],live:{genres:["Comedy"]}} : {...youtrack[0],live:{genres:["Comedy"]}};
  const render = (props) => renderToStaticMarkup(React.createElement(module.exports,{item,genre:"Comedy",...props}));
  assert.match(render({cacheFixture:false}),/TMDB genre match: Comedy/);
  assert.match(render({cacheFixture:true}),/Fictional cache genre match: Comedy/);
  assert.doesNotMatch(render({genre:"Drama"}),/genre match:/);
  assert.doesNotMatch(render({item:{...item,live:null}}),/genre match:/);
}
console.log("Both tracker filters match stored genres exactly and preserve unknown states");
