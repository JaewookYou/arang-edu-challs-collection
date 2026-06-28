const fs = require('fs');
const { JSDOM } = require('jsdom');
const [htmlFile, cookie, flag, urlArg] = process.argv.slice(2);
const html = fs.readFileSync(htmlFile, 'utf8');
const hits = [];
const dom = new JSDOM(html, {
  url: urlArg || 'http://victim.local/board/1',
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  beforeParse(window) {
    try { window.document.cookie = cookie || ''; } catch (e) {}
    // innerText 폴리필 (실제 브라우저엔 있음)
    try {
      Object.defineProperty(window.HTMLElement.prototype, 'innerText',
        { get() { return this.textContent; }, configurable: true });
    } catch (e) {}
    window.fetch = (u) => { hits.push('FETCH ' + u);
      const body = ('' + u).includes('/board/0') ? ('flag article: ' + flag) : '';
      return Promise.resolve({ text: () => Promise.resolve(body), json: () => Promise.resolve({}) }); };
    window.Image = function () { const o = {};
      Object.defineProperty(o, 'src', { set(v) { hits.push('IMG ' + v); } }); return o; };
    window.XMLHttpRequest = function () { return { open(m,u){this._u=u;}, send(){hits.push('XHR '+this._u);}, setRequestHeader(){} }; };
    if (window.navigator) window.navigator.sendBeacon = (u) => { hits.push('BEACON ' + u); return true; };
  }
});
// load 이벤트 백스톱
try { dom.window.dispatchEvent(new dom.window.Event('load')); } catch (e) {}
setTimeout(() => {
  const dec = s => { try { return decodeURIComponent(s); } catch(e){ return s; } };
  const leaked = hits.some(h => flag && (h.includes(flag) || dec(h).includes(flag)));
  console.log(JSON.stringify({ leaked, hits }));
}, 700);
