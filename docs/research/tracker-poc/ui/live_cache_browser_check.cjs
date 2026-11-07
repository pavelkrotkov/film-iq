// Local fictional browser exercise: real UIs/trackers, intercepted metadata and image.
const {chromium} = require(process.cwd() + '/.cache/tracker-poc/browser-tools/node_modules/playwright-core');
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');

(async () => {
  const base = path.resolve('.cache/tracker-poc'), mode = process.argv[2];
  if (!['kaneo','youtrack'].includes(mode)) throw Error('Expected kaneo or youtrack');
  const id = process.argv[3], project = process.argv[4], cookieFile = process.argv[5];
  if (mode === 'kaneo' && (!/^[\w-]+$/.test(id || '') || !/^[\w-]+$/.test(project || '') || !cookieFile || !path.resolve(cookieFile).startsWith(base + '/'))) throw Error('Expected fictional task, project and project-local cookies');
  if (mode === 'youtrack' && !/^FILMPOC-[1-9]\d*$/.test(id || '')) throw Error('Expected fictional issue');
  const profile = path.join(base,mode === 'kaneo' ? 'browser-tools/cache-fixture-kaneo-profile' : 'browser-tools/filmiq-headless-profile');
  const bundle = mode === 'kaneo' ? fs.readFileSync(path.join(base, 'kaneo-live-cache-candidate.js')) : null;
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l3sAAAAASUVORK5CYII=','base64');
  const image = 'https://image.tmdb.org/t/p/w500/filmiq-fictional.png';
  let browser, surface, phase='startup', cacheReads=0, expiredReads=0, firstDeadline=0, imageReads=0, liveCalls=0, blocked=0, replaced=0, scriptPaths=[], responseStates=[], errors=[];
  try {
    browser = await chromium.launchPersistentContext(profile, {executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser',headless:true,serviceWorkers:'block',env:{...process.env,TMPDIR:profile},args:['--disable-background-networking','--disable-sync','--no-first-run']});
    if (mode === 'kaneo') {
      const cookies = fs.readFileSync(cookieFile,'utf8').split('\n').map(line=>line.replace(/^#HttpOnly_/, '')).filter(line=>line&&!line.startsWith('#')).map(line=>{
        const [domain,,cookiePath,secure,expires,name,value] = line.split('\t');
        if (!['localhost','localhost.local'].includes(domain) || cookiePath !== '/') throw Error('Unexpected cookie scope');
        return {url:'http://localhost:15173/',secure:secure==='TRUE',expires:Number(expires)||-1,name,value};
      });
      await browser.addCookies(cookies);
    }
    await browser.addInitScript(() => {
      window.__posterCheck = {fetches:[],created:[],revoked:[]};
      const originalFetch = window.fetch;
      window.fetch = function(resource, options) {
        if (String(resource).startsWith('https://image.tmdb.org/t/p/w500/filmiq-fictional.png')) window.__posterCheck.fetches.push(options?.cache);
        return originalFetch.apply(this, arguments);
      };
      const create = URL.createObjectURL.bind(URL), revoke = URL.revokeObjectURL.bind(URL);
      URL.createObjectURL = blob => {const url=create(blob);window.__posterCheck.created.push(url);return url;};
      URL.revokeObjectURL = url => {window.__posterCheck.revoked.push(url);return revoke(url);};
    });
    await browser.route('**/*', async route => {
      const req=route.request(), url=new URL(req.url()), text=decodeURIComponent(url.href+' '+(req.postData()||''));
      if (url.pathname.endsWith('/app.js')) scriptPaths.push(url.pathname);
      if (url.href === image && req.method() === 'GET') {imageReads++;return route.fulfill({status:200,contentType:'image/png',headers:{'Access-Control-Allow-Origin':'*','Cache-Control':'public,max-age=3600'},body:png});}
      if (!['localhost','127.0.0.1','[::1]'].includes(url.hostname) || /FILMREAL|movary/i.test(text)) {blocked++;return route.abort();}
      if (mode === 'kaneo' && url.port === '15174' && url.pathname === '/dist/app.js') {replaced++;return route.fulfill({status:200,contentType:'application/javascript',body:bundle});}
      const cachePath = mode === 'kaneo' ? `/cache/${id}` : `/api/issues/${id}/extensionEndpoints/filmiq-tmdb-fixture-isolated/metadata/cached`;
      if (url.pathname === cachePath) {
        cacheReads++;
        if (!firstDeadline) firstDeadline = Date.now() + 20000;
        const pastDeadline = Date.now() >= firstDeadline;
        if (pastDeadline) expiredReads++;
        const data = {tmdb_id:900000001,title:'Fictional film',synopsis:'Still fresh fictional synopsis',year:2001,genres:['Drama'],directors:[],poster_url:image,cache_expires_at:new Date(pastDeadline?Date.now()+60000:firstDeadline).toISOString(),availability:!pastDeadline?{status:'complete',checked_at:new Date().toISOString(),offers:[{provider:'Fixture Stream',kind:'subscription'}]}:{status:'unknown',checked_at:null,offers:[]}};
        return route.fulfill({status:200,contentType:'application/json',headers:{'Access-Control-Allow-Origin':'http://localhost:15174','Access-Control-Allow-Credentials':'true','Cache-Control':'no-store'},body:JSON.stringify(data)});
      }
      if (/\/refresh\/|\/metadata\/read$/.test(url.pathname)) {liveCalls++;return route.abort();}
      if (req.method() !== 'GET' || (url.pathname.includes('/api/issues/') && !url.pathname.includes(id)) || url.port === '15175' || url.port === '15176') {blocked++;return route.abort();}
      return route.continue();
    });
    const page=browser.pages()[0]||await browser.newPage();
    page.on('pageerror',error=>{
      const message = /^(Cannot read properties of (?:undefined|null) \(reading '[\w-]+'\)|[\w.]+ is not a function|Failed to fetch)$/.test(error.message) ? error.message : '[redacted]';
      const location = String(error.stack || '').match(/\bapp\.js:\d+:\d+/)?.[0] || null;
      errors.push({name:error.name,message,location});
    });
    page.on('response',response=>{const u=new URL(response.url());if(u.hostname==='localhost' && (u.pathname.includes('/api/task')||u.pathname.includes('/api/project')||u.pathname.includes('/api/issues')))responseStates.push(response.status());});
    phase='open';
    const url=mode==='kaneo' ? `http://localhost:15174/?project=${encodeURIComponent(project)}#film=${id}` : `http://localhost:18180/app/filmiq-cache-fixture-ui/films?app_project=FILMPOC&app_film=${id}`;
    await page.goto('about:blank');
    await page.goto(url,{waitUntil:'domcontentloaded'});
    surface=page;
    if (mode === 'youtrack') {
      const login=JSON.parse(fs.readFileSync(path.join(base,'private/youtrack-browser-fictional.json'))).login;
      surface=null;
      for (let i=0;i<45&&!surface;i++) {for(const frame of page.frames()) if(await frame.evaluate(user=>window.YTApp?.me?.login===user,login).catch(()=>false)){surface=frame;break;} if(!surface) await page.waitForTimeout(1000);}
      if(!surface) throw Error('Fictional YouTrack widget unavailable');
    }
    phase='initial';
    await surface.getByText('Fixture Stream (subscription)',{exact:false}).first().waitFor({timeout:15000});
    await surface.waitForFunction(() => window.__posterCheck.fetches.length > 0,{timeout:15000});
    const poster = surface.locator('img[src^="blob:"]').first();
    await poster.waitFor({state:'visible', timeout:15000});
    const posterBlob = await poster.getAttribute('src');
    const before=await surface.evaluate(()=>window.__posterCheck);
    assert.ok(before.fetches.every(value=>value==='no-store'));
    assert.ok(posterBlob && before.created.includes(posterBlob), 'Displayed poster blob was not created');
    phase='expiry';
    await page.waitForFunction(() => false, null, {timeout:1}).catch(()=>{}); // yield to pending iframe events
    for (let i=0;i<35 && !expiredReads;i++) await page.waitForTimeout(1000);
    assert.ok(expiredReads,'Cache-only rehydration did not run after expiry');
    await surface.getByText('Still fresh fictional synopsis',{exact:true}).first().waitFor({timeout:15000});
    await surface.getByText(/US (?:provider status|availability): unknown/i).first().waitFor({timeout:15000});
    const after=await surface.evaluate(()=>window.__posterCheck);
    assert.ok(after.revoked.includes(posterBlob),'Displayed poster blob was not revoked');
    assert.equal(liveCalls,0);
    if (mode === 'kaneo') assert.ok(replaced>=1);
    console.log(JSON.stringify({passed:true,mode,metadataIntercepted:true,cacheOnlyReads:cacheReads,expiryRehydrated:true,posterFetches:after.fetches.length,posterHttpNoStore:after.fetches.every(value=>value==='no-store'),posterDisplayed:true,priorBlobRevoked:true,imageRequestsIntercepted:imageReads,liveCalls,blocked}));
  } catch(e) {
    const diagnostics = surface ? await surface.evaluate(() => ({detail:!!document.querySelector('.detail'), posterFetches:window.__posterCheck?.fetches?.length||0, hasFixtureStream:document.body?.innerText.includes('Fixture Stream')||false, hasUnknown:document.body?.innerText.includes('unknown')||false,scriptCount:document.scripts.length})).catch(()=>null) : null;
    console.error(JSON.stringify({passed:false,mode,phase,error:e.message.split('\n')[0],cacheReads,imageReads,liveCalls,blocked,replaced,scriptRequestCount:scriptPaths.length,responseStates,errors,diagnostics}));process.exitCode=1;
  }
  finally {if(browser) await browser.close();}
})().catch(e=>{console.error(e.name);process.exitCode=1;});
