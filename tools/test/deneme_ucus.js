/* Yalnız yerel testler içindir; siteye ve uygulamaya girmez. Sayfaya yüklenince A.demo() ile deneme uçuşu kurar. */
A.demo=function(){const P=people(),find=n=>P.find(x=>x.n===n);
  const key='ÖRNEK IST-ESB 18:00';D.FA=D.FA||{};D.FA[key]=Date.now();D.AC=D.AC||{};D.AC['ÖRNEK']={tip:'73H',ad:'Boeing 737-800',tarih:new Date().toISOString().slice(0,10),kaynak:'örnek'};
  if(!D.F.includes(key))D.F.unshift(key);D.cur=key;delete D.C[key];
  /* check-in'li (mavi) ve bloke (gri) koltuklar: örnek */
  const S=D.S[key]={};/* mavi: check-in'li */['1A','2D','3C','5A','5B','5C','6D','6E','7A','8F','9B'].forEach(k=>S[k]=1);/* gri: bloke (gerekirse açılır) */['1C','1F','4A','4C','5D','5E','5F','10A','10B','10D','11A','11B','11C','11D','11E','11F'].forEach(k=>S[k]=2);
  const L=[['Abdullah Gül',1],['Hakan Fidan',1],['Numan Kurtulmuş',2],['Mehmet Şimşek',1],['Selçuk Bayraktaroğlu',1],['Yaşar Güler',2],['Özgür Özel',1]].map(([n,pax])=>[find(n),pax]).filter(a=>a[0]);
  const noUp=P.find(x=>!x.u&&!x.o&&x.r>=40&&x.r<300&&isActive(x.t));if(noUp)L.push([noUp,1]);
  D.P[key]=L.slice(0,8).map(([x,pax],i)=>({key:norm(x.n),id:'d'+i+Date.now(),n:x.n,sub:x.t,rank:x.r||999,up:x.u||'',o:x.o||'',pax,t:Date.now()+i}));
  tab='ucus';assign();save();render();toast('Örnek senaryo hazır: 8 rical yolcusu yerleştirildi')};