import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {build} from 'esbuild';
import React from 'react';
import {renderToString} from 'react-dom/server';

const require = createRequire(import.meta.url);
const result = await build({entryPoints:['poster.jsx'],bundle:true,format:'cjs',platform:'node',external:['react'],write:false});
const module = {exports:{}};
new Function('require','module','exports',result.outputFiles[0].text)(require,module,module.exports);
const html = renderToString(React.createElement(module.exports.Poster,{transient:true,fallback:'No poster'}));
assert.match(html,/No poster/);
assert.doesNotMatch(html,/<img/);
const ordinary = renderToString(React.createElement(module.exports.Poster,{url:'https://image.tmdb.org/t/p/w500/fictional.png',alt:'Fictional'}));
assert.match(ordinary,/<img/);
assert.match(ordinary,/src="https:\/\/image\.tmdb\.org\/t\/p\/w500\/fictional\.png"/);
console.log('Missing transient poster renders a placeholder without throwing');
