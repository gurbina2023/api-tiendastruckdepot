# -*- coding: utf-8 -*-
import json

# El token de Mapbox NO aparece en el HTML: la geocodificación la hace el
# servidor (server.py, endpoint /geocode) usando la variable de entorno
# MAPBOX_TOKEN. El navegador de los usuarios nunca ve el token.
payload = json.load(open("payload.json", encoding="utf-8"))
n_branches = len(payload["branches"])
n_places = len(payload["index"])
data_js = json.dumps(payload, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Verificador de cobertura · Truck Depot</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  :root{ --rojo:#E1251B; --negro:#111; --gris:#f4f4f5; --linea:#e2e2e6; }
  *{ box-sizing:border-box; }
  html,body{ margin:0; height:100%; font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:#1a1a1a; }
  header{ background:var(--negro); color:#fff; padding:10px 16px; display:flex; align-items:center; gap:14px; }
  header .logo{ font-weight:800; letter-spacing:.5px; font-size:20px; }
  header .logo b{ color:var(--rojo); }
  header .sub{ font-size:13px; color:#cfcfd4; }
  header .stats{ margin-left:auto; font-size:12px; color:#bdbdc4; }
  .wrap{ display:flex; height:calc(100vh - 52px); }
  #side{ width:390px; min-width:320px; border-right:1px solid var(--linea); overflow-y:auto; padding:14px; background:#fff; }
  #map{ flex:1; }
  h2{ font-size:13px; text-transform:uppercase; letter-spacing:.6px; color:#666; margin:16px 0 8px; }
  .card{ border:1px solid var(--linea); border-radius:10px; padding:12px; margin-bottom:12px; }
  input[type=text]{ width:100%; padding:10px 12px; border:1px solid #cfcfd6; border-radius:8px; font-size:15px; }
  .hint{ font-size:12px; color:#777; margin-top:6px; line-height:1.45; }
  .matches{ list-style:none; margin:6px 0 0; padding:0; max-height:230px; overflow:auto; }
  .matches li{ padding:8px 10px; border-radius:8px; cursor:pointer; font-size:14px; }
  .matches li:hover{ background:var(--gris); }
  .matches li small{ color:#888; }
  .res-place{ font-size:16px; font-weight:700; margin-bottom:2px; }
  .row{ display:flex; align-items:center; gap:9px; padding:7px 0; border-top:1px dashed var(--linea); }
  .row:first-of-type{ border-top:0; }
  .dot{ width:12px; height:12px; border-radius:50%; flex:none; border:1px solid rgba(0,0,0,.25); }
  .row .b{ font-weight:600; }
  .badge{ margin-left:auto; font-size:12px; font-weight:700; padding:3px 9px; border-radius:20px; color:#fff; white-space:nowrap; }
  .muted{ color:#888; font-size:13px; }
  .btn{ background:var(--rojo); color:#fff; border:0; padding:9px 12px; border-radius:8px; font-weight:600; cursor:pointer; font-size:14px; }
  .btn.sec{ background:#e9e9ee; color:#333; }
  .legend label{ display:flex; align-items:center; gap:8px; font-size:13px; padding:3px 0; cursor:pointer; }
  .legend .sw{ width:14px; height:14px; border-radius:3px; flex:none; }
  .toolbar{ display:flex; gap:8px; margin-bottom:8px; }
  .note{ background:#fff8e1; border:1px solid #f2e2a8; border-radius:8px; padding:9px 11px; font-size:12px; color:#6b5b12; line-height:1.5; }
  .tabbar{ display:flex; gap:6px; margin-bottom:10px; }
  .tab{ flex:1; text-align:center; padding:8px; border:1px solid var(--linea); border-radius:8px; cursor:pointer; font-size:13px; font-weight:600; color:#555; }
  .tab.on{ background:var(--negro); color:#fff; border-color:var(--negro); }
  select{ width:100%; padding:9px; border:1px solid #cfcfd6; border-radius:8px; font-size:14px; }
  @media(max-width:820px){ .wrap{ flex-direction:column; height:auto; } #side{ width:100%; border-right:0; border-bottom:1px solid var(--linea);} #map{ height:60vh; } }
</style>
</head>
<body>
<header>
  <div class="logo">TRUCK<b>DEPOT</b></div>
  <div class="sub">Verificador de cobertura de entrega · Guatemala</div>
  <div class="stats" id="stats"></div>
</header>
<div class="wrap">
  <div id="side">
    <div class="tabbar">
      <div class="tab on" data-t="ubi" onclick="setTab('ubi')">Por ubicación</div>
      <div class="tab" data-t="suc" onclick="setTab('suc')">Por sucursal</div>
    </div>

    <div id="pane-ubi">
      <div class="card">
        <label for="q"><b>1) Buscar municipio, zona o aldea</b></label>
        <input type="text" id="q" placeholder="Ej.: Mixco, Zona 10, Antigua, Amatitlán…" autocomplete="off" oninput="onType()">
        <ul class="matches" id="matches"></ul>
        <div class="hint">Escribe la ubicación del cliente tal como aparece en la promesa de entrega.</div>
      </div>
      <div class="card">
        <label for="addr"><b>2) Comprobar una dirección real</b></label>
        <div class="toolbar" style="margin-top:6px">
          <input type="text" id="addr" placeholder="Ej.: 5a avenida 10-00 zona 10, Guatemala" onkeydown="if(event.key==='Enter')searchAddress()">
          <button class="btn" onclick="searchAddress()">Buscar</button>
        </div>
        <div id="gkeyStatus" class="hint" style="margin-top:6px">Escribe la dirección y pulsa <b>Buscar</b>.</div>

        <details id="advBox" style="margin-top:8px">
          <summary style="cursor:pointer;font-size:13px;color:#555"><b>Más opciones</b></summary>
          <div style="margin-top:12px">
            <div class="hint"><b>Limpiar</b>: quita el marcador del mapa y borra la búsqueda actual.</div>
            <div class="toolbar" style="margin-top:6px"><button class="btn sec" onclick="clearLocation()">🧹 Limpiar ubicación</button></div>
          </div>
          <div style="margin-top:12px">
            <div class="hint"><b>Alternativa</b>: ábrela en Google Maps y pega las coordenadas.</div>
            <div class="toolbar" style="margin-top:6px"><button class="btn sec" onclick="openGoogle()">Abrir en Google Maps ↗</button></div>
            <div class="toolbar">
              <input type="text" id="coords" placeholder="Pega coordenadas o el enlace de Google" onkeydown="if(event.key==='Enter')checkCoords()">
              <button class="btn sec" onclick="checkCoords()">Verificar</button>
            </div>
            <div style="margin-top:4px"><a href="#" onclick="quickOSM();return false;" style="font-size:12px;color:#777">↳ búsqueda rápida OpenStreetMap (puede fallar)</a></div>
          </div>
        </details>
      </div>
      <div id="result"></div>
    </div>

    <div id="pane-suc" style="display:none">
      <div class="card">
        <label for="selb"><b>Ver cobertura de una sucursal</b></label>
        <select id="selb" onchange="showBranch()" style="margin-top:6px"></select>
      </div>
      <div id="branchInfo"></div>
    </div>

    <h2>Sucursales (mostrar / ocultar)</h2>
    <div class="toolbar">
      <button class="btn sec" onclick="allLayers(true)">Todas</button>
      <button class="btn sec" onclick="allLayers(false)">Ninguna</button>
    </div>
    <div class="legend" id="legend"></div>

    <h2>Notas</h2>
    <div class="note">Los polígonos son <b>áreas aproximadas</b> a nivel municipio/zona (no fronteras oficiales). El tiempo real depende de la dirección exacta. Las franjas de <b>24/48&nbsp;h</b> son <b>envío nacional</b> (CEDI / Departamentos) y no se dibujan como zona.</div>
  </div>
  <div id="map"></div>
</div>

<script>
/* La búsqueda de direcciones se hace a través del servidor (endpoint /geocode);
   el token de Mapbox vive solo en el servidor y nunca llega a este navegador. */
const DATA = /*DATA*/;
const COLOR = {}; DATA.branches.forEach(b=>COLOR[b.name]=b.color);
const norm = s => (s||"").normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().replace(/\s+/g,' ').trim();
document.getElementById('stats').textContent = DATA.branches.length + " sucursales · " + DATA.index.length + " ubicaciones";

function tierColor(min){ if(min<=45)return '#1a9850'; if(min<=60)return '#66bd63'; if(min<=90)return '#a6d96a';
  if(min<=120)return '#f5a70a'; if(min<=180)return '#f46d43'; if(min<=360)return '#d73027'; return '#7a7a7a'; }

/* ---------- mapa ---------- */
let map=null, branchLayers={}, selMarker=null;
function initMap(){
  if(!window.L){ document.getElementById('map').innerHTML='<div style="padding:20px;color:#777">El mapa necesita conexión a internet para cargarse. El buscador de ubicaciones funciona igual.</div>'; return; }
  map=L.map('map',{zoomControl:true});
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'© OpenStreetMap'}).addTo(map);
  DATA.branches.forEach(b=>{ branchLayers[b.name]=L.layerGroup().addTo(map); });
  DATA.geo.features.forEach(f=>{ const p=f.properties; if(p.kind!=='coverage')return;
    L.geoJSON(f,{style:{color:p.color,weight:1.4,fillColor:p.color,fillOpacity:0.14}})
     .bindPopup('<b>'+p.branch+'</b><br>Entrega a domicilio hasta <b>'+p.label+'</b>')
     .addTo(branchLayers[p.branch]); });
  DATA.geo.features.forEach(f=>{ const p=f.properties; if(p.kind!=='store')return; const c=f.geometry.coordinates;
    L.circleMarker([c[1],c[0]],{radius:6,color:'#fff',weight:2,fillColor:p.color,fillOpacity:1})
     .bindPopup('<b>Tienda '+p.branch+'</b>').addTo(branchLayers[p.branch]); });
  try{ map.fitBounds(L.geoJSON(DATA.geo).getBounds().pad(0.05)); }catch(e){ map.setView([15.3,-90.4],7); }
}

/* ---------- leyenda ---------- */
function buildLegend(){
  const el=document.getElementById('legend'); el.innerHTML='';
  DATA.branches.forEach(b=>{
    const id='ck_'+norm(b.name).replace(/[^a-z0-9]/g,'');
    const lab=document.createElement('label');
    lab.innerHTML='<input type="checkbox" checked id="'+id+'"><span class="sw" style="background:'+b.color+'"></span>'+b.name;
    lab.querySelector('input').addEventListener('change',e=>{ if(!map)return; const lg=branchLayers[b.name];
      if(e.target.checked) map.addLayer(lg); else map.removeLayer(lg); });
    el.appendChild(lab);
  });
  const sel=document.getElementById('selb'); sel.innerHTML='<option value="">— elige —</option>';
  DATA.branches.forEach(b=>{ const o=document.createElement('option'); o.value=b.name; o.textContent=b.name; sel.appendChild(o); });
}
function allLayers(on){ DATA.branches.forEach(b=>{ const ck=document.getElementById('ck_'+norm(b.name).replace(/[^a-z0-9]/g,''));
  ck.checked=on; if(map){ if(on)map.addLayer(branchLayers[b.name]); else map.removeLayer(branchLayers[b.name]); } }); }

/* ---------- pestañas ---------- */
function setTab(t){ document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('on',x.dataset.t===t));
  document.getElementById('pane-ubi').style.display = t==='ubi'?'':'none';
  document.getElementById('pane-suc').style.display = t==='suc'?'':'none'; }

/* ---------- buscar por ubicación ---------- */
function onType(){
  const q=norm(document.getElementById('q').value); const ul=document.getElementById('matches'); ul.innerHTML='';
  if(q.length<2)return;
  const hits=DATA.index.filter(it=>norm(it.place).includes(q)).slice(0,40);
  hits.forEach(it=>{ const li=document.createElement('li');
    const fast=it.entries[0];
    li.innerHTML=it.place+' <small>· '+it.entries.map(e=>e.branch).filter((v,i,a)=>a.indexOf(v)===i).length+' sucursal(es)</small>';
    li.onclick=()=>selectPlace(it); ul.appendChild(li); });
  if(!hits.length) ul.innerHTML='<li class="muted">Sin coincidencias</li>';
}
function entryRows(entries){
  return entries.map(e=>{ const nac=e.minutes>=1440;
    return '<div class="row"><span class="dot" style="background:'+(COLOR[e.branch]||'#999')+'"></span>'+
      '<span class="b">'+e.branch+'</span>'+
      '<span class="badge" style="background:'+(nac?'#7a7a7a':tierColor(e.minutes))+'">'+(nac?'Envío nacional':e.label)+'</span></div>'; }).join('');
}
function selectPlace(it){
  document.getElementById('matches').innerHTML='';
  document.getElementById('q').value=it.place;
  const locals=it.entries.filter(e=>e.minutes<360.5);
  let html='<div class="card"><div class="res-place">'+it.place+'</div>';
  if(it.info){ html+='<div class="muted" style="font-size:12px;margin-bottom:6px">📍 '+it.info+'</div>'; }
  if(it.entries.length){ html+='<div class="muted" style="margin-bottom:6px">Sucursales que pueden despachar (de más rápida a más lenta):</div>'+entryRows(it.entries);
    if(!locals.length) html+='<div class="hint">Solo con envío nacional (24/48&nbsp;h); sin reparto local a domicilio desde una tienda cercana.</div>';
  } else html+='<div class="muted">Sin cobertura registrada.</div>';
  html+='</div>';
  document.getElementById('result').innerHTML=html;
  if(map && it.coord){ if(selMarker)map.removeLayer(selMarker);
    selMarker=L.marker(it.coord).addTo(map).bindPopup('<b>'+it.place+'</b>').openPopup();
    map.flyTo(it.coord, 11); }
}

/* ---------- buscar por sucursal ---------- */
function showBranch(){
  const name=document.getElementById('selb').value; const box=document.getElementById('branchInfo');
  if(!name){ box.innerHTML=''; return; }
  allLayers(false);
  const ck=document.getElementById('ck_'+norm(name).replace(/[^a-z0-9]/g,'')); ck.checked=true; if(map)map.addLayer(branchLayers[name]);
  const b=DATA.branches.find(x=>x.name===name);
  const byTier={};
  DATA.index.forEach(it=>it.entries.forEach(e=>{ if(e.branch===name){ (byTier[e.label]=byTier[e.label]||{min:e.minutes,places:[]}).places.push(it.place); }}));
  const order=Object.entries(byTier).sort((a,b)=>a[1].min-b[1].min);
  let html='<div class="card"><div class="res-place" style="color:'+b.color+'">'+name+'</div>';
  order.forEach(([label,o])=>{ const nac=o.min>=1440;
    html+='<div style="margin-top:8px"><span class="badge" style="background:'+(nac?'#7a7a7a':tierColor(o.min))+'">'+(nac?'Envío nacional':label)+'</span> '+
      '<span class="muted">'+o.places.length+' destino(s)</span><div class="hint" style="margin-top:4px">'+o.places.join(' · ')+'</div></div>'; });
  html+='</div>'; box.innerHTML=html;
  if(map){ try{ map.fitBounds(branchLayers[name].getBounds().pad(0.1)); }catch(e){ map.flyTo([b.store[0],b.store[1]],9);} }
}

/* ---------- geocodificar dirección real ---------- */
function pip(lng,lat,ring){ let inside=false;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++){ const xi=ring[i][0],yi=ring[i][1],xj=ring[j][0],yj=ring[j][1];
    if(((yi>lat)!==(yj>lat)) && (lng<(xj-xi)*(lat-yi)/(yj-yi)+xi)) inside=!inside; } return inside; }
function inFeature(lng,lat,g){ if(g.type==='Polygon')return pip(lng,lat,g.coordinates[0]);
  if(g.type==='MultiPolygon')return g.coordinates.some(p=>pip(lng,lat,p[0])); return false; }
/* ---- geocodificador: el servidor consulta Mapbox por nosotros (/geocode).
        El token queda solo en el servidor; el navegador nunca lo ve. ---- */
function searchAddress(){
  const q=document.getElementById('addr').value.trim(); const box=document.getElementById('result');
  if(!q){ box.innerHTML='<div class="card muted">Escribe una dirección.</div>'; return; }
  box.innerHTML='<div class="card muted">Buscando dirección…</div>';
  fetch('geocode?q='+encodeURIComponent(q))
   .then(function(r){ return r.json().then(function(d){ return {ok:r.ok, st:r.status, d:d}; }); })
   .then(function(o){
     if(!o.ok){ box.innerHTML='<div class="card muted">No se pudo buscar la dirección ('+o.st+'): '+((o.d&&o.d.message)||'')+'. Usa <b>Abrir en Google Maps ↗</b> y pega las coordenadas (en <b>Más opciones</b>).</div>'; const a=document.getElementById('advBox'); if(a) a.open=true; return; }
     const f=o.d && o.d.features && o.d.features[0];
     if(!f){ box.innerHTML='<div class="card muted">Mapbox no encontró esa dirección. Agrega detalle (zona, municipio, departamento).</div>'; return; }
     const c=(f.geometry && f.geometry.coordinates) || f.center;
     const p=f.properties || {};
     const label=(p.full_address || p.place_formatted || p.name || f.place_name || 'Ubicación');
     showPoint(c[1], c[0], String(label).split(',').slice(0,2).join(','));
   })
   .catch(function(e){ box.innerHTML='<div class="card muted">No se pudo conectar con el servidor de búsqueda. Usa <b>Abrir en Google Maps ↗</b> y pega las coordenadas (en <b>Más opciones</b>).</div>';
     const a=document.getElementById('advBox'); if(a) a.open=true; });
}

function clearLocation(){
  if(map && selMarker){ map.removeLayer(selMarker); selMarker=null; }
  document.getElementById('addr').value='';
  const q=document.getElementById('q'); if(q) q.value='';
  const m=document.getElementById('matches'); if(m) m.innerHTML='';
  const c=document.getElementById('coords'); if(c) c.value='';
  document.getElementById('result').innerHTML='<div class="card muted">Ubicación limpiada. Escribe una nueva dirección y pulsa <b>Buscar</b>.</div>'; }

function openGoogle(){ const q=document.getElementById('addr').value.trim(); if(!q){ document.getElementById('result').innerHTML='<div class="card muted">Escribe primero la dirección del cliente.</div>'; return; }
  window.open('https://www.google.com/maps/search/?api=1&query='+encodeURIComponent(q+' Guatemala'),'_blank'); }

function parseLatLng(s){ s=(s||'').trim();
  let m=s.match(/@(-?\d{1,2}\.\d+),(-?\d{2,3}\.\d+)/); if(m)return [parseFloat(m[1]),parseFloat(m[2])];
  m=s.match(/!3d(-?\d{1,2}\.\d+)!4d(-?\d{2,3}\.\d+)/); if(m)return [parseFloat(m[1]),parseFloat(m[2])];
  m=s.match(/(-?\d{1,2}\.\d+)\s*[, ]\s*(-?\d{2,3}\.\d+)/); if(m)return [parseFloat(m[1]),parseFloat(m[2])];
  return null; }

function checkCoords(){ const box=document.getElementById('result');
  let ll=parseLatLng(document.getElementById('coords').value);
  if(!ll){ box.innerHTML='<div class="card muted">No reconocí las coordenadas. Pega algo como <b>14.59950, -90.50690</b> o el enlace (URL) de Google Maps.</div>'; return; }
  let lat=ll[0], lng=ll[1];
  const inGT=(a,b)=>a>13&&a<18.5&&b<-88&&b>-92.9;
  if(!inGT(lat,lng)){ if(inGT(lng,lat)){ const t=lat; lat=lng; lng=t; }
    else { box.innerHTML='<div class="card muted">Esas coordenadas no parecen estar en Guatemala. Debe ser latitud (~14–17) y longitud (~-88 a -92).</div>'; return; } }
  showPoint(lat,lng,'Ubicación marcada'); }

function showPoint(lat,lng,title){
  if(map){ if(selMarker)map.removeLayer(selMarker); selMarker=L.marker([lat,lng]).addTo(map).bindPopup('<b>'+title+'</b>').openPopup(); map.flyTo([lat,lng],13); }
  const hits={}; DATA.geo.features.forEach(f=>{ const p=f.properties; if(p.kind!=='coverage')return;
    if(inFeature(lng,lat,f.geometry)){ if(!hits[p.branch]||p.minutes<hits[p.branch].minutes) hits[p.branch]={branch:p.branch,label:p.label,minutes:p.minutes}; }});
  let entries=Object.values(hits).sort((x,y)=>x.minutes-y.minutes);
  let near=null,nd=1e9; DATA.branches.forEach(b=>{ const d=Math.hypot(b.store[0]-lat,b.store[1]-lng); if(d<nd){nd=d;near=b;} });
  let html='<div class="card"><div class="res-place">'+title+'</div><div class="muted" style="font-size:12px;margin-bottom:6px">'+lat.toFixed(5)+', '+lng.toFixed(5)+'</div>';
  if(entries.length){ html+='<div class="muted" style="margin-bottom:6px">Cae dentro de la cobertura a domicilio de:</div>'+entryRows(entries); }
  else { html+='<div class="muted">Fuera de las zonas de reparto local dibujadas. Tienda más cercana: <b>'+near.name+'</b> (~'+Math.round(nd*111)+'&nbsp;km). Puede aplicar envío nacional 24/48&nbsp;h.</div>'; }
  html+='<div class="hint">Cobertura aproximada a nivel municipio/zona.</div></div>';
  document.getElementById('result').innerHTML=html; }

function quickOSM(){ const q=document.getElementById('addr').value.trim(); const box=document.getElementById('result');
  if(!q){ box.innerHTML='<div class="card muted">Escribe primero una dirección arriba.</div>'; return; }
  box.innerHTML='<div class="card muted">Buscando en OpenStreetMap…</div>';
  fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=gt&q='+encodeURIComponent(q))
   .then(r=>r.json()).then(a=>{ if(!a.length){ box.innerHTML='<div class="card muted">OpenStreetMap no encontró la dirección. Usa el botón <b>Google Maps ↗</b> y pega las coordenadas.</div>'; return; }
     showPoint(+a[0].lat,+a[0].lon, a[0].display_name.split(',').slice(0,2).join(',')); })
   .catch(e=>{ box.innerHTML='<div class="card muted">Sin conexión para OpenStreetMap. Usa el botón <b>Google Maps ↗</b> y pega las coordenadas.</div>'; }); }

initMap(); buildLegend();
</script>
</body>
</html>
"""

HTML = HTML.replace("/*DATA*/", data_js)
for fn in ("Verificador_Cobertura_TruckDepot.html", "index.html"):
    with open(fn, "w", encoding="utf-8") as f:
        f.write(HTML)
print("HTML escrito:", len(HTML), "bytes ·", n_branches, "sucursales ·", n_places, "ubicaciones")
print("Archivos: Verificador_Cobertura_TruckDepot.html + index.html (para alojar)")
