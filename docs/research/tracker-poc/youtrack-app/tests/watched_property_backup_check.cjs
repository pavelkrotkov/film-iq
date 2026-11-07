/* Fictional-only full-property export/restore checks; no YouTrack calls. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const visible = {'FILMPOC-1':true,'FILMPOC-2':true,'FILMREAL-1':true};
const registry = Object.fromEntries(Object.keys(visible).map(id=>[id,{
  project:{key:id.split('-')[0]},isReported:true,isVisibleTo:()=>visible[id],fields:{'FilmIQ TMDB ID':42},
}]));
const context = {exports:{},require(name){
  assert.equal(name,'@jetbrains/youtrack-scripting-api/entities');
  return {Issue:{findById:id=>registry[id]||null}};
}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../movary.js'),'utf8'),context);
const endpoints = context.exports.httpHandler.endpoints;
const alice={login:'fictional-alice',ringId:'ring-fictional-alice',isBanned:false,extensionProperties:{filmPreferences:'unchanged'}};
const bob={login:'fictional-bob',ringId:'ring-fictional-bob',isBanned:false,extensionProperties:{filmMovarySnapshot:'bob-unchanged'}};
function call(user,method,route,input){
  const headers={};
  const ctx={currentUser:user,request:{json:()=>input,getParameter:key=>input?.[key]??null},
    response:{code:200,addHeader(name,value){headers[name]=value;},json(value){this.value=value;}}};
  endpoints.find(e=>e.method===method && e.path===route).handle(ctx);
  return JSON.parse(JSON.stringify({status:ctx.response.code,value:ctx.response.value,headers}));
}
const events={watched:true,played_watch_dates:[{date:null,plays:2}],history_export_dates:[null,'2001-01-01','2001-01-01']};
const stamp='2026-11-05T12:00:00Z';
const legacyEmpty={version:'youtrack-poc-movary-watched-v1',source:'Movary',complete:true,observed_at:stamp,films:{}};
const full={version:'youtrack-poc-movary-projects-v2',legacy_empty:legacyEmpty,projects:{
  FILMPOC:{version:'youtrack-poc-movary-watched-v3',source:'Movary',complete:true,project:'FILMPOC',observed_at:'2026-11-06T12:00:00Z',
    films:{'FILMPOC-2':{...events,tmdb_id:43}},historical:[{issue_id:'FILMPOC-1',observed_at:stamp,reason:'unbound',film:{...events,tmdb_id:null}}]},
  FILMREAL:{version:'youtrack-poc-movary-watched-v2',source:'Movary',complete:true,project:'FILMREAL',observed_at:stamp,
    films:{'FILMREAL-1':{...events,tmdb_id:42}}},
}};
// Noncanonical whitespace tests exact property-string preservation.
const original=JSON.stringify(full,null,2);
alice.extensionProperties.filmMovarySnapshot=original;
const backup=call(alice,'GET','/property-export',null);
assert.equal(backup.status,200);
assert.equal(backup.headers['Cache-Control'],'no-store');
assert.equal(backup.value.raw,original);
assert.deepEqual(backup.value.owner,{login:alice.login,ring_id:alice.ringId});
assert.equal(alice.extensionProperties.filmPreferences,'unchanged');
assert.equal(bob.extensionProperties.filmMovarySnapshot,'bob-unchanged');

const changed=JSON.stringify(full); // same data, different exact string
alice.extensionProperties.filmMovarySnapshot=changed;
assert.equal(call(alice,'POST','/property-restore',{expected:backup.value,backup:backup.value}).status,409);
assert.equal(alice.extensionProperties.filmMovarySnapshot,changed);
const current=call(alice,'GET','/property-export',null).value;
assert.equal(call(alice,'POST','/property-restore',{expected:current,backup:backup.value}).value.status,'restored');
assert.equal(alice.extensionProperties.filmMovarySnapshot,original);
assert.equal(call(alice,'POST','/property-restore',{expected:backup.value,backup:backup.value}).value.status,'unchanged');
assert.equal(bob.extensionProperties.filmMovarySnapshot,'bob-unchanged');

visible['FILMPOC-1']=false; // only historical evidence references this issue
assert.equal(call(alice,'GET','/property-export',null).status,409);
assert.equal(call(alice,'POST','/property-restore',{expected:backup.value,backup:backup.value}).status,409);
assert.equal(alice.extensionProperties.filmMovarySnapshot,original);
const realOnly={...full,projects:{FILMREAL:full.projects.FILMREAL}};
alice.extensionProperties.filmMovarySnapshot=JSON.stringify(realOnly);
const realOnlyExport=call(alice,'GET','/property-export',null).value;
assert.equal(call(alice,'POST','/property-restore',{expected:realOnlyExport,backup:backup.value}).status,409, 'hidden backup history is rejected');
assert.equal(alice.extensionProperties.filmMovarySnapshot,JSON.stringify(realOnly));
visible['FILMPOC-1']=true;
assert.equal(call(bob,'POST','/property-restore',{expected:realOnlyExport,backup:backup.value}).status,400);
assert.equal(bob.extensionProperties.filmMovarySnapshot,'bob-unchanged');

const missing={login:'fictional-missing',ringId:'ring-fictional-missing',isBanned:false,extensionProperties:{}};
const absent=call(missing,'GET','/property-export',null).value;
assert.equal(absent.raw,null);
missing.extensionProperties.filmMovarySnapshot='';
const empty=call(missing,'GET','/property-export',null).value;
assert.equal(empty.raw,'');
assert.equal(call(missing,'POST','/property-restore',{expected:empty,backup:absent}).status,200);
assert.equal(missing.extensionProperties.filmMovarySnapshot,null);
missing.extensionProperties.filmMovarySnapshot='{malformed';
assert.equal(call(missing,'GET','/property-export',null).status,500);
assert.equal(call(missing,'POST','/property-restore',{expected:absent,backup:empty}).status,409);
assert.equal(missing.extensionProperties.filmMovarySnapshot,'{malformed');
assert.equal(call({login:'guest',ringId:'guest',isBanned:false,extensionProperties:{}},'GET','/property-export',null).status,401);
console.log('Fictional full watched-property export, exact restore, visibility and owner checks passed');
