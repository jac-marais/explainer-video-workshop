import { mkdirSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { argumentsFor, stillTimes, launchBrowser, openPage, pageDuration, seekPage, assertPageHealthy } from './seek-browser.mjs';

const usage = `Save stills from a paused composition or capture each section.sheet of a frames page.
  node scripts/film/stills.mjs --project DIR OUT_DIR TIME...
  node scripts/film/stills.mjs --project DIR OUT_DIR --every STEP FROM TO
  node scripts/film/stills.mjs --project DIR OUT_DIR --sheets [--page frames.html]
Each still is a 1920x1080 t<time>.png in OUT_DIR. With --sheets, --page defaults to frames.html.
Writes OUT_DIR/sfx.json from window.SFX, or [] when absent.
See seek-browser.mjs for browser setup, page selection and capture guards.`;

async function main() {
  if (process.argv.includes('--help')) { console.log(usage); return; }
  const { options, positional, project } = argumentsFor(process.argv.slice(2), ['--project', '--page', '--every', '--sheets']);
  if (!positional.length) throw new Error('OUT_DIR is required');
  const output = resolve(positional.shift()), sheets = !!options['--sheets'];
  if (sheets && (positional.length || options['--every'])) throw new Error('--sheets cannot be combined with times');
  const times = sheets ? [] : stillTimes(positional, options['--every']);
  const browser = await launchBrowser(project);
  try {
    const { page, errors } = await openPage(browser, project, options['--page'] || process.env.PAGE || (sheets ? 'frames.html' : 'index.html'), !sheets);
    mkdirSync(output, { recursive: true });
    let count;
    if (sheets) {
      const sections = page.locator('section.sheet');
      count = await sections.count();
      if (!count) throw new Error('no section.sheet elements on the frames page');
      const names = new Set();
      for (let index = 0; index < count; index++) {
        const section = sections.nth(index), id = await section.getAttribute('id');
        if (!id || !/^[\w-]+$/.test(id) || names.has(id)) throw new Error('each sheet needs a unique filename-safe id');
        names.add(id);
        await section.screenshot({ path: join(output, `${id}.png`) });
        assertPageHealthy(errors);
      }
    } else {
      const duration = await pageDuration(page);
      if (times.some(time => time > duration) || (options['--every'] && Number(options['--every'][2]) > duration)) throw new Error('stills must be within data-duration');
      for (const time of times) {
        await seekPage(page, time);
        await page.screenshot({ path: join(output, `t${time.toFixed(3).padStart(8, '0')}.png`) });
        assertPageHealthy(errors);
      }
      count = times.length;
    }
    const events = await page.evaluate(() => window.SFX ?? []);
    if (!Array.isArray(events)) throw new Error('window.SFX must be an array when present');
    writeFileSync(join(output, 'sfx.json'), JSON.stringify(events));
    assertPageHealthy(errors);
    console.log(`${count} ${sheets ? 'sheets' : 'stills'}, ${events.length} sound events: ${output}`);
  } finally {
    await browser.close();
  }
}

main().catch(error => { console.error(error.message); process.exitCode = 1; });
