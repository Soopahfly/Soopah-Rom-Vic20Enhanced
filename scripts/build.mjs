import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import crypto from 'node:crypto';

const root = fileURLToPath(new URL('../', import.meta.url));
const build = path.join(root, 'build');
const verification = path.join(root, 'verification');
fs.mkdirSync(build, { recursive: true });
fs.mkdirSync(verification, { recursive: true });
const executable = name => process.env[name.toUpperCase()] || (process.platform === 'win32' ? `${name}.exe` : name);
function run(exe, args) {
  const result = spawnSync(exe, args, { encoding: 'utf8' });
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  if (result.error || result.status !== 0) throw result.error ?? new Error(`${exe} exited ${result.status}`);
}
const object = path.join(build, 'vic20-fixed.o');
const binary = path.join(build, 'vic20-fixed.bin');
run(executable('ca65'), ['--cpu', '6502', '--feature', 'labels_without_colons', '-l', path.join(build, 'vic20-fixed.lst'), '-o', object, path.join(root, 'src/vic20-fixed.s')]);
run(executable('ld65'), ['-C', path.join(root, 'src/vic20.cfg'), '-Ln', path.join(build, 'vic20-fixed.labels'), '-o', binary, object]);
const rebuilt = fs.readFileSync(binary);
if (rebuilt.length !== 16384) throw new Error(`Wrong ROM size: ${rebuilt.length}`);
const symbols = fs.readFileSync(path.join(build, 'vic20-fixed.labels'), 'utf8');
let preservedLabels = 0;
for (const match of symbols.matchAll(/^al\s+([0-9A-F]+)\s+\.LAB_([0-9A-F]{4})$/gm)) {
  const expected = parseInt(match[2], 16);
  if (expected >= 0xc000) {
    if (parseInt(match[1], 16) !== expected) throw new Error(`Moved ROM label: ${match[0]}`);
    preservedLabels++;
  }
}
const original = Buffer.concat([
  fs.readFileSync(path.join(root, 'reference/basic.901486-01.bin')),
  fs.readFileSync(path.join(root, 'reference/kernal.901486-07.bin')),
]);
if (original.length !== 16384) throw new Error('Wrong reference ROM sizes');
// Restrict changes to the six corrections, spare areas and startup banner.
const allowed = [[0xe188,0xe189], [0xe18b,0xe18c], [0xe437,0xe44d], [0xe47c,0xe4a0], [0xe4da,0xe500], [0xeff5,0xeff6], [0xf0ed,0xf102], [0xf26f,0xf279], [0xf513,0xf514], [0xf822,0xf834], [0xfe5d,0xfe66]];
const differences = [];
for (let i = 0; i < original.length; i++) {
  if (original[i] !== rebuilt[i]) {
    const address = 0xc000 + i;
    if (!allowed.some(([start, end]) => address >= start && address < end)) throw new Error(`Unexpected modification at $${address.toString(16)}`);
    differences.push({ address: `$${address.toString(16).toUpperCase()}`, original: original[i], patched: rebuilt[i] });
  }
}
const images = [['vic20-fixed.bin', rebuilt], ['basic.901486-01-fixed.bin', rebuilt.subarray(0,8192)], ['kernal.901486-07-fixed.bin', rebuilt.subarray(8192)]];
for (const [name, data] of images) {
  fs.writeFileSync(path.join(build, name), data);
  if (process.argv.includes('--update-roms')) fs.writeFileSync(path.join(root, 'roms', name), data);
  if (!data.equals(fs.readFileSync(path.join(root, 'roms', name)))) throw new Error(`Build differs from published ROM: ${name}`);
}
const report = { bytes: rebuilt.length, changedBytes: differences.length, preservedLabels, sha256: crypto.createHash('sha256').update(rebuilt).digest('hex'), publishedRomsMatch: true, differences };
fs.writeFileSync(path.join(verification, 'build-report.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ bytes: report.bytes, changedBytes: report.changedBytes, preservedLabels, publishedRomsMatch: true, sha256: report.sha256 }));
