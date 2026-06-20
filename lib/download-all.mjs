#!/usr/bin/env node
/**
 * Download every mirrored EnvKit service archive listed in lib/services.json into
 * ./services-cache/, verifying each against its sha256. This is the "download all
 * services" entry point.
 *
 * The binaries are NOT committed to this repo — GitHub blocks files over 100 MB
 * (mongodb is 620 MB, postgres 311 MB, mysql 8 243 MB), so they live as assets on
 * the `services` release. This script pulls them all from there.
 *
 * Usage:  node lib/download-all.mjs [outDir]
 */
import fs from 'node:fs';
import https from 'node:https';
import crypto from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const index = JSON.parse(fs.readFileSync(path.join(here, 'services.json'), 'utf8'));
const outDir = path.resolve(process.argv[2] || path.join(here, '..', 'services-cache'));
fs.mkdirSync(outDir, { recursive: true });

function download(url, dest, redirects = 0) {
  return new Promise((resolve, reject) => {
    if (redirects > 8) return reject(new Error('too many redirects'));
    https.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        res.resume();
        return download(new URL(res.headers.location, url).toString(), dest, redirects + 1).then(resolve, reject);
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error(`HTTP ${res.statusCode} for ${url}`));
      }
      const file = fs.createWriteStream(dest);
      res.pipe(file);
      file.on('finish', () => file.close(() => resolve()));
      file.on('error', reject);
    }).on('error', reject);
  });
}

function sha256(file) {
  return new Promise((resolve, reject) => {
    const h = crypto.createHash('sha256');
    fs.createReadStream(file).on('data', (d) => h.update(d)).on('end', () => resolve(h.digest('hex'))).on('error', reject);
  });
}

let ok = 0, failed = 0;
for (const svc of index.services) {
  const url = `${index.baseUrl}/${svc.file}`;
  const dest = path.join(outDir, svc.file);
  try {
    if (fs.existsSync(dest) && (await sha256(dest)) === svc.sha256) {
      console.log(`✓ ${svc.file} (cached, verified)`);
      ok++;
      continue;
    }
    process.stdout.write(`↓ ${svc.file} (${(svc.size / 1e6).toFixed(0)} MB)… `);
    await download(url, dest);
    const got = await sha256(dest);
    if (got !== svc.sha256) throw new Error(`sha256 mismatch (got ${got})`);
    console.log('verified');
    ok++;
  } catch (err) {
    console.log(`FAILED ${svc.file}: ${err.message}`);
    failed++;
  }
}
console.log(`\nDone: ${ok} ok, ${failed} failed → ${outDir}`);
process.exit(failed ? 1 : 0);
