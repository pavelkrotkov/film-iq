// Real Kaneo UI and session, synthetic task only; all non-local traffic is blocked.
const {chromium} = require(process.cwd() + '/.cache/tracker-poc/browser-tools/node_modules/playwright-core');
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');

(async () => {
  const base = path.resolve('.cache/tracker-poc');
  const source = process.argv[3];
  const task = process.argv[2];
  const text = `Fictional cache browser save ${Date.now()}`;
  if (!/^[A-Za-z0-9_-]+$/.test(task || '') || !source || !path.resolve(source).startsWith(base + '/')) throw Error('Expected fictional task and project-local cookies');
  const cookies = fs.readFileSync(source, 'utf8').split('\n').map((line) => line.replace(/^#HttpOnly_/, '')).filter((line) => line && !line.startsWith('#')).map((line) => {
    const [domain, , cookiePath, secure, expires, name, value] = line.split('\t');
    if (!['localhost', 'localhost.local'].includes(domain) || cookiePath !== '/') throw Error('Unexpected cookie scope');
    return {url:'http://localhost:15173/', secure: secure === 'TRUE', expires: Number(expires) || -1, name, value};
  });
  const profile = path.join(base, 'browser-tools/cache-fixture-kaneo-profile');
  const browser = await chromium.launchPersistentContext(profile, {executablePath:'/Applications/Brave Browser.app/Contents/MacOS/Brave Browser', headless:true, serviceWorkers:'block', env:{...process.env,TMPDIR:profile}, args:['--disable-background-networking','--disable-sync','--no-first-run']});
  let calls = 0, blocked = 0, phase = 'setup';
  try {
    await browser.addCookies(cookies);
    await browser.route('**/*', route => {
      const req = route.request(), url = new URL(req.url());
      if (url.hostname !== 'localhost' || !['15173','15174','15179'].includes(url.port) || /movary|FILMREAL/i.test(url.href)) {blocked++; return route.abort();}
      if (url.port === '15179') {
        if (url.pathname !== `/cache/${task}` || req.method() !== 'GET') {blocked++; return route.abort();}
        calls++;
      }
      if (req.method() !== 'GET' && !url.pathname.endsWith(`/task/description/${task}`)) {blocked++; return route.abort();}
      return route.continue();
    });
    const page = browser.pages()[0] || await browser.newPage();
    phase = 'open';
    await page.goto(`http://localhost:15174/dist/cache-fixture/#film=${task}`, {waitUntil:'domcontentloaded'});
    await page.locator('.detail h2').waitFor({timeout:30000});
    await page.getByText('Fixture Stream (subscription)', {exact:false}).waitFor({timeout:30000});
    assert.ok(calls >= 1);
    const synopsis = page.locator('.detail textarea[rows="7"]');
    await synopsis.waitFor();
    await synopsis.fill(text);
    phase = 'save';
    await Promise.all([page.waitForResponse(r => r.url().endsWith(`/task/description/${task}`) && r.request().method() === 'PUT' && r.ok()), page.getByRole('button', {name:'Save to Kaneo'}).click()]);
    const beforeReload = calls;
    phase = 'reload';
    await page.reload({waitUntil:'domcontentloaded'});
    await page.getByText('Fixture Stream (subscription)', {exact:false}).waitFor({timeout:30000});
    assert.equal(await synopsis.inputValue(), text);
    assert.ok(calls > beforeReload, 'reload did not read cache');
    console.log(JSON.stringify({passed:true, trackerSaveReload:true, cacheHydrationAfterReload:true, cacheReads:calls, blocked}));
  } catch (e) { console.error(JSON.stringify({passed:false, phase, error:e.message.split('\n')[0], calls, blocked})); process.exitCode=1; }
  finally { await browser.close(); }
})().catch(e => {console.error(e.name); process.exitCode=1;});
