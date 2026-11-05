// Existing YouTrack widget in a separate fixture app; no live provider or real project calls.
const {chromium} = require(process.cwd() + '/.cache/tracker-poc/browser-tools/node_modules/playwright-core');
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');

(async () => {
  const base = path.resolve('.cache/tracker-poc'), profile = path.join(base, 'browser-tools/filmiq-headless-profile');
  const login = JSON.parse(fs.readFileSync(path.join(base, 'private/youtrack-browser-fictional.json'))).login;
  const token = fs.readFileSync(path.join(base, 'private/youtrack-token'), 'utf8').trim();
  const issue = process.argv[2];
  const text = `Fictional YouTrack cache browser save ${Date.now()}`;
  if (!/^FILMPOC-[1-9]\d*$/.test(issue || '')) throw Error('Expected a FILMPOC fictional issue');
  const mapping = await fetch(`http://localhost:18180/api/issues/${issue}?fields=id,idReadable,summary,customFields(name,value)`, {headers:{Authorization:`Bearer ${token}`}});
  if (!mapping.ok) throw Error('Fictional issue unavailable');
  const row = await mapping.json(), ids = row.customFields.filter(f => f.name === 'FilmIQ TMDB ID');
  if (row.idReadable !== issue || row.summary !== 'Fictional film' || ids.length !== 1 || ids[0].value !== 900000001) throw Error('Fictional issue identity changed');
  const allowedIssue = row.id;
  const browser = await chromium.launchPersistentContext(profile, {executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser', headless:true, serviceWorkers:'block', env:{...process.env,TMPDIR:profile}, args:['--disable-background-networking','--disable-sync','--no-first-run']});
  let calls = 0, blocked = 0, phase = 'setup';
  try {
    await browser.route('**/*', route => {
      const req = route.request(), url = new URL(req.url());
      const text = decodeURIComponent(url.href + ' ' + (req.postData() || ''));
      if (!['localhost','127.0.0.1','[::1]'].includes(url.hostname) || /FILMREAL|movary/i.test(text)) {blocked++; return route.abort();}
      const fixtureRead = url.pathname === `/api/issues/${issue}/extensionEndpoints/filmiq-tmdb-fixture-isolated/metadata/read`;
      if (fixtureRead) calls++;
      if (req.method() !== 'GET' && !(req.method() === 'POST' && (fixtureRead || url.pathname === `/api/issues/${allowedIssue}`))) {blocked++; return route.abort();}
      return route.continue();
    });
    const page = browser.pages()[0] || await browser.newPage();
    const frameFor = async () => {
      for (let attempt=0; attempt<45; attempt++) {
        for (const frame of page.frames()) if (await frame.evaluate(user => window.YTApp?.me?.login === user, login).catch(() => false)) return frame;
        await page.waitForTimeout(1000);
      }
      throw Error('Fictional widget unavailable or fictional session expired');
    };
    phase = 'open';
    await page.goto(`http://localhost:18180/app/filmiq-cache-fixture-ui/films?app_project=FILMPOC&app_film=${issue}`, {waitUntil:'domcontentloaded'});
    let frame = await frameFor();
    await frame.getByLabel('Synopsis').waitFor({timeout:45000});
    await frame.getByText('Fixture Stream (subscription)', {exact:false}).first().waitFor({timeout:30000});
    assert.ok(calls >= 1);
    await frame.getByLabel('Synopsis').fill(text);
    phase = 'save';
    const button = frame.getByRole('button',{name:'Save film',exact:true});
    await button.focus();
    await Promise.all([page.waitForResponse(r => r.url().endsWith(`/api/issues/${allowedIssue}`) && r.request().method()==='POST' && r.ok()), page.keyboard.press('Enter')]);
    const beforeReload = calls;
    phase = 'reload';
    await page.reload({waitUntil:'domcontentloaded'});
    frame = await frameFor();
    await frame.getByLabel('Synopsis').waitFor({timeout:45000});
    await frame.getByText('Fixture Stream (subscription)', {exact:false}).first().waitFor({timeout:30000});
    assert.equal(await frame.getByLabel('Synopsis').inputValue(),text);
    assert.ok(calls > beforeReload, 'reload did not read the cache');
    await page.screenshot({path:path.join(base,'browser-tools/youtrack-fictional-cache.png')});
    console.log(JSON.stringify({passed:true,trackerSaveReload:true,cacheHydrationAfterReload:true,cacheReads:calls,blocked}));
  } catch (e) {console.error(JSON.stringify({passed:false,phase,error:e.message.split('\n')[0],calls,blocked}));process.exitCode=1;}
  finally {await browser.close();}
})().catch(e => {console.error(e.name);process.exitCode=1;});
