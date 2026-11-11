// Cache only the generated public app shell. Never cache API responses or user data.
import {readdir, readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {join} from 'node:path';
const dist = new URL('../dist/', import.meta.url);
async function files(dir, prefix = '') {
  const entries = await readdir(dir, {withFileTypes: true});
  const result = await Promise.all(entries.map(e => e.isDirectory()
    ? files(join(dir, e.name), `${prefix}${e.name}/`)
    : [`${prefix}${e.name}`]));
  return result.flat();
}
const paths = (await files(dist.pathname)).filter(p => p !== 'sw.js').sort();
const hash = createHash('sha256');
for (const path of paths) hash.update(path).update(await readFile(new URL(path, dist)));
const version = hash.digest('hex').slice(0, 16);
const template = await readFile(new URL('./sw-template.js', import.meta.url), 'utf8');
await writeFile(new URL('sw.js', dist), template.replace('__VERSION__', version).replace('__PRECACHE__', JSON.stringify(paths.map(p => '/' + p))));
console.log(`Service worker: ${paths.length} static files, version ${version}`);
