// Fresh API-only authentication inside the isolated fictional fixture container.
const readline = require('node:readline');
const base = 'http://127.0.0.1:5173/api';
const password = process.env.FIXTURE_PASSWORD;
if (!password) throw Error('Missing fictional fixture password');
const cookie = new Map();
async function call(path, body, method) {
  const headers = {'Content-Type': 'application/json', Origin: 'http://localhost:25173'};
  if (cookie.size) headers.Cookie = [...cookie].map(([k, v]) => `${k}=${v}`).join('; ');
  const response = await fetch(base + path, {method: method || (body ? 'POST' : 'GET'), headers, body: body ? JSON.stringify(body) : undefined});
  for (const raw of response.headers.getSetCookie()) {
    const [pair] = raw.split(';'); const i = pair.indexOf('=');
    cookie.set(pair.slice(0, i), pair.slice(i + 1));
  }
  if (!response.ok) throw Error(`Fixture API status ${response.status}`);
  return await response.json();
}
(async () => {
  let ready = false;
  for (let attempt = 0; attempt < 30; attempt++) {
    try { await call('/auth/get-session'); ready = true; break; }
    catch { await new Promise(resolve => setTimeout(resolve, 1000)); }
  }
  if (!ready) throw Error('Fictional API unavailable');
  await call('/auth/sign-in/email', {email: 'recovery@example.invalid', password});
  process.stdout.write('{"ready":true}\n');
  const lines = readline.createInterface({input: process.stdin, crlfDelay: Infinity});
  for await (const line of lines) {
    try {
      const {path, body, method} = JSON.parse(line);
      if (typeof path !== 'string' || !path.startsWith('/') || path.includes('..') || path.includes('://')) throw Error('Invalid fixture path');
      const data = await call(path, body, method);
      process.stdout.write(JSON.stringify({ok:true, data}) + '\n');
    } catch (_) { process.stdout.write('{"ok":false}\n'); }
  }
})().catch(() => { process.stderr.write('Fictional API client failed\n'); process.exitCode = 1; });
