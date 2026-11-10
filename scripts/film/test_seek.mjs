import test from 'node:test';
import assert from 'node:assert/strict';
import { argumentsFor, stillTimes, renderRange } from './seek-browser.mjs';
import { concatEntry } from './render-seek.mjs';

test('explicit project and finite still times', () => {
  const parsed = argumentsFor(['--project', "/tmp/project-'#", 'out', '0', '1'], ['--project']);
  assert.equal(parsed.project, "/tmp/project-'#");
  assert.deepEqual(stillTimes(parsed.positional.slice(1)), [0, 1]);
  assert.deepEqual(stillTimes([], ['0.5', '0', '1']), [0, 0.5, 1]);
  assert.deepEqual(stillTimes([], ['0.1', '0.2', '0.5']), [0.2, 0.3, 0.4, 0.5]);
  for (const times of [[], ['NaN'], ['Infinity'], ['-1']]) assert.throws(() => stillTimes(times));
  for (const every of [['0', '0', '1'], ['-1', '0', '1'], ['Infinity', '0', '1'], ['1', 'NaN', '1'], ['1', '1', '0']]) {
    assert.throws(() => stillTimes([], every));
  }
  assert.throws(() => argumentsFor([], ['--project']), /--project/);
  assert.throws(() => argumentsFor(['--project'], ['--project']), /missing/);
});

test('render bounds and worker guards', () => {
  assert.deepEqual(renderRange({ '--to': '2', '--workers': '2' }, 3), { fps: 30, workers: 2, first: 0, last: 60 });
  assert.deepEqual(renderRange({ '--from': '1', '--fps': '24' }, 3), { fps: 24, workers: 4, first: 24, last: 72 });
  for (const options of [{ '--workers': '0' }, { '--workers': '1.5' }, { '--fps': '0' }, { '--fps': 'Infinity' },
    { '--from': '-1' }, { '--from': 'NaN' }, { '--from': '2', '--to': '2' }, { '--to': '4' }, { '--to': 'Infinity' }, { '--to': '0.001' }]) {
    assert.throws(() => renderRange(options, 3));
  }
});

test('concat escapes apostrophes and preserves hashes', () => {
  assert.equal(concatEntry("/tmp/clip-'#.mp4"), "file '/tmp/clip-'\\''#.mp4'\n");
});
