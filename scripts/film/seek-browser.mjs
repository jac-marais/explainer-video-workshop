// Capture uses installed Chrome with its sandbox on and Playwright from the project or PLAYWRIGHT.
// PAGE supplies the page when --page is absent; ordinary captures default to index.html.
// Capture allows file and data requests, waits for fonts and image decoding, and rejects page errors.
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import { existsSync } from 'node:fs';
import { join, resolve } from 'node:path';

export function argumentsFor(argv, optionNames) {
  const options = {}, positional = [];
  for (let index = 0; index < argv.length; index++) {
    const argument = argv[index];
    if (!argument.startsWith('--')) {
      positional.push(argument);
      continue;
    }
    if (!optionNames.includes(argument) || argument in options) throw new Error(`unexpected option ${argument}`);
    if (argument === '--sheets') options[argument] = true;
    else {
      const count = argument === '--every' ? 3 : 1;
      const values = argv.slice(index + 1, index + 1 + count);
      if (values.length !== count || values.some(value => value.startsWith('--'))) throw new Error(`missing value for ${argument}`);
      options[argument] = count === 1 ? values[0] : values;
      index += count;
    }
  }
  if (!options['--project']) throw new Error('--project DIR is required');
  return { options, positional, project: resolve(options['--project']) };
}

export function renderRange(options, duration) {
  const fps = Number(options['--fps'] ?? 30), workers = Number(options['--workers'] ?? 4);
  const from = Number(options['--from'] ?? 0), to = Number(options['--to'] ?? duration);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error('data-duration must be finite and positive');
  if (!Number.isInteger(workers) || workers < 1 || !Number.isFinite(fps) || fps <= 0
      || !Number.isFinite(from) || !Number.isFinite(to) || from < 0 || to > duration || from >= to) {
    throw new Error('--workers needs an integer >= 1, --fps a finite positive number, and 0 <= --from < --to <= duration');
  }
  const first = Math.round(from * fps), last = Math.round(to * fps);
  if (!Number.isSafeInteger(first) || !Number.isSafeInteger(last) || last <= first) throw new Error('range contains no frames or too many frames');
  return { fps, workers, first, last };
}

export function stillTimes(positional, every) {
  if (every) {
    if (positional.length) throw new Error('choose times or --every STEP FROM TO');
    const [step, from, to] = every.map(Number);
    if (!Number.isFinite(step) || step <= 0 || !Number.isFinite(from) || !Number.isFinite(to) || from < 0 || from >= to) {
      throw new Error('--every needs a finite positive interval and 0 <= FROM < TO');
    }
    const count = Math.floor((to - from) / step + 1e-9) + 1;
    if (!Number.isSafeInteger(count)) throw new Error('--every requests too many stills');
    return Array.from({ length: count }, (_, index) => Number((from + index * step).toPrecision(15)));
  }
  const times = positional.map(Number);
  if (!times.length || !times.every(time => Number.isFinite(time) && time >= 0)) throw new Error('give at least one finite nonnegative time in seconds');
  return times;
}

export async function launchBrowser(project) {
  const modulePath = process.env.PLAYWRIGHT || createRequire(join(project, 'package.json')).resolve('playwright');
  const playwright = await import(modulePath.startsWith('file:') ? modulePath : pathToFileURL(resolve(modulePath)).href);
  const { chromium } = playwright.chromium ? playwright : playwright.default;
  return chromium.launch({ channel: 'chrome', headless: true, chromiumSandbox: true,
    args: ['--allow-file-access-from-files'] });
}

export async function openPage(browser, project, pageName, needsTimeline = true) {
  const pagePath = resolve(project, pageName);
  if (!existsSync(pagePath)) throw new Error(`page does not exist: ${pagePath}`);
  const context = await browser.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1, serviceWorkers: 'block' });
  try {
    await context.route(url => !['file:', 'data:'].includes(url.protocol), route => route.abort());
    const page = await context.newPage(), errors = [];
    page.on('pageerror', error => errors.push(String(error)));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    await page.goto(pathToFileURL(pagePath).href);
    if (needsTimeline) {
      await page.waitForFunction(() => {
        const root = document.querySelector('[data-composition-id]');
        const timeline = window.__timelines?.[root?.dataset.compositionId || 'film'];
        return !!timeline;
      }, null, { timeout: 30000, polling: 100 }).catch(() => { throw new Error(`timeline never registered: ${errors.join(' | ')}`); });
    }
    await page.evaluate(async () => {
      await document.fonts.ready;
      await Promise.all([...document.images].map(image => image.decode().catch(() => {})));
    });
    assertPageHealthy(errors);
    return { context, page, errors };
  } catch (error) {
    await context.close();
    throw error;
  }
}

export function assertPageHealthy(errors) {
  if (errors.length) throw new Error(`page errors:\n${errors.join('\n')}`);
}

export async function seekPage(page, time) {
  await page.evaluate(async time => {
    const root = document.querySelector('[data-composition-id]');
    window.__timelines[root?.dataset.compositionId || 'film'].seek(time, false);
    await Promise.all([...document.images].map(image => image.decode().catch(() => {})));
  }, time);
}

export async function pageDuration(page) {
  const duration = await page.evaluate(() => Number(document.querySelector('[data-duration]')?.dataset.duration));
  if (!Number.isFinite(duration) || duration <= 0) throw new Error('page needs a finite positive data-duration');
  return duration;
}
