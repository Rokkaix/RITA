/* RITA çevrimdışı önbellek: uygulama kabuğu önbellekten, veri ağdan (yoksa son kopya). */
const C='rita-__SURUM__';
const SHELL=['./','index.html','manifest.webmanifest','icons/icon-192.png','icons/icon-512.png','icons/apple-touch-icon.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(C).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(k=>Promise.all(k.filter(x=>x!==C).map(x=>caches.delete(x)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{const u=new URL(e.request.url);if(e.request.method!=='GET'||u.origin!==location.origin)return;
  const net=()=>fetch(e.request.mode==='navigate'||u.pathname.includes('/data/')?new Request(e.request.url,{cache:'no-cache',credentials:'same-origin'}):e.request).then(r=>{if(r.ok){const cp=r.clone();caches.open(C).then(c=>c.put(e.request,cp))}return r});
  if(u.pathname.includes('/data/')||e.request.mode==='navigate'){e.respondWith(net().catch(()=>caches.match(e.request,{ignoreSearch:true}).then(r=>r||caches.match('index.html'))));return}
  e.respondWith(caches.match(e.request).then(r=>r||net()))});
/* Bildirim: RITA bildirim sunucusundan gelen görev bildirimi ekrana düşer; dokununca kart/Görevlerim açılır. */
self.addEventListener('push',e=>{let d={};try{d=e.data?e.data.json():{}}catch(x){d={t:'RITA',b:e.data&&e.data.text()}}
  e.waitUntil(Promise.all([
    self.registration.showNotification(d.t||'RITA · yeni görev',{body:d.b||'',icon:'icons/icon-192.png',badge:'icons/icon-192.png',tag:d.tag||undefined,renotify:!d.s,silent:!!d.s,requireInteraction:!d.s,vibrate:d.s?undefined:[200,100,200],data:{u:d.u||'./'}}),
    self.clients.matchAll({type:'window',includeUncontrolled:true}).then(L=>L.forEach(c=>c.postMessage({rita:'push'})))]))});
self.addEventListener('notificationclick',e=>{e.notification.close();const u=(e.notification.data&&e.notification.data.u)||'./';
  e.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(L=>{for(const c of L){if('focus' in c){c.navigate?c.navigate(u).catch(()=>{}):0;return c.focus()}}return self.clients.openWindow(u)}))});
