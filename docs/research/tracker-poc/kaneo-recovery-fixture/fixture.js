const assert = require('node:assert/strict');
const mode = process.argv[2];
const base = 'http://127.0.0.1:5173';
const headers = {'Content-Type':'application/json', Origin:'http://localhost:' + (mode === 'create' ? 25173 : 25174)};
const fixturePassword = process.env.FIXTURE_PASSWORD;
if (!fixturePassword) throw Error('Missing fictional fixture password');
const credentials = {name:'Fictional Recovery', email:'recovery@example.invalid', password:fixturePassword};
const cookies = new Map();
async function call(path, payload, method) {
  const h = {...headers};
  if (cookies.size) h.Cookie = [...cookies].map(([k,v]) => `${k}=${v}`).join('; ');
  const response = await fetch(base + '/api' + path, {method:method || (payload ? 'POST' : 'GET'), headers:h, body:payload ? JSON.stringify(payload) : undefined});
  for (const raw of response.headers.getSetCookie()) { const [pair] = raw.split(';'); const i = pair.indexOf('='); cookies.set(pair.slice(0,i), pair.slice(i+1)); }
  if (!response.ok) throw Error(`Fixture API failed: ${path.split('/')[1]} HTTP ${response.status}`);
  return await response.json();
}
(async () => {
  await call(mode === 'create' ? '/auth/sign-up/email' : '/auth/sign-in/email', credentials);
  let workspace, project;
  if (mode === 'create') {
    workspace = await call('/auth/organization/create', {name:'Fictional Recovery Workspace',slug:'fictional-recovery'});
    project = await call('/project', {name:'Fictional Films',workspaceId:workspace.id,icon:'🎬',slug:'fictional-films'});
    const field = await call('/custom-field',{projectId:project.id,name:'Fixture Score',type:'number'});
    const task = await call(`/task/${project.id}`, {title:'Fictional Recovery Film',description:'Synthetic recovery synopsis',priority:'no-priority',status:'to-do'});
    await call(`/task/status/${task.id}`,{status:'in-progress'},'PUT');
    await call('/custom-field/value',{taskId:task.id,fieldId:field.id,value:'8'},'PUT');
    await call(`/comment/${task.id}`,{content:'Synthetic recovery comment'});
  } else {
    workspace = (await call('/workspace')).find(x => x.name === 'Fictional Recovery Workspace');
    assert.ok(workspace, 'fictional workspace missing after restore');
    project = (await call(`/project?workspaceId=${encodeURIComponent(workspace.id)}`)).find(x => x.name === 'Fictional Films');
    assert.ok(project, 'fictional project missing after restore');
  }
  const fields = await call(`/custom-field/project/${project.id}`);
  const field = fields.find(x => x.name === 'Fixture Score' && x.type === 'number');
  assert.ok(field, 'synthetic field missing');
  const values = await call(`/custom-field/project/${project.id}/values`);
  const matches = values.filter(x => x.fieldId === field.id && x.value === '8');
  assert.equal(matches.length, 1, 'expected exactly one synthetic value');
  const task = await call(`/task/${matches[0].taskId}`);
  assert.equal(task.title, 'Fictional Recovery Film');
  assert.equal(task.description, 'Synthetic recovery synopsis');
  assert.equal(task.status, 'in-progress');
  assert.ok((await call(`/comment/${task.id}`)).some(x => x.content === 'Synthetic recovery comment'));
  console.log(`${mode}: fictional user, workspace, project, film, lifecycle, numeric field and comment verified`);
})().catch(error => {console.error(error.message); process.exitCode = 1;});
