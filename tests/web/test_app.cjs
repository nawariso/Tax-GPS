'use strict';
// Lifecycle tests use real API responses; only DOM and response timing are controlled.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const base = process.env.TAX_GPS_DEMO_URL || 'http://127.0.0.1:8765';
assert.match(base, /^http:\/\/127\.0\.0\.1:\d+$/);
const source = fs.readFileSync(path.join(__dirname, '../../examples/web/profile.js'), 'utf8') + '\n' + fs.readFileSync(path.join(__dirname, '../../examples/web/app.js'), 'utf8');

class Element {
  constructor() {
    this.children = [];
    this.listeners = {};
    this.hidden = false;
    this.disabled = false;
    this.valid = true;
    this.value = '';
    this.text = '';
    this.classList = {toggle() {}};
    this.attributes = {};
  }
  set textContent(value) { this.text = String(value); }
  get textContent() { return this.text + this.children.map(node => node.textContent).join(' '); }
  get innerText() { return this.textContent; }
  append(...nodes) { this.children.push(...nodes); }
  replaceChildren(...nodes) { this.children = nodes; this.text = ''; }
  setAttribute(name, value) { this.attributes[name] = value; }
  addEventListener(name, fn) { this.listeners[name] = fn; }
  reportValidity() { return this.valid; }
  click() { this.listeners.click?.(); }
  remove() { this.removed = true; }
}

function harness() {
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id, new Element());
    return elements.get(id);
  };
  const values = {salary:'990500', social_security:'10500', assets:'500000',
    expenses:'50000', budget:'100000', shared_usage:'0', planning_date:'2026-10-14'};
  Object.entries(values).forEach(([key,value]) => { get(key).value = value; });
  Object.entries({personal_eligible:'true', mortgage_interest:'0', mortgage_eligible:'false',
    required_coverage:'', existing_coverage:'', other_income:'0', retirement_usage:'0'}).forEach(([key,value])=>{get(key).value=value;});
  const calls = [];
  const context = vm.createContext({
    document: {getElementById:get, createElement:() => new Element(),
      querySelector:selector => get(selector)},
    Intl, Number, Object, Map, String, Blob, URL, setTimeout,
    FormData: class extends Map {
      constructor() { super(Object.keys(values).map(key => [key, get(key).value])); }
    },
    fetch: (url, options) => new Promise((resolve, reject) => {
      calls.push({url, options, resolve, reject});
    }),
  });
  vm.runInContext(source, context);
  return {
    get, calls,
    latest: () => vm.runInContext('latest', context),
    rows: () => vm.runInContext('comparisonRows(latest)', context),
    export: () => vm.runInContext('comparisonExport()', context),
    choose(id, checked = true, hash) { return vm.runInContext(`selectComparison(${JSON.stringify(id)},${JSON.stringify(checked)},${JSON.stringify(hash ?? this.latest().outcomes.result_hash)})`,context); },
    detail(id) { return vm.runInContext(`comparisonOpportunityDetail(${JSON.stringify(id)},latest)`,context); },
    recalculate: () => vm.runInContext('calculate()', context),
    scenario(value) { get('scenario').value = value; get('scenario').listeners.change(); },
    record(group, values) { return vm.runInContext(`addRecord(${JSON.stringify(group)},${JSON.stringify(values)})`,context); },
    async resolve(index, status = 200) {
      const call = calls[index];
      const response = await fetch(base + call.url, call.options);
      assert.equal(response.status, status, 'Response must come from the real engine');
      call.resolve(response);
      await settle();
    },
  };
}
const settle = () => new Promise(resolve => setTimeout(resolve, 30));

test('comparison starts with pinned NO_ACTION and no selected cash candidates',async()=>{
  const app=harness();await app.resolve(0);
  assert.equal(app.rows().length,1);
  assert.equal(app.rows()[0],app.latest().outcomes.candidates[0]);
  assert.equal(app.get('comparisonTableBody').children.length,1);
  assert.deepEqual(Array.from(app.export().comparison_view.selected_candidate_ids),[]);
});
test('selection renders authoritative fields without mutating engine output',async()=>{
  const app=harness();await app.resolve(0);const original=JSON.stringify(app.latest());
  const candidate=app.latest().outcomes.candidates[1];assert.equal(app.choose(candidate.candidate_id),true);
  assert.equal(app.rows()[1],candidate);assert.equal(JSON.stringify(app.latest()),original);
  const cells=app.get('comparisonTableBody').children[1].children;
  assert.equal(cells[1].textContent,'79,000.00 บาท');
  assert.equal(cells[2].textContent,'60,500.00 บาท');
  assert.equal(cells[3].textContent,'18,500.00 บาท');
  assert.equal(cells[4].textContent,'100,000.00 บาท');
  assert.equal(cells[5].textContent,'0.00 บาท');
  assert.equal(cells[6].textContent,'250,000.00 บาท');
  assert.equal(cells[7].textContent,'ยังไม่ทราบ');
  assert.match(cells[8].textContent,/5 ปี/);
  assert.equal(app.choose(candidate.candidate_id,false),true);assert.equal(app.rows().length,1);
});
test('baseline and unknown candidate IDs cannot become user selections',async()=>{
  const app=harness();await app.resolve(0);
  assert.equal(app.choose(app.latest().outcomes.candidates[0].candidate_id),false);
  assert.equal(app.choose('not-a-candidate'),false);assert.equal(app.rows().length,1);
});
test('selection reset binds to result identity even for repeated candidate IDs',async()=>{
  const app=harness();await app.resolve(0);const old=app.latest().outcomes;
  app.choose(old.candidates[1].candidate_id);app.get('budget').value='25000';
  app.get('planner').listeners.input();assert.equal(app.export(),null);
  assert.equal(app.get('comparisonTableBody').children.length,0);
  const pending=app.recalculate();await app.resolve(1);await pending;
  assert.equal(app.rows().length,1);assert.equal(app.choose(old.candidates[1].candidate_id,true,old.result_hash),false);
});
test('recalculating an unchanged profile also clears presentation selections',async()=>{
  const app=harness();await app.resolve(0);app.choose(app.latest().outcomes.candidates[1].candidate_id);
  const pending=app.recalculate();await app.resolve(1);await pending;assert.equal(app.rows().length,1);
});
test('zero tax benefit remains selectable and is not ranked away',async()=>{
  const app=harness();app.scenario('zero');await app.resolve(1);
  const candidate=app.latest().outcomes.candidates[1];assert.equal(candidate.tax_saved,'0.00');
  assert.equal(app.choose(candidate.candidate_id),true);assert.equal(app.rows().length,2);
});
test('NO_ACTION-only and partial financial results do not create alternatives',async()=>{
  const app=harness();app.scenario('debt');await app.resolve(1);assert.equal(app.rows().length,1);
  assert.match(app.get('comparisonSelectionStatus').textContent,/ไม่มีรายการใช้เงิน/);
  app.scenario('unknown');await app.resolve(2);assert.equal(app.rows().length,1);
  assert.equal(app.get('comparisonTableBody').children[0].children[6].textContent,'ยังไม่ทราบ');
});
test('missing lockup metadata is not described as no constraints',async()=>{
  const app=harness();await app.resolve(0);
  assert.match(app.detail('TH-OPP-SOLAR-ROOFTOP-2026'),/ไม่ระบุในข้อมูลที่ใช้/);
});
test('export keeps engine material intact and identifies user-selected presentation',async()=>{
  const app=harness();await app.resolve(0);const candidate=app.latest().outcomes.candidates[1];app.choose(candidate.candidate_id);
  const exported=app.export();assert.equal(exported.outcomes,app.latest().outcomes);
  assert.equal(exported.comparison_view.result_hash,app.latest().outcomes.result_hash);
  assert.equal(exported.comparison_view.kind,'USER_SELECTED_COMPARISON');
  assert.deepEqual(Array.from(exported.comparison_view.selected_candidate_ids),[candidate.candidate_id]);
});
test('late real response cannot replace selections made on a newer result',async()=>{
  const app=harness();app.scenario('zero');await app.resolve(1);
  const id=app.latest().outcomes.candidates[1].candidate_id;app.choose(id);await app.resolve(0);
  assert.equal(app.rows().length,2);assert.equal(app.rows()[1].candidate_id,id);assert.equal(app.latest().tax_before,'0.00');
});


test('a detached selector from an unchanged earlier calculation cannot restore selection',async()=>{
  const app=harness();await app.resolve(0);
  const oldInput=app.get('candidates').children[1].children[1].children.at(-1).children[0];
  const pending=app.recalculate();await app.resolve(1);await pending;
  oldInput.checked=true;oldInput.listeners.change();assert.equal(app.rows().length,1);
});

test('latest scenario wins when an earlier real response arrives later', async () => {
  const app = harness();
  app.scenario('zero');
  await app.resolve(1);
  assert.equal(app.latest().tax_before, '0.00');
  await app.resolve(0);
  assert.equal(app.latest().tax_before, '0.00');
  assert.equal(app.get('tax').textContent, '0.00');
});

test('an older request cannot clear the latest pending UI state', async () => {
  const app = harness();
  app.scenario('tight');
  await app.resolve(0);
  assert.equal(app.get('result').hidden, true);
  assert.equal(app.get('calculate').disabled, true);
  assert.equal(app.latest(), null);
  await app.resolve(1);
  assert.equal(app.latest().outcomes.candidates[1].cash_outflow, '50000.00');
});

test('an older failure cannot overwrite the latest successful result', async () => {
  const app = harness();
  app.scenario('zero');
  await app.resolve(1);
  app.calls[0].reject(new Error('delayed older transport failure'));
  await settle();
  assert.equal(app.get('error').hidden, true);
  assert.equal(app.get('result').hidden, false);
  assert.equal(app.latest().tax_before, '0.00');
});

test('invalid input cancels publication of an already pending response', async () => {
  const app = harness();
  app.get('planner').valid = false;
  await app.recalculate();
  await app.resolve(0);
  assert.equal(app.latest(), null);
  assert.equal(app.get('result').hidden, true);
  assert.equal(app.get('calculate').disabled, false);
});

test('editing financial input invalidates displayed and exported results', async () => {
  const app = harness();
  await app.resolve(0);
  assert.equal(app.latest().tax_before, '79000.00');
  app.get('budget').value = '25000';
  app.get('planner').listeners.input();
  assert.equal(app.latest(), null);
  assert.equal(app.get('result').hidden, true);
  const pending = app.recalculate();
  await app.resolve(1);
  await pending;
  assert.equal(app.latest().outcomes.candidates[1].cash_outflow, '25000.00');
  assert.equal(app.latest().outcomes.candidates[1].tax_saved, '5000.00');
});

test('extended coverage fields reach the real engine', async()=>{
  const app=harness();
  app.get('required_coverage').value='1000000';
  app.get('existing_coverage').value='200000';
  const pending=app.recalculate();
  await app.resolve(1); await pending;
  assert.equal(app.latest().financial.protection_gap,'800000.00');
});

test('adding a debt invalidates results and blocks tax-motivated allocation',async()=>{
  const app=harness(); await app.resolve(0);
  app.record('debts',{debt_id:'card-1',category:'CREDIT_CARD',balance:'120000',apr_percent:'24',minimum_payment:'5000',secured:'false'});
  assert.equal(app.latest(),null);
  const pending=app.recalculate();await app.resolve(1);await pending;
  assert.equal(app.latest().financial.critical_debt_balance,'120000.00');
  assert.ok(app.latest().outcomes.candidates.every(c=>c.cash_outflow==='0.00'));
});

test('unsupported retirement input hides results and publishes an explicit error',async()=>{
  const app=harness();await app.resolve(0);
  app.get('retirement_usage').value='10000';
  const pending=app.recalculate();await app.resolve(1,400);await pending;
  assert.equal(app.latest(),null);assert.equal(app.get('result').hidden,true);
  assert.equal(app.get('error').hidden,false);
  assert.match(app.get('error').textContent,/เกษียณ/);
});

test('C01 prior usage clears tax, selection and export and cannot be restored by an old selector',async()=>{
  const app=harness();await app.resolve(0);
  const old=app.latest();app.choose(old.outcomes.candidates[1].candidate_id);
  app.get('shared_usage').value='100000';
  const pending=app.recalculate();await app.resolve(1,400);await pending;
  assert.equal(app.latest(),null);assert.equal(app.export(),null);
  assert.equal(app.rows().length,0);assert.equal(app.get('result').hidden,true);
  assert.match(app.get('error').textContent,/ลงทุนเดิม|วงเงินเดิม|ใช้สิทธิไปแล้ว/);
  assert.doesNotMatch(app.get('error').textContent,/ตรวจจำนวนเงิน/);
  assert.equal(app.choose(old.outcomes.candidates[1].candidate_id,true,old.outcomes.result_hash),false);
});

test('C01 unknown usage cannot publish a baseline after a late earlier response',async()=>{
  const app=harness();app.get('shared_usage').value='';
  const pending=app.recalculate();await app.resolve(1,400);await pending;
  await app.resolve(0);
  assert.equal(app.latest(),null);assert.equal(app.export(),null);
  assert.equal(app.get('result').hidden,true);
  assert.match(app.get('error').textContent,/ยังไม่ทราบ|ตรวจสอบ/);
  assert.match(app.get('error').textContent,/ข้อมูลที่ยังขาด: opportunity_facts\.shared_limit_usage/);
  assert.doesNotMatch(app.get('error').textContent,/ตรวจจำนวนเงิน/);
});

test('family scenario maps its records and normal scenario clears them',async()=>{
  const app=harness();app.scenario('family');await app.resolve(1);
  assert.equal(app.latest().tax_before,'42500.00');
  assert.equal(app.latest().tax_state.allowances.mortgage_interest,'100000.00');
  app.scenario('normal');await app.resolve(2);
  assert.equal(app.latest().tax_before,'79000.00');
  assert.deepEqual(Array.from(app.latest().submitted_profile.tax.benefits.children),[]);
  await app.resolve(0);
  assert.equal(app.latest().tax_before,'79000.00');
});

test('removing a debt clears its guardrail effect after recalculation',async()=>{
  const app=harness();const record=app.record('debts',{debt_id:'d',category:'CREDIT_CARD',balance:'120000',apr_percent:'24',minimum_payment:'5000',secured:'false'});
  const pending=app.recalculate();await app.resolve(1);await pending;
  assert.equal(app.latest().financial.critical_debt_balance,'120000.00');
  record.card.children.at(-1).click();assert.equal(app.latest(),null);
  const next=app.recalculate();await app.resolve(2);await next;
  assert.equal(app.latest().financial.critical_debt_balance,'0.00');
  assert.equal(app.latest().outcomes.candidates[1].cash_outflow,'100000.00');
});
