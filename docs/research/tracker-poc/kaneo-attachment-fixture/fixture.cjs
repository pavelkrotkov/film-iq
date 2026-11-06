// Runs only inside a new, network-isolated fictional Kaneo container.
const assert = require('node:assert/strict');
const mode = process.argv[2];
assert.ok(['create', 'missing', 'verify'].includes(mode));
const base = 'http://127.0.0.1:5173';
const image = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aQ1wAAAAASUVORK5CYII=', 'base64');
const cookies = new Map();
let stage = 'startup';
const credentials = {name:'Fictional Attachment',email:'attachment@example.invalid',password:process.env.FIXTURE_PASSWORD};
assert.ok(credentials.password);

async function request(path, payload, method) {
  const headers = {'Content-Type':'application/json',Origin:'http://localhost:25173'};
  if (cookies.size) headers.Cookie = [...cookies].map(([key,value]) => `${key}=${value}`).join('; ');
  const response = await fetch(base + '/api' + path, {method:method || (payload ? 'POST' : 'GET'),headers,body:payload ? JSON.stringify(payload) : undefined});
  for (const raw of response.headers.getSetCookie()) {
    const [pair] = raw.split(';'); const i = pair.indexOf('='); cookies.set(pair.slice(0,i),pair.slice(i+1));
  }
  return response;
}
async function json(path, payload, method) {
  const response = await request(path,payload,method);
  if (!response.ok) throw Error(`Fictional API ${path.split('/')[1]} returned HTTP ${response.status}`);
  return response.json();
}

(async () => {
  let reachable = false;
  for (let i=0;i<60;i++) {
    try { await request('/auth/get-session'); reachable=true; break; } catch { await new Promise(resolve => setTimeout(resolve,1000)); }
  }
  assert.ok(reachable,'Fictional Kaneo did not start');
  stage='login';
  await json(mode === 'create' ? '/auth/sign-up/email' : '/auth/sign-in/email',credentials);
  let workspace,project;
  if (mode === 'create') {
    stage='create-record';
    workspace=await json('/auth/organization/create',{name:'Attachment Fixture Workspace',slug:'attachment-fixture'});
    project=await json('/project',{name:'Attachment Fixture Films',workspaceId:workspace.id,icon:'🎬',slug:'attachment-fixture'});
    const field=await json('/custom-field',{projectId:project.id,name:'Fixture Anchor',type:'number'});
    const task=await json(`/task/${project.id}`,{title:'Fictional Attachment Film',description:'Synthetic fixture',priority:'no-priority',status:'to-do'});
    await json('/custom-field/value',{taskId:task.id,fieldId:field.id,value:'8'},'PUT');
    const input={filename:'fictional.png',contentType:'image/png',size:image.length,surface:'description'};
    stage='presign';
    const upload=await json(`/task/image-upload/${task.id}`,input,'PUT');
    const target=new URL(upload.uploadUrl);
    assert.equal(target.protocol,'http:'); assert.equal(target.hostname,'garage'); assert.equal(target.port,'3900');
    stage='upload';
    const put=await fetch(target,{method:'PUT',headers:upload.headers,body:image,redirect:'error'});
    assert.ok(put.ok,`Fictional S3 upload returned HTTP ${put.status}`);
    stage='finalize';
    const asset=await json(`/task/image-upload/${task.id}/finalize`,{...input,key:upload.key});
    assert.match(new URL(asset.url).pathname,/^\/api\/asset\/[^/]+$/);
    stage='save-reference';
    await json(`/task/description/${task.id}`,{description:`![Fictional image](${asset.url})`},'PUT');
  } else {
    workspace=(await json('/workspace')).find(value => value.name === 'Attachment Fixture Workspace');
    assert.ok(workspace);
    project=(await json(`/project?workspaceId=${encodeURIComponent(workspace.id)}`)).find(value => value.name === 'Attachment Fixture Films');
    assert.ok(project);
  }
  stage='field-list';
  const fields=await json(`/custom-field/project/${project.id}`);
  const field=fields.find(value => value.name === 'Fixture Anchor' && value.type === 'number');
  assert.ok(field);
  stage='field-value';
  const values=await json(`/custom-field/project/${project.id}/values`);
  const anchor=values.filter(value => value.fieldId === field.id && value.value === '8');
  assert.equal(anchor.length,1);
  stage='task-read';
  const task=await json(`/task/${anchor[0].taskId}`);
  assert.equal(task.title,'Fictional Attachment Film');
  stage='reference-check';
  const match=/\/api\/asset\/([a-zA-Z0-9_-]+)/.exec(task.description);
  assert.ok(match,'Restored task must retain its asset reference');
  if (mode === 'missing') {
    // Prove the empty store is reachable with these credentials for both PUT
    // and GET, so the missing original is not merely a dead service.
    stage='control-presign';
    const input={filename:'control.png',contentType:'image/png',size:image.length,surface:'description'};
    const controlUpload=await json(`/task/image-upload/${task.id}`,input,'PUT');
    const target=new URL(controlUpload.uploadUrl);
    assert.equal(target.hostname,'garage'); assert.equal(target.port,'3900'); assert.equal(target.protocol,'http:');
    const put=await fetch(target,{method:'PUT',headers:controlUpload.headers,body:image,redirect:'error'});
    assert.equal(put.status,200);
    const controlAsset=await json(`/task/image-upload/${task.id}/finalize`,{...input,key:controlUpload.key});
    const controlPath=new URL(controlAsset.url).pathname;
    assert.match(controlPath,/^\/api\/asset\/[a-zA-Z0-9_-]+$/);
    const control=await request(controlPath.slice(4));
    assert.equal(control.status,200);
    assert.deepEqual(Buffer.from(await control.arrayBuffer()),image);
  }
  stage='read-asset';
  const asset=await request(`/asset/${match[1]}`);
  if (mode === 'missing') {
    assert.equal(asset.status,404,'Database-only restore must not contain object bytes');
    console.log(`Database-only negative control: asset unavailable (HTTP ${asset.status})`);
  } else {
    assert.equal(asset.status,200);
    assert.deepEqual(Buffer.from(await asset.arrayBuffer()),image);
    console.log(`${mode}: fictional task, attachment reference and exact image bytes verified`);
  }
})().catch(error => {console.error(`Fictional phase ${stage}: ${error.name}`);process.exitCode=1;});
