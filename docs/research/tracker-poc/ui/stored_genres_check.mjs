import assert from "node:assert/strict";
import {decodeStoredGenres, encodeStoredGenres, GENRES_PREFIX, genreEdit, hasStoredGenre, storedGenreLabels, storedGenreText} from "./stored_genres.js";

assert.deepEqual(decodeStoredGenres(null), {status: "unknown", genres: []});
assert.deepEqual(decodeStoredGenres(""), {status: "unknown", genres: []});
assert.deepEqual(decodeStoredGenres("Drama"), {status: "known", genres: ["Drama"]});
assert.deepEqual(decodeStoredGenres("  Film noir  "), {status: "known", genres: ["  Film noir  "]});
assert.deepEqual(decodeStoredGenres('["Legacy literal"]'), {status: "known", genres: ['["Legacy literal"]']});

const genres = ["Drama", "Science fiction", "Comedy, dark"];
const encoded = encodeStoredGenres(genres);
assert.equal(encoded, `${GENRES_PREFIX}${JSON.stringify(genres)}`);
assert.deepEqual(decodeStoredGenres(encoded), {status: "known", genres});
assert.deepEqual(storedGenreLabels(encoded), genres);
assert.equal(storedGenreText(encoded), "Drama\nScience fiction\nComedy, dark");
assert.equal(hasStoredGenre(encoded, "Drama"), true);
assert.equal(hasStoredGenre(encoded, "dram"), false);
assert.equal(hasStoredGenre(encoded, "drama"), false);
assert.deepEqual(decodeStoredGenres(encodeStoredGenres([])), {status: "known", genres: []});
assert.equal(hasStoredGenre(null, "Drama"), false);
assert.deepEqual(genreEdit("Drama", "Drama", null), {changed:false, value:"Drama"}, "legacy scalar must not be rewritten");
assert.deepEqual(genreEdit(null, "", null), {changed:false, value:null}, "unknown must stay unknown");
assert.deepEqual(genreEdit("Drama", "Drama\nComedy, dark", null), {changed:true, value:encodeStoredGenres(["Drama", "Comedy, dark"])});
assert.deepEqual(genreEdit(encoded, "", null), {changed:true, value:null});
assert.deepEqual(genreEdit(encoded, "", ""), {changed:true, value:""});
assert.deepEqual(genreEdit(encodeStoredGenres([]), "", null), {changed:false, value:encodeStoredGenres([])}, "known-empty must not become unknown on unrelated save");
assert.deepEqual(genreEdit(encodeStoredGenres([]), "", null, true), {changed:true, value:null}, "an explicit reset turns known-empty into unknown");
assert.deepEqual(genreEdit(encodeStoredGenres([]), "", "", true), {changed:true, value:""});
assert.throws(() => genreEdit("Drama", "Drama\n\nComedy", null), /one nonblank genre/);

for (const raw of [42, "   ", "Drama\nComedy", GENRES_PREFIX, `${GENRES_PREFIX}{}`, `${GENRES_PREFIX}[1]`, `${GENRES_PREFIX}[" "]`]) {
  assert.deepEqual(decodeStoredGenres(raw), {status: "invalid", genres: []});
}
for (const bad of [null, "Drama", [""], ["Drama", 2], ["  "]]) {
  assert.throws(() => encodeStoredGenres(bad));
}
console.log("Stored genres preserve legacy labels, exact matches and unknown/empty distinctions");
