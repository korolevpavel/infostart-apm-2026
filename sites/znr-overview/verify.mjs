import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const root = new URL('./dist/', import.meta.url);
const elements = new Map();
const element = key => {
  if (!elements.has(key)) elements.set(key, {innerHTML:'',textContent:'',open:false,dataset:{},attributes:{},setAttribute(k,v){this.attributes[k]=v;},classList:{toggle(){}},addEventListener(){},showModal(){this.open=true;},close(){this.open=false;},getBoundingClientRect(){return {left:0,top:0,right:800,bottom:600};}});
  return elements.get(key);
};
const context = vm.createContext({
  window:{addEventListener(){},localStorage:{setItem(k,v){this[k]=v;}}}, location:{hash:''},
  document:{documentElement:{dataset:{}},querySelector:element,querySelectorAll(){return [];},addEventListener(){}},
  console, URL, Blob, setTimeout, clearTimeout,
});
vm.runInContext(fs.readFileSync(new URL('data.js',root),'utf8'),context);
vm.runInContext(fs.readFileSync(new URL('app.js',root),'utf8'),context);
const run = expression => vm.runInContext(expression,context);
assert.equal(run('document.documentElement.dataset.theme'),'light');
run("document.querySelector('#themeButton').onclick()");
assert.equal(run('document.documentElement.dataset.theme'),'dark');
assert.equal(run("window.localStorage['znr-theme']"),'dark');
assert.equal(element('#themeButton').attributes['aria-pressed'],'true');
assert.equal(element('#themeButton').attributes['aria-label'],'Включить светлую тему');
run("document.querySelector('#themeButton').onclick()");
assert.equal(run('document.documentElement.dataset.theme'),'light');
run("window.localStorage.setItem=()=>{throw new Error('Storage disabled');}; setTheme('dark',true)");
assert.equal(run('document.documentElement.dataset.theme'),'dark');
assert.equal(run('D.items.length'),6);
assert.equal(run('questionCount'),22);
assert.equal(run('totalTasks'),108);
assert.equal(run('completed'),0);
assert.equal(run("'llm-wiki/wiki/log.md' in D.documents"),false);
assert.ok(run("Object.keys(D.documents).every(p=>!p.includes('/raw/')&&!p.includes('/archive/')&&!p.includes('/.'))"));
assert.ok(!fs.readFileSync(new URL('styles.css',root),'utf8').includes('@import'));
assert.equal((element('#cards').innerHTML.match(/class="card"/g)||[]).length,6);
run("search='DEV-1C-05'; renderCards()");
assert.equal((element('#cards').innerHTML.match(/class="card"/g)||[]).length,1);
run("search='невозможныйзапрос'; renderCards()");
assert.ok(element('#cards').innerHTML.includes('Ничего не найдено'));
run("search=''; filter='mockup'; renderCards()");
assert.equal((element('#cards').innerHTML.match(/class="card"/g)||[]).length,3);
run("location.hash='#questions'; route()");
assert.equal((element('#questionList').innerHTML.match(/class="question-row"/g)||[]).length,22);
run("qItem='3'; renderQuestions()");
assert.equal((element('#questionList').innerHTML.match(/class="question-row"/g)||[]).length,4);
run("location.hash='#decisions'; route()");
assert.equal((element('#main').innerHTML.match(/class="decision-row"/g)||[]).length,18);
run("location.hash='#sources'; route()");
assert.ok(element('#main').innerHTML.includes('repositoryReady=false'));
for(let i=1;i<=6;i++) {
  run(`openItem(${i},'questions')`);
  assert.ok(element('#detailBody').innerHTML.includes('Дословные группы'));
  run("detailTab='tasks'; renderDetail()");
  assert.ok(element('#detailBody').innerHTML.includes('class="task"'));
  run("detailTab='docs'; renderDetail()");
  assert.equal((element('#detailBody').innerHTML.match(/class="doc-tile"/g)||[]).length,5);
}
run("openDoc('openspec/wiki-reconciliation.md')");
assert.ok(element('#documentBody').innerHTML.includes('<table>'));
run("openDoc('llm-wiki/raw/example.png')");
assert.ok(element('#documentBody').innerHTML.includes('Оригинал хранится в проекте'));
assert.ok(!run("inline('<img src=x onerror=alert(1)>')").includes('<img'));
assert.equal(run("resolveLink('../../../llm-wiki/wiki/index.md','openspec/changes/dev-01-weight-abcd-print/design.md').path"),'llm-wiki/wiki/index.md');
console.log('PASS: snapshot counts, cards, search, filters, 22 questions, 18 decisions, six detail views, documents, escaping. Browser rendering is not verified.');
