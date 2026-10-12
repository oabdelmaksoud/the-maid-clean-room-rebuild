// Explicit browser recorder. Validators never execute this file.
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.argv[2]);
const [url, variant, output, executable] = process.argv.slice(3);
(async () => {
  const browser = await chromium.launch({headless: true, ...(executable ? {executablePath: executable} : {})});
  try {
    const context = await browser.newContext({viewport: {width: 960, height: 640}, deviceScaleFactor: 1, locale: 'en-US', timezoneId: 'UTC', colorScheme: 'light', reducedMotion: 'reduce'});
    await context.route('**/*', route => new URL(route.request().url()).origin === new URL(url).origin ? route.continue() : route.abort());
    const page = await context.newPage();
    page.setDefaultTimeout(5000);
    await page.goto(`${url}/app.html?variant=${variant}`, {waitUntil: 'networkidle'});
    await page.screenshot({path: path.join(output, 'desktop.png'), animations: 'disabled'});
    await page.setViewportSize({width: 390, height: 700});
    await page.screenshot({path: path.join(output, 'mobile.png'), animations: 'disabled'});
    await page.setViewportSize({width: 960, height: 640});
    const state = async () => ({tasks: await page.locator('li').allTextContents(), error: await page.locator('#error').textContent(), input: await page.locator('input').inputValue()});
    await page.getByRole('button', {name: 'Save task'}).click();
    const feedback = {steps: [{id: 'blank', action: 'Submit blank task', state: await state()}]};
    await page.getByLabel('Task', {exact: true}).fill('Read a chapter');
    await page.getByRole('button', {name: 'Save task'}).click();
    const add = {id: 'add', action: 'Save Read a chapter', state: await state()};
    const baseline = {steps: [add]};
    await page.reload({waitUntil: 'networkidle'});
    const persistence = {steps: [add, {id: 'reload', action: 'Reload page', state: await state()}]};
    for (const [name, value] of Object.entries({baseline, feedback, persistence})) fs.writeFileSync(path.join(output, `${name}.json`), JSON.stringify(value, null, 2) + '\n');
    fs.writeFileSync(path.join(output, 'environment.json'), JSON.stringify({browser: browser.version(), playwright: require(path.join(process.argv[2], 'package.json')).version, viewport: ['960x640', '390x700'], scale: 1}, null, 2) + '\n');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
