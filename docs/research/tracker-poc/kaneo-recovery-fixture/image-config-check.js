// Run only inside the fictional recovery source-app container.
const assert = require('node:assert/strict');
const base = 'http://127.0.0.1:5173/api';
const cookies = new Map();
const password = process.env.FIXTURE_PASSWORD;
if (!password) throw Error('Missing fictional fixture password');

async function call(path, body, method) {
  const headers = {'Content-Type': 'application/json', Origin: 'http://localhost:25173'};
  if (cookies.size) headers.Cookie = [...cookies].map(([k, v]) => `${k}=${v}`).join('; ');
  const response = await fetch(base + path, {
    method: method || (body ? 'POST' : 'GET'), headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  for (const raw of response.headers.getSetCookie()) {
    const [pair] = raw.split(';');
    const i = pair.indexOf('=');
    cookies.set(pair.slice(0, i), pair.slice(i + 1));
  }
  return response;
}

(async () => {
  let response;
  for (let attempt = 0; attempt < 30; attempt++) {
    try { response = await call('/auth/get-session'); break; }
    catch { await new Promise(resolve => setTimeout(resolve, 1000)); }
  }
  assert.ok(response, 'fixture service did not start');
  response = await call('/auth/sign-in/email', {email: 'recovery@example.invalid', password});
  assert.equal(response.status, 200, 'fictional account login failed');
  response = await call('/workspace');
  assert.equal(response.status, 200);
  const workspace = (await response.json()).find(x => x.name === 'Fictional Recovery Workspace');
  assert.ok(workspace);
  response = await call(`/project?workspaceId=${encodeURIComponent(workspace.id)}`);
  assert.equal(response.status, 200);
  const project = (await response.json()).find(x => x.name === 'Fictional Films');
  assert.ok(project);
  response = await call(`/custom-field/project/${project.id}/values`);
  assert.equal(response.status, 200);
  const values = await response.json();
  const fixture = values.find(x => x.fieldName === 'Fixture Score' && x.value === '8');
  assert.ok(fixture, 'fictional film missing');
  response = await call(`/task/image-upload/${fixture.taskId}`, {
    filename: 'fictional.png', contentType: 'image/png', size: 1, surface: 'description',
  }, 'PUT');
  assert.equal(response.status, 503, 'expected missing image storage to be reported');
  console.log('Fictional task image upload returned HTTP 503 when storage was unconfigured.');
})().catch(error => { console.error(error.message); process.exitCode = 1; });
