import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';
import {allOptions, compose, hash, variantId} from './variants.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const args = process.argv.slice(2);
const options = {fixes: true, rainbow: true, banner: true};
let all = false;
for (const arg of args) {
  if (arg === '--all') { all = true; continue; }
  const match = /^--(fixes|rainbow|banner)=(true|false)$/.exec(arg);
  if (!match) throw new Error(`Unknown option: ${arg}`);
  options[match[1]] = match[2] === 'true';
}
const build = spawnSync(process.execPath, [path.join(root,'scripts/build.mjs')], {stdio:'inherit'});
if (build.error || build.status !== 0) throw build.error ?? new Error('Assembly failed');
const original = Buffer.concat([
  fs.readFileSync(path.join(root,'reference/basic.901486-01.bin')),
  fs.readFileSync(path.join(root,'reference/kernal.901486-07.bin')),
]);
const assembled = fs.readFileSync(path.join(root,'build/vic20-fixed.bin'));
const git = spawnSync('git', ['rev-parse','HEAD'], {cwd:root,encoding:'utf8'});
if (git.status !== 0) throw new Error('Cannot determine source commit');
const reports = [];
for (const selected of all ? allOptions() : [options]) {
  const id = variantId(selected);
  const directory = path.join(root,'dist',id);
  fs.mkdirSync(directory,{recursive:true});
  const combined = compose(original,assembled,selected);
  const files = {
    'basic.901486-01.bin': combined.subarray(0,8192),
    'kernal.901486-07.bin': combined.subarray(8192),
    'vic20-combined.bin': combined,
  };
  const report = {
    id, options:selected, target:'PAL 901486-07 / BASIC 901486-01',
    sourceCommit:git.stdout.trim(),
    files:Object.fromEntries(Object.entries(files).map(([name,data]) =>
      [name,{bytes:data.length,sha256:hash(data)}])),
    changedBytes:combined.reduce((n,byte,i) => n+Number(byte !== original[i]),0),
    limits:['Install the BASIC and KERNAL from the same variant together',
      'Combined image is BASIC followed by KERNAL, not an 8 KB chip image',
      'Physical hardware and full-machine timing remain unverified'],
  };
  for (const [name,data] of Object.entries(files)) fs.writeFileSync(path.join(directory,name),data);
  fs.writeFileSync(path.join(directory,'manifest.json'),JSON.stringify(report,null,2)+'\n');
  fs.writeFileSync(path.join(directory,'SHA256SUMS'),
    Object.entries(report.files).map(([name,file]) => `${file.sha256}  ${name}`).join('\n')+'\n');
  fs.writeFileSync(path.join(directory,'README.txt'),
    `Soopah ROM V2.26 - ${id}\nPAL VIC-20 only.\n\n`+
    `Fixes: ${selected.fixes}; rainbow: ${selected.rainbow}; V2.26 heading: ${selected.banner}\n`+
    'Install both 8 KB images from this folder together. Keep the original character ROM.\n'+
    'The combined image is BASIC first, then KERNAL. It is not an 8 KB chip image.\n'+
    'Fixes off deliberately retains original bugs. Hardware testing remains outstanding.\n');
  reports.push(report);
  console.log(`Built ${id}`);
}
fs.writeFileSync(path.join(root,'dist/index.json'),JSON.stringify(reports,null,2)+'\n');
