import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {describe, expect, it, vi} from 'vitest';

function worker() {
  const handlers: Record<string, (event: any) => void> = {};
  const cache = {addAll:vi.fn().mockResolvedValue(undefined),match:vi.fn().mockResolvedValue('cached-shell')};
  const caches = {open:vi.fn().mockResolvedValue(cache),keys:vi.fn().mockResolvedValue(['tb-farm-shell-old','unrelated-cache']),delete:vi.fn().mockResolvedValue(true)};
  const fetch = vi.fn().mockRejectedValue(new Error('offline'));
  const source = readFileSync(new URL('../../scripts/sw-template.js', import.meta.url), 'utf8').replace('__VERSION__', 'test').replace('__PRECACHE__', JSON.stringify(['/index.html','/assets/app.js']));
  runInNewContext(source, {self:{location:{origin:'https://farm.test'},addEventListener:(name:string, cb:(event:any)=>void)=>{handlers[name]=cb}},caches,fetch,URL,Promise});
  return {handlers, caches, cache, fetch};
}
describe('service worker shell policy', () => {
  it('precaches only the generated public file list', async () => {
    const {handlers,cache}=worker();let promise:Promise<void>|undefined;
    handlers.install({waitUntil:(p:Promise<void>)=>{promise=p}});
    await promise;
    expect(cache.addAll).toHaveBeenCalledWith(['/index.html','/assets/app.js']);
  });
  it('serves the cached shell for a known offline navigation', async () => {
    const {handlers,cache}=worker();let response:Promise<unknown>|undefined;
    handlers.fetch({request:{method:'GET',mode:'navigate',url:'https://farm.test/products'},respondWith:(p:Promise<unknown>)=>{response=p}});
    expect(await response).toBe('cached-shell');
    expect(cache.match).toHaveBeenCalledWith('/index.html');
  });
  it('does not intercept API, POST or cross-origin requests', () => {
    const {handlers}=worker();const respondWith=vi.fn();
    for (const request of [
      {method:'GET', mode:'cors', url:'https://farm.test/api/products'},
      {method:'POST', mode:'cors', url:'https://farm.test/api/entry'},
      {method:'GET', mode:'cors', url:'https://other.test/assets/app.js'},
    ]) handlers.fetch({request, respondWith});
    expect(respondWith).not.toHaveBeenCalled();
  });
  it('deletes only old application-shell caches', async () => {
    const {handlers,caches}=worker();let promise:Promise<unknown>|undefined;
    handlers.activate({waitUntil:(p:Promise<unknown>)=>{promise=p}});
    await promise;
    expect(caches.delete).toHaveBeenCalledTimes(1);
    expect(caches.delete).toHaveBeenCalledWith('tb-farm-shell-old');
  });
});
