import assert from "node:assert/strict";
import { missingLinkedFilm, unavailableFilterSources } from "./availability_state.js";

const available = {preferences: {}, movary: {status: "available"}, minimum: "8", watched: "", watchlistOnly: true, sortInterest: false, movaryOnly: true};
assert.deepEqual(unavailableFilterSources(available), []);
assert.deepEqual(unavailableFilterSources({...available, preferences: null}), ["personal preferences"]);
assert.deepEqual(unavailableFilterSources({...available, movary: {status: "unknown"}}), ["Movary watched data"]);
assert.deepEqual(unavailableFilterSources({...available, preferences: null, movary: null}), ["personal preferences", "Movary watched data"]);
assert.deepEqual(unavailableFilterSources({preferences: null, movary: null}), [], "unavailable sources without active filters must not block discovery");
assert.equal(missingLinkedFilm("missing", undefined, false, false), false, "do not claim a missing film before loading");
assert.equal(missingLinkedFilm("missing", undefined, true, true), false, "do not claim a missing film during loading");
assert.equal(missingLinkedFilm("missing", undefined, true, false), true);
assert.equal(missingLinkedFilm("found", {id: "found"}, true, false), false);
console.log("Unavailable filter sources and direct-link states passed");
