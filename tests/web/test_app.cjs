'use strict';
// Lifecycle tests use real API responses; only DOM and response timing are controlled.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const base = process.env.TAX_GPS_DEMO_URL || 'http://127.0.0.1:8765';
assert.match(base, /^http:\/\/127\.0\.0\.1:\d+$/);
const source = fs.readFileSync(path.join(__dirname, '../../examples/web/app.js'), 'utf8');

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
    recalculate: () => vm.runInContext('calculate()', context),
    scenario(value) { get('scenario').value = value; get('scenario').listeners.change(); },
    async resolve(index) {
      const call = calls[index];
      const response = await fetch(base + call.url, call.options);
      assert.equal(response.status, 200, 'Fixture must be calculated by the real engine');
      call.resolve(response);
      await settle();
    },
  };
}
const settle = () => new Promise(resolve => setTimeout(resolve, 30));

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
