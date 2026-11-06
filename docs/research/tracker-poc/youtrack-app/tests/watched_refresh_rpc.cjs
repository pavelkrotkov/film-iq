/* Offline line-protocol harness for the actual YouTrack handler, no network. */
const fs = require('node:fs');
const path = require('node:path');
const readline = require('node:readline');
const vm = require('node:vm');

const users = {login:'admin', isBanned:false, extensionProperties:{}};
const events = day => ({watched:true,played_watch_dates:[{date:day,plays:2}],history_export_dates:[]});
const original = {version:'youtrack-poc-movary-watched-v2',source:'Movary',complete:true,
  observed_at:'2026-11-05T12:00:00+00:00',project:'FILMREAL',films:{
    'FILMREAL-1':{...events('2001-01-01'),tmdb_id:null},
    'FILMREAL-2':{...events('2001-01-02'),tmdb_id:202},
  }};
users.extensionProperties.filmMovarySnapshot = JSON.stringify({version:'youtrack-poc-movary-projects-v2',projects:{FILMREAL:original},legacy_empty:null});
let hidden = false;
const registry = Object.fromEntries([[1,101],[2,202]].map(([n,id])=>[`FILMREAL-${n}`,{
  project:{key:'FILMREAL'},fields:{'FilmIQ TMDB ID':id},isReported:true,isVisibleTo:()=>!(hidden && n===1),
}]));
const context = {exports:{},require(name){
  if(name !== '@jetbrains/youtrack-scripting-api/entities') throw Error('Unexpected import');
  return {Issue:{findById(id){return registry[id] || null;}}};
}};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../movary.js'),'utf8'),context);
const endpoints = context.exports.httpHandler.endpoints;
const lines = readline.createInterface({input:process.stdin,crlfDelay:Infinity});
(async()=>{
  for await (const line of lines) {
    try {
      const message=JSON.parse(line);
      if(message.action==='hidden') { hidden=message.value===true; process.stdout.write('{"ok":true}\n'); continue; }
      if(message.action==='raw') { process.stdout.write(JSON.stringify({raw:users.extensionProperties.filmMovarySnapshot})+'\n'); continue; }
      const ctx={currentUser:users,request:{json:()=>message.body,getParameter:key=>message.query?.[key]??null},
        response:{code:200,json(value){this.value=value;}}};
      const endpoint=endpoints.find(item=>item.method===message.method && item.path===message.path);
      if(!endpoint) throw Error('Unknown endpoint');
      endpoint.handle(ctx);
      process.stdout.write(JSON.stringify({status:ctx.response.code,value:ctx.response.value})+'\n');
    } catch (_) { process.stdout.write('{"error":true}\n'); }
  }
})().catch(()=>{process.exitCode=1;});
