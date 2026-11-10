// Usage: node scripts/film/render-seek.mjs --project DIR OUT.mp4 [--from S] [--to S] [--fps 30] [--workers 4] [--page index.html]
import { spawn, spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { join, dirname, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { argumentsFor, renderRange, launchBrowser, openPage, pageDuration, seekPage, assertPageHealthy } from './seek-browser.mjs';

const usage = `Render a silent MP4 by seeking the paused timeline frame by frame in installed Chrome.
  node scripts/film/render-seek.mjs --project DIR OUT.mp4 [--from S] [--to S]
      [--fps 30] [--workers 4] [--page index.html]
Uses Chrome's sandbox, file/data requests only, and Playwright from the project/run
or PLAYWRIGHT. PAGE also sets the page. --from defaults to 0 and --to to data-duration.
OUT is never overwritten; temporary encoded segments remain beside it for inspection.
Use when HyperFrames' bundled browser cannot run on the host. Add audio afterwards:
  scripts/run/py scripts/film/render.py --skip-render OUT.mp4 -o FILM.mp4 --narration MIX.wav
Page and encoder errors exit 1.`;

export function concatEntry(path) {
  return `file '${path.replaceAll("'", "'\\''")}'\n`;
}

async function renderChunk(browser, project, pageName, temporary, worker, first, last, fps) {
  const { context, page, errors } = await openPage(browser, project, pageName);
  let encoder, completion;
  try {
    const segment = join(temporary, `seg${String(worker).padStart(2, '0')}.mp4`);
    encoder = spawn('ffmpeg', ['-nostdin', '-n', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg', '-i', '-',
      '-vf', 'scale=in_range=pc:out_range=tv,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-color_range', 'tv', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
      '-r', String(fps), segment], { stdio: ['pipe', 'inherit', 'inherit'] });
    completion = new Promise(resolve => {
      encoder.on('error', error => resolve(error));
      encoder.on('close', (code, signal) => resolve(code === 0 ? null : new Error(`ffmpeg failed: ${signal || code}`)));
    });
    let inputError;
    encoder.stdin.on('error', error => { inputError = error; });
    for (let frame = first; frame < last; frame++) {
      await seekPage(page, frame / fps);
      const image = await page.screenshot({ type: 'jpeg', quality: 92 });
      assertPageHealthy(errors);
      if (inputError || encoder.exitCode !== null || encoder.signalCode) throw inputError || new Error('ffmpeg exited during capture');
      if (!encoder.stdin.write(image)) {
        await Promise.race([
          new Promise(resolve => encoder.stdin.once('drain', resolve)),
          completion.then(error => { throw error || new Error('ffmpeg closed during capture'); }),
        ]);
      }
      if ((frame - first) % 300 === 0) console.log(`worker ${worker}: frame ${frame - first}/${last - first}`);
    }
    encoder.stdin.end();
    const error = await completion;
    if (error) throw error;
    assertPageHealthy(errors);
    return segment;
  } finally {
    if (encoder && encoder.exitCode === null && !encoder.signalCode) {
      // Closing the pipe wakes ffmpeg when capture fails before its first frame.
      encoder.stdin.destroy();
      encoder.kill('SIGTERM');
    }
    if (completion) await completion;
    await context.close();
  }
}

async function main() {
  if (process.argv.includes('--help')) { console.log(usage); return; }
  const { options, positional, project } = argumentsFor(process.argv.slice(2), ['--project', '--page', '--from', '--to', '--fps', '--workers']);
  if (positional.length !== 1) throw new Error('give one OUT.mp4 path');
  const output = resolve(positional[0]);
  if (existsSync(output)) throw new Error(`output already exists: ${output}`);
  const browser = await launchBrowser(project), started = Date.now();
  try {
    const pageName = options['--page'] || process.env.PAGE || 'index.html';
    const probe = await openPage(browser, project, pageName);
    const duration = await pageDuration(probe.page);
    await probe.context.close();
    const { first, last, fps, workers } = renderRange(options, duration);
    mkdirSync(dirname(output), { recursive: true });
    const temporary = mkdtempSync(join(dirname(output), '.seek-'));
    const framesPerWorker = Math.ceil((last - first) / workers), jobs = [];
    for (let worker = 0; worker < workers; worker++) {
      const chunkFirst = first + worker * framesPerWorker, chunkLast = Math.min(last, chunkFirst + framesPerWorker);
      if (chunkFirst < chunkLast) jobs.push(renderChunk(browser, project, pageName, temporary, worker, chunkFirst, chunkLast, fps));
    }
    const results = await Promise.allSettled(jobs);
    const failed = results.find(result => result.status === 'rejected');
    if (failed) throw failed.reason;
    const list = join(temporary, 'list.txt');
    writeFileSync(list, results.map(result => concatEntry(result.value)).join(''));
    const concat = spawnSync('ffmpeg', ['-nostdin', '-n', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list,
      '-c', 'copy', '-movflags', '+faststart+write_colr', output], { stdio: 'inherit' });
    if (concat.error || concat.status !== 0) throw concat.error || new Error(`concat failed: ${concat.signal || concat.status}`);
    console.log(`${output}: ${last - first} frames at ${fps} fps, ${((Date.now() - started) / 1000).toFixed(1)} s; segments: ${temporary}`);
  } finally {
    await browser.close();
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch(error => { console.error(error.message); process.exitCode = 1; });
}
