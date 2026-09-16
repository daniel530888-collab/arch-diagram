"""Wire the tile base map into src/diagram-table.html."""
import io, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'src', 'diagram-table.html')
s = io.open(P, encoding='utf-8').read()

# --- 1. state -------------------------------------------------------------
old = '''  map:{ img:"", imgAR:0, treat:"gray", widthM:600, rings:"150, 300, 500", north:0, link:false } };'''
new = '''  map:{ img:"", imgAR:0, treat:"gray", widthM:600, rings:"150, 300, 500", north:0, link:false,
        lat:"", lon:"", tiles:"plain", zoom:0, attrib:"" } };'''
assert old in s, 'state'
s = s.replace(old, new)

old = '''     if(saved.map) Object.keys(S.map).forEach(function(k){ if(k in saved.map) S.map[k]=saved.map[k]; }); }catch(e){}'''
assert old in s, 'restore'

# --- 2. UI: search + coords + tile style, above the upload row ------------
old = '''      <h2>02b 地圖底圖 <b>Base Map</b></h2>
      <div class="row">
        <button id="pickImg">選擇底圖</button>'''
new = '''      <h2>02b 地圖底圖 <b>Base Map</b></h2>
      <div class="row">
        <input id="mQuery" placeholder="搜尋地點或地址" style="flex:1;min-width:0">
        <button id="searchBtn">搜尋</button>
      </div>
      <div id="mResults" class="hits"></div>
      <div class="row" style="margin-top:7px">
        <label class="f" style="flex:1;min-width:0">緯度 LAT<input id="mLat" inputmode="decimal"></label>
        <label class="f" style="flex:1;min-width:0">經度 LON<input id="mLon" inputmode="decimal"></label>
      </div>
      <div class="row" style="margin-top:7px">
        <div class="seg" id="tileSeg">
          <button data-k="plain" type="button">無標註</button>
          <button data-k="light" type="button">淺色</button>
          <button data-k="osm" type="button">OSM</button>
          <button data-k="dark" type="button">深色</button>
        </div>
      </div>
      <div class="row" style="margin-top:7px">
        <button id="grabBtn" class="btn-solid">抓取地圖底圖</button>
      </div>
      <p class="hint" id="mapNote">依「底圖實際寬度」自動選縮放級別，抓完會把寬度改寫成實測值。</p>
      <div class="row" style="margin-top:12px">
        <button id="pickImg">改用自己的圖</button>'''
assert old in s, 'ui'
s = s.replace(old, new)

# --- 3. CSS for the result list ------------------------------------------
old = '''.chk{display:flex;align-items:center;gap:8px;margin-top:11px;font-size:13px;color:var(--ink2)}'''
new = '''.hits{display:flex;flex-direction:column;gap:3px;margin-top:6px}
.hits .hit{text-align:left;font-size:12px;line-height:1.35;padding:6px 8px;color:var(--ink2)}
.hits .hit:hover{color:var(--ink)}
.hint.ok{color:var(--accent)}
.chk{display:flex;align-items:center;gap:8px;margin-top:11px;font-size:13px;color:var(--ink2)}'''
assert old in s, 'css'
s = s.replace(old, new)

# --- 4. the tile code, before the base-map handlers -----------------------
old = '''/* ---------- base map ---------- */
function loadImage(file){'''
tiles = io.open(os.path.join(ROOT, 'tools', '_tiles.js'), encoding='utf-8').read()
assert old in s, 'anchor'
s = s.replace(old, tiles + '\n/* ---------- base map ---------- */\nfunction loadImage(file){')

# --- 5. wiring ------------------------------------------------------------
old = '''seg("treatSeg",  "t",      function(){ return S.map.treat; }, function(v){ S.map.treat = v; });'''
new = '''seg("treatSeg",  "t",      function(){ return S.map.treat; }, function(v){ S.map.treat = v; });
seg("tileSeg",   "k",      function(){ return S.map.tiles; }, function(v){ S.map.tiles = v; });'''
assert old in s, 'seg'
s = s.replace(old, new)

old = '''  ["groundSeg","layoutSeg","boardSeg","frameSeg","logicSeg","sizeSeg","oriSeg","dpiSeg","treatSeg"]'''
new = '''  ["groundSeg","layoutSeg","boardSeg","frameSeg","logicSeg","sizeSeg","oriSeg","dpiSeg","treatSeg","tileSeg"]'''
assert old in s, 'syncall'
s = s.replace(old, new)

old = '''  set("mWidth", S.map.widthM); set("mRings", S.map.rings); set("mNorth", S.map.north);'''
new = '''  set("mWidth", S.map.widthM); set("mRings", S.map.rings); set("mNorth", S.map.north);
  set("mLat", S.map.lat); set("mLon", S.map.lon);'''
assert old in s, 'syncset'
s = s.replace(old, new)

old = '''[["mWidth","widthM"], ["mRings","rings"], ["mNorth","north"]].forEach(function(p){'''
new = '''$("searchBtn").onclick = searchPlace;
$("mQuery").onkeydown = function(e){ if(e.key === "Enter"){ e.preventDefault(); searchPlace(); } };
$("grabBtn").onclick = grabMap;
[["mWidth","widthM"], ["mRings","rings"], ["mNorth","north"], ["mLat","lat"], ["mLon","lon"]].forEach(function(p){'''
assert old in s, 'handlers'
s = s.replace(old, new)

# --- 6. attribution on the sheet -----------------------------------------
old = '''  tb += txt(M + 18, H - M + 18, "日期 " + new Date().toISOString().slice(0, 10) +
    "　·　輸出 " + opx[0] + " × " + opx[1] + " px @ " + S.dpi + " dpi",
    { fill:C.ink3, size:10, mono:true, raw:true });'''
new = '''  tb += txt(M + 18, H - M + 18, "日期 " + new Date().toISOString().slice(0, 10) +
    "　·　輸出 " + opx[0] + " × " + opx[1] + " px @ " + S.dpi + " dpi" +
    (S.type === "site" && S.map.attrib && S.map.img ? "　·　底圖 " + S.map.attrib : ""),
    { fill:C.ink3, size:10, mono:true, raw:true });'''
assert old in s, 'attrib'
s = s.replace(old, new)

io.open(P, 'w', encoding='utf-8').write(s)
print('map wired into src/diagram-table.html')
