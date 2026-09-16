// Smoke test: run the artifact's inline script against a stub DOM and render every
// diagram type in both layouts. Fails loudly on NaN/undefined leaking into the SVG.
const fs = require('fs');

const html = fs.readFileSync(__dirname + '/../src/diagram-table.html', 'utf8');
const src = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)]
  .map(m => m[1]).filter(s => s.trim())[0];

const SEGS = {
  groundSeg: ['g', ['paper', 'ink']],
  layoutSeg: ['l', ['single', 'board']],
  boardSeg:  ['b', ['2x2', '3x2', '3x3', '4x2', '1x3']],
  frameSeg:  ['f', ['rect', 'circle']],
  logicSeg:  ['lg', ['cat', 'tier']],
  sizeSeg:   ['z', ['a4', 'a3', 'a2', 'sq', 'wide']],
  oriSeg:    ['o', ['land', 'port']],
  dpiSeg:    ['d', ['96', '150', '300', '600']],
  treatSeg:  ['t', ['plain', 'gray', 'fade']]
};

class El {
  constructor(id = '', tag = 'div') {
    this.id = id; this.tagName = tag; this.children = []; this.dataset = {};
    this.style = {}; this.attrs = {}; this.value = ''; this.textContent = '';
    this.innerHTML = ''; this.hidden = false; this.checked = false; this.className = '';
    this.classList = { toggle() {}, add() {}, remove() {}, contains() { return false; } };
  }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k]; }
  appendChild(c) { this.children.push(c); return c; }
  querySelector() { return null; }
  addEventListener() {}
  getBoundingClientRect() { return { left: 0, top: 0, width: 1120, height: 792 }; }
  focus() {} setSelectionRange() {} click() {}
  cloneNode() { const e = new El(this.id, this.tagName); e.innerHTML = this.innerHTML; return e; }
  get outerHTML() { return '<svg>' + this.innerHTML + '</svg>'; }
}

const els = {};
const get = id => (els[id] || (els[id] = new El(id)));
for (const [id, [attr, vals]] of Object.entries(SEGS)) {
  const el = get(id);
  el.children = vals.map(v => { const b = new El('', 'button'); b.dataset[attr] = v; return b; });
}
get('tTitle').value = '基地分析'; get('tProject').value = '測試專案'; get('tNo').value = 'A-01';
get('mWidth').value = '600'; get('mRings').value = '150, 300, 500'; get('mNorth').value = '0';

global.window = { addEventListener() {}, print() {} };
global.document = {
  getElementById: get,
  createElement: tag => new El('', tag),
  activeElement: null
};
global.localStorage = { getItem: () => null, setItem() {} };
global.navigator = { clipboard: { writeText: () => Promise.resolve(), write: () => Promise.resolve() } };
global.Image = class { set src(_) {} };
global.FileReader = class { readAsDataURL() {} };
global.ClipboardItem = class {};
global.Blob = class {};
global.setTimeout = () => 0;

eval(src);

const sheet = get('sheet'), ta = get('data');
const typeBtns = get('types').children;
const layoutBtns = get('layoutSeg').children;
const TYPES = ['share', 'stack', 'column', 'radar', 'rose', 'bubble', 'matrix', 'site', 'section', 'users'];

let fails = 0;
const check = (label, svg) => {
  const bad = [];
  if (!svg || svg.length < 400) bad.push('empty/too short (' + (svg || '').length + ')');
  if (/NaN/.test(svg)) bad.push('NaN in output');
  if (/undefined/.test(svg)) bad.push('undefined in output');
  if (/Infinity/.test(svg)) bad.push('Infinity in output');
  const opens = (svg.match(/<svg/g) || []).length, closes = (svg.match(/<\/svg>/g) || []).length;
  if (opens !== closes) bad.push('unbalanced nested <svg> ' + opens + '/' + closes);
  if (bad.length) { fails++; console.log('  FAIL ' + label + ' — ' + bad.join('; ')); }
  else console.log('  ok   ' + label + '  (' + svg.length + ' chars)');
};

if (typeBtns.length !== TYPES.length) {
  console.log('FAIL: expected ' + TYPES.length + ' types, got ' + typeBtns.length); fails++;
}

for (const layout of [0, 1]) {
  console.log((layout ? '— board layout' : '— single sheet'));
  layoutBtns[layout].onclick();
  for (let i = 0; i < typeBtns.length; i++) {
    typeBtns[i].onclick();
    check(TYPES[i] || ('type' + i), sheet.innerHTML);
  }
}

console.log('— option sweep on 基地疊圖 (board)');
typeBtns[7].onclick(); layoutBtns[1].onclick();
for (const [id, [attr, vals]] of Object.entries(SEGS)) {
  for (const v of vals) {
    get(id).children.find(b => b.dataset[attr] === v).onclick();
    check(id + '=' + v, sheet.innerHTML);
  }
}


// differential: does 階層單色 actually change the colours?
function fillsOf(){ return [...sheet.innerHTML.matchAll(/fill="(#[0-9a-fA-F]{6})"/g)].map(m=>m[1]); }
typeBtns[0].onclick(); layoutBtns[0].onclick();
get('logicSeg').children.find(b=>b.dataset.lg==='cat').onclick();   const a=fillsOf().join(',');
get('logicSeg').children.find(b=>b.dataset.lg==='tier').onclick();  const b2=fillsOf().join(',');
console.log(a===b2 ? 'FAIL: 階層單色 changed nothing' : 'ok   階層單色 repaints');
get('groundSeg').children.find(x=>x.dataset.g==='paper').onclick(); const c=fillsOf().join(',');
get('groundSeg').children.find(x=>x.dataset.g==='ink').onclick();   const d2=fillsOf().join(',');
console.log(c===d2 ? 'FAIL: 黑圖紙 changed nothing' : 'ok   黑圖紙 repaints');
// board panels really are one per layer
typeBtns[7].onclick(); layoutBtns[1].onclick();
get('boardSeg').children.find(x=>x.dataset.b==='3x2').onclick();
const panels=(sheet.innerHTML.match(/<svg x=/g)||[]).length;
console.log(panels===6 ? 'ok   6 layers -> 6 panels' : 'FAIL: expected 6 panels, got '+panels);
