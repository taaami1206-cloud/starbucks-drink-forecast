// 電波がないところでもアプリを開けるように、アプリ本体（index.html）だけを保存しておく。
// ネットにつながるときは毎回最新版を取りに行き、つながらないときは保存しておいたものを使う。
// 問題データはiPadの中（localStorage）にあるので、ここでは扱わない。
const CACHE = 'ba-app-v1';
const APP = ['./', './index.html'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(APP)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET' || new URL(e.request.url).origin !== location.origin) return;
  // 電車などで電波が弱いときに待たされないよう、3秒でつながらなければ保存版を使う
  const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000));
  e.respondWith(
    Promise.race([fetch(e.request), timeout])
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
        }
        return res;
      })
      .catch(() => caches.match(e.request, { ignoreSearch: true }).then((r) => r || caches.match('./index.html')))
  );
});
