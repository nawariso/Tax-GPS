'use strict';
const $ = id => document.getElementById(id);
const form = $('planner');
let latest = null;
let calculationVersion = 0;
let calculationTimer = null;
let lastInputSnapshot = null;
const errorFields = new Map();
let comparisonNeedsReselection = false;
const money = value => value === null ? 'ยังไม่ทราบ' : new Intl.NumberFormat('th-TH', {minimumFractionDigits: 2, maximumFractionDigits: 2}).format(Number(value));
const baht = value => value === null ? 'ยังไม่ทราบ' : `${money(value)} บาท`;
const labels = {'TH-RIGHT-PERSONAL-ALLOWANCE':'ค่าลดหย่อนส่วนตัว','TH-RIGHT-SOCIAL-SECURITY':'เงินสมทบประกันสังคม','TH-OPP-THAI-ESG-2026':'วงเงินลดหย่อน Thai ESG','TH-OPP-ARTWORK-2025-2027':'การซื้อผลงานศิลปะ','TH-OPP-SOLAR-ROOFTOP-2026':'โซลาร์รูฟท็อปสำหรับที่อยู่อาศัย'};
const decisions = {ALLOW:'อยู่ในขอบเขตที่ผ่านข้อจำกัด', CAP:'จำกัดตามสภาพคล่อง', BLOCK:'ไม่เปิดให้ใช้เงินเพิ่ม', REQUIRE_REVIEW:'ต้องตรวจสอบข้อมูลเพิ่มเติม', NOT_APPLICABLE:'ไม่ใช้กับรายการนี้'};
const statuses = {AVAILABLE:'มีวงเงินสิทธิ', CLAIMED:'ใช้สิทธิแล้ว', REQUIRES_INPUT:'ต้องการข้อมูลเพิ่ม', RULE_NOT_READY:'กฎยังไม่พร้อมใช้งาน', INELIGIBLE:'ไม่เข้าเงื่อนไข', EXHAUSTED:'ไม่มีวงเงินเหลือ', OUTSIDE_EFFECTIVE_PERIOD:'อยู่นอกช่วงเวลาที่ใช้สิทธิได้'};
const reasons = {NO_ACTION_BASELINE:'ไม่ใช้เงินเพิ่ม ภาษีและสภาพคล่องคงเดิม', BUDGET_BOUND:'ติดเพดานงบที่กรอก', GUARDRAIL_CAP_APPLIED:'ลดวงเงินตามข้อจำกัดทางการเงิน', SHARED_LIMIT_APPLIED:'ติดเพดานวงเงินร่วม', FULL_ALLOCATION_DEDUCTION:'ใช้การลดหย่อนเต็มจำนวนตาม policy ที่เปิดใช้', PARTIAL_FINANCIAL_STATE:'ข้อมูลการเงินยังไม่ครบ ไม่สมมุติค่าที่ไม่ทราบเป็นศูนย์'};
function el(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function row(label, value) { const node = el('div'); node.append(el('dt', label), el('dd', value)); return node; }
function showTab(rights) {
  $('comparisonView').hidden = rights;
  $('rightsView').hidden = !rights;
  $('comparisonTab').classList.toggle('active', !rights);
  $('rightsTab').classList.toggle('active', rights);
  $('comparisonTab').setAttribute('aria-pressed', String(!rights));
  $('rightsTab').setAttribute('aria-pressed', String(rights));
}
$('comparisonTab').addEventListener('click', () => showTab(false));
$('rightsTab').addEventListener('click', () => showTab(true));
let comparisonResultHash = null;
const comparisonSelection = new Set();
function resetComparison() {
  comparisonSelection.clear(); comparisonResultHash = null;
  $('comparisonTableBody').replaceChildren();
  $('comparisonSelectionStatus').textContent = 'ยังไม่มีผลคำนวณสำหรับเปรียบเทียบ';
}
function comparisonRows(data) {
  if (!data || !data.outcomes || data.outcomes.result_hash !== comparisonResultHash) return [];
  return data.outcomes.candidates.filter(candidate => candidate.allocations.length === 0 || comparisonSelection.has(candidate.candidate_id));
}
function comparisonOpportunityDetail(id, data) {
  const item = data.discovery.opportunities.find(opportunity => opportunity.opportunity_id === id);
  const name = labels[id] || item?.name || id;
  const lock = item?.lockup_metadata;
  const holding = lock ? `อย่างน้อย ${lock.minimum_holding_years} ปี · ${lock.measurement === 'purchase-date-to-purchase-date' ? 'นับจากวันที่ซื้อ' : lock.measurement}` : 'ไม่ระบุในข้อมูลที่ใช้';
  return `${name}: ${holding} · กฎ: ${item?.rule_ids.join(', ') || 'ไม่ระบุ'} · แหล่งอ้างอิง: ${item?.source_ids.join(', ') || 'ไม่ระบุ'}`;
}
function renderComparison(data) {
  const body = $('comparisonTableBody'); body.replaceChildren();
  const rows = comparisonRows(data);
  rows.forEach(candidate => {
    const baseline = candidate.allocations.length === 0;
    const tr = el('tr'); tr.setAttribute('data-candidate-id',candidate.candidate_id);
    const title = baseline ? 'NO_ACTION · ไม่ใช้เงินเพิ่ม' : candidate.allocations.map(a => `${labels[a.opportunity_id] || data.discovery.opportunities.find(o => o.opportunity_id === a.opportunity_id)?.name || a.opportunity_id}: ${baht(a.amount)}`).join(' · ');
    const heading = el('th', title); heading.setAttribute('scope','row');tr.append(heading);
    ['tax_before','tax_after','tax_saved','cash_outflow','unused_budget','spendable_surplus_after','protection_gap'].forEach(key => tr.append(el('td',baht(candidate[key]))));
    tr.append(el('td',baseline ? 'จุดอ้างอิง ไม่ใช้เงินเพิ่ม' : candidate.allocations.map(a => comparisonOpportunityDetail(a.opportunity_id,data)).join(' | ')));
    const guardNotes = candidate.allocations.map(a => data.guardrails.assessments.find(g => g.opportunity_id === a.opportunity_id)).filter(Boolean).map(g => `${decisions[g.decision] || g.decision} · ${g.reason_codes.join(', ')}`).join(' · ');
    tr.append(el('td',[candidate.reason_codes.map(code => reasons[code] || code).join(' · '),guardNotes].filter(Boolean).join(' · ')));
    body.append(tr);
  });
  $('comparisonSelectionStatus').textContent = data.outcomes.candidates.every(c => c.allocations.length === 0) ? 'ไม่มีรายการใช้เงินที่ engine เปิดให้ทดลอง — แสดง NO_ACTION และเหตุผลจริง' : `เลือกมาเทียบ ${rows.filter(c => c.allocations.length > 0).length} รายการ · NO_ACTION แสดงเสมอ · เรียงตาม engine ไม่ใช่อันดับ`;
}
function selectComparison(id, checked, resultHash) {
  if (!latest || !latest.outcomes || typeof checked !== 'boolean' || resultHash !== comparisonResultHash || resultHash !== latest.outcomes.result_hash) return false;
  const candidate = latest.outcomes.candidates.find(c => c.candidate_id === id && c.allocations.length > 0);
  if (!candidate) return false;
  if (checked) comparisonSelection.add(id); else comparisonSelection.delete(id);
  renderComparison(latest);return true;
}
function comparisonExport() {
  if(latest?.planning_availability==='PVD_BASELINE_ONLY')return {...latest,comparison_view:{version:'1',kind:'BASELINE_ONLY',result_hash:latest.tax_state.output_hash}};
  if (!latest || !latest.outcomes || latest.outcomes.result_hash !== comparisonResultHash) return null;
  return {...latest,comparison_view:{version:'1',kind:'USER_SELECTED_COMPARISON',result_hash:latest.outcomes.result_hash,selected_candidate_ids:comparisonRows(latest).filter(c => c.allocations.length > 0).map(c => c.candidate_id)}};
}
function render(data) {
  resetComparison();
  const baselineOnly=data.planning_availability==='PVD_BASELINE_ONLY';
  $('comparisonTab').disabled=baselineOnly;
  $('pvdPlanningNote').hidden=!baselineOnly;$('pvdResult').hidden=!baselineOnly;
  $('tax').textContent=money(data.tax_before);$('taxable').textContent=money(data.taxable_income);
  if(baselineOnly){
    showTab(true);renderProfile(data);$('ready').textContent='ภาพรวมภาษีพร้อม · PVD กรณีพื้นฐาน';
    $('surplus').textContent='ยังไม่เปิด';$('reserve').textContent='ส่วนทดลองเงินเพิ่มรอขั้นถัดไป';
    $('pvdBreakdown').replaceChildren();
    [['เงินสะสมลูกจ้างที่จ่ายแล้ว',data.pvd.employee_paid],['ส่วนยกเว้นก่อนค่าใช้จ่าย',data.pvd.exemption],['ค่าใช้จ่ายจากรายได้หลังยกเว้น',data.tax_state.expenses.section_40_1],['ส่วนลดหย่อนหลังค่าใช้จ่าย',data.pvd.allowance],['เงินสะสมส่วนเกินสิทธิ',data.pvd.excess]].forEach(([label,value])=>$('pvdBreakdown').append(row(label,baht(value))));
    $('candidates').replaceChildren();$('comparisonTableBody').replaceChildren();$('rights').replaceChildren();
    data.discovery.existing_rights.forEach(item=>{const card=el('article',undefined,'right');card.append(el('h3',labels[item.opportunity_id]||item.name),el('p',`รวมในฐานภาษีแล้ว ${baht(item.eligible_amount)} · ไม่ใช้เงินเพิ่ม`));$('rights').append(card);});
    $('hashes').replaceChildren();Object.entries({output_hash:data.tax_state.output_hash,engine_version:data.tax_state.engine_version,rule_pack_version:data.tax_state.rule_pack_version}).forEach(([key,value])=>$('hashes').append(el('dt',key),el('dd',value)));return;
  }
  comparisonResultHash = data.outcomes.result_hash;
  renderComparison(data);
  renderProfile(data);
  $('tax').textContent = money(data.tax_before);
  $('taxable').textContent = money(data.taxable_income);
  $('surplus').textContent = money(data.financial.spendable_surplus);
  $('reserve').textContent = `หลังกันเงินที่ต้องรักษา ${baht(data.financial.protected_liquidity)}`;
  $('ready').textContent = data.financial.status === 'READY' ? 'ข้อมูลสภาพคล่องครบ' : 'ข้อมูลสภาพคล่องยังไม่ครบ';
  const names = new Map(data.discovery.opportunities.map(item => [item.opportunity_id, labels[item.opportunity_id] || item.name]));
  $('candidates').replaceChildren();
  data.outcomes.candidates.forEach(candidate => {
    const baseline = candidate.allocations.length === 0;
    const card = el('article', undefined, `candidate${baseline ? ' baseline' : ''}`);
    const head = el('div', undefined, 'candidateheader');
    head.append(el('small', baseline ? 'NO ACTION · จุดอ้างอิง' : 'FEASIBLE SCENARIO · ไม่ใช่คำแนะนำ'), el('h3', baseline ? 'ไม่ใช้เงินเพิ่ม' : candidate.allocations.map(a => names.get(a.opportunity_id) || a.opportunity_id).join(' + ')), el('p', baseline ? 'เก็บสภาพคล่องไว้เท่าเดิม' : `จัดสรร ${baht(candidate.total_allocation)}`));
    const body = el('div', undefined, 'candidatebody');
    const saving = el('div', undefined, 'saving');
    saving.append(el('span', 'ภาษีที่ลดลงจากจุดอ้างอิง'), el('strong', money(candidate.tax_saved)), el('small', 'บาท / ปี'));
    const dl = el('dl');
    dl.append(row('ภาษีหลังทางเลือกนี้', baht(candidate.tax_after)), row('เงินที่ต้องจ่ายเพิ่ม', baht(candidate.cash_outflow)), row('งบที่ยังไม่ใช้', baht(candidate.unused_budget)), row('สภาพคล่องใช้เพิ่มที่เหลือ', baht(candidate.spendable_surplus_after)), row('ช่องว่างความคุ้มครอง', baht(candidate.protection_gap)));
    body.append(saving, dl, el('div', candidate.reason_codes.map(code => reasons[code] || code).join(' · '), 'reason'));
    if (!baseline) {
      const picker = el('label',undefined,'comparison-picker');const input = el('input');
      input.type = 'checkbox';input.id = `compare-${candidate.candidate_id}`;
      input.checked = false;const selectionVersion = calculationVersion;
      input.addEventListener('change',()=>{if(selectionVersion !== calculationVersion || !selectComparison(candidate.candidate_id,input.checked,data.outcomes.result_hash))input.checked=false;});
      picker.append(input,el('span','เลือกมาเทียบในตาราง — ไม่ใช่คำสั่งซื้อ'));body.append(picker);
    }
    card.append(head, body);
    $('candidates').append(card);
  });
  $('rights').replaceChildren();
  const guards = new Map(data.guardrails.assessments.map(item => [item.opportunity_id, item]));
  [...data.discovery.existing_rights, ...data.discovery.opportunities].forEach(item => {
    const card = el('article', undefined, 'right');
    card.append(el('h3', labels[item.opportunity_id] || item.name), el('span', statuses[item.status] || item.status, 'status'));
    if (!item.requires_new_cash) card.append(el('p', `สิทธิเดิมที่รวมในฐานภาษีแล้ว: ${baht(item.eligible_amount)} · ไม่จัดสรรเงินซ้ำ`));
    else {
      card.append(el('p', `วงเงินสิทธิที่เหลือ: ${baht(item.remaining_capacity)}`));
      const guard = guards.get(item.opportunity_id);
      if (guard) card.append(el('p', `${decisions[guard.decision] || guard.decision} · เพดานใช้เงินใหม่ ${baht(guard.max_feasible_allocation)}`));
      if (item.lockup_metadata) card.append(el('p', `เงื่อนไขการถือครองจาก catalog: อย่างน้อย ${item.lockup_metadata.minimum_holding_years} ปี · ${item.lockup_metadata.measurement === 'purchase-date-to-purchase-date' ? 'นับจากวันที่ซื้อ' : item.lockup_metadata.measurement}`));
      card.append(el('p', `เหตุผลจาก engine: ${item.reason_codes.join(', ')}`));
      if (item.missing_fact_ids.length) card.append(el('p', `ข้อมูลที่ยังขาด: ${item.missing_fact_ids.join(', ')}`));
    }
    card.append(el('p', `กฎ: ${item.rule_ids.join(', ')} · แหล่งอ้างอิง: ${item.source_ids.join(', ')}`));
    $('rights').append(card);
  });
  $('hashes').replaceChildren();
  const hashes = {result_hash: data.outcomes.result_hash, input_hash:data.outcomes.input_hash, policy_hash:data.outcomes.policy_hash, engine_version:data.outcomes.engine_version};
  Object.entries(hashes).forEach(([key,value]) => $('hashes').append(el('dt', key), el('dd', value)));
}
function inputSnapshot() {
  return JSON.stringify({...Object.fromEntries(new FormData(form)),profile:collectProfile()});
}
function updateStatus(text) {
  $('inputStatus').textContent = text;
  $('liveStatus').textContent = text;
  $('loading').textContent = text;
}
function clearPublishedResults() {
  clearTimeout(calculationTimer);
  calculationTimer = null;
  calculationVersion++;
  const height = $('result').hidden ? 0 : $('result').getBoundingClientRect?.().height;
  if (height && $('liveShell').style) $('liveShell').style.minHeight = `${height}px`;
  if (comparisonSelection.size) comparisonNeedsReselection = true;
  resetComparison();
  errorFields.forEach((description,input)=>{
    input.removeAttribute('aria-invalid');
    if (description === null) input.removeAttribute('aria-describedby');
    else input.setAttribute('aria-describedby',description);
  });
  errorFields.clear();
  latest = null;
  $('download').disabled = true;
  $('result').hidden = true;
  $('liveShell').hidden = false;
  $('error').hidden = true;
  $('loading').hidden = true;
  $('calculate').disabled = false;
  document.querySelector('.results').setAttribute('aria-busy','true');
}
function invalidateResults() {
  const snapshot = inputSnapshot();
  if (snapshot === lastInputSnapshot) return;
  lastInputSnapshot = snapshot;
  clearPublishedResults();
  updateStatus('กำลังรออัปเดต · คำนวณอัตโนมัติเมื่อหยุดพิมพ์');
  updateGroupSummaries();
  calculationTimer = setTimeout(() => calculate(),450);
}
form.addEventListener('input', invalidateResults);
form.addEventListener('change', invalidateResults);

const fieldNames = {salary:'รายได้จากเงินเดือนทั้งปี',social_security:'ประกันสังคมที่จ่ายแล้ว',assets:'สินทรัพย์สภาพคล่อง',expenses:'ค่าใช้จ่ายจำเป็นต่อเดือน',budget:'งบทดลอง',shared_usage:'ยอด Thai ESG / ESGX ที่ใช้ไปแล้ว',planning_date:'วันที่วางแผน',personal_eligible:'สิทธิส่วนตัว',mortgage_interest:'ดอกเบี้ยบ้าน',mortgage_eligible:'เงื่อนไขสิทธิดอกเบี้ยบ้าน',required_coverage:'ความคุ้มครองที่ต้องการ',existing_coverage:'ความคุ้มครองที่มีอยู่',other_income:'รายได้อื่น',retirement_usage:'เงินออมเกษียณ'};
function fieldForFact(fact) {
  const pvdInput=pvdFieldForFact(fact);if(pvdInput)return pvdInput;
  if (fact === 'opportunity_facts.shared_limit_usage') return $('shared_usage');
  const parent = fact.match(/^parent\.(father|mother)\.eligible$/);
  if (parent) return profileRecords.parents.find(entry=>entry.fields.relationship.value === parent[1])?.fields.eligible;
  const record = fact.match(/^(parent|parents|children|debts|commitments)\[(\d+)\](?:\.(.+))?$/);
  if (record) {
    const fields=profileRecords[record[1] === 'parent' ? 'parents' : record[1]]?.[Number(record[2])]?.fields;
    return fields ? record[3] ? fields[record[3]] : Object.values(fields)[0] : null;
  }
  const key = fact.split('.').at(-1);
  return Object.hasOwn(fieldNames,key) ? $(key) : null;
}
function revealField(input) {
  if (!input) return;
  let parent = input.parentElement;
  while (parent) {if (parent.tagName === 'DETAILS') parent.open = true;parent = parent.parentElement;}
  input.focus?.();
  input.scrollIntoView?.({block:'center'});
}
function addErrorLink(input, label, target = $('error')) {
  if (!input) return;
  if (!errorFields.has(input)) errorFields.set(input,input.getAttribute('aria-describedby'));
  input.setAttribute('aria-invalid','true');
  input.setAttribute('aria-describedby',[errorFields.get(input),'error'].filter(Boolean).join(' '));
  const link = el('a',label,'error-link');link.href = `#${input.id}`;
  link.addEventListener('click',event=>{event.preventDefault();revealField(input);});
  target.append(link);
}
async function calculate(manual = false) {
  clearPublishedResults();
  lastInputSnapshot = inputSnapshot();
  updateGroupSummaries();
  const version = calculationVersion;
  if (!form.checkValidity()) {
    updateStatus('ยังมีข้อมูลที่ต้องกรอก · ดูช่องที่ระบุด้านล่าง');
    $('error').textContent = 'กรอกข้อมูลที่จำเป็นให้ครบก่อน ระบบจะคำนวณต่อให้อัตโนมัติ';
    const invalid = Array.from(form.elements || []).filter(input=>input.willValidate && !input.validity.valid);
    invalid.forEach(input=>addErrorLink(input,fieldNames[input.id] || input.labels?.[0]?.textContent || 'ตรวจรายการที่เพิ่ม'));
    $('error').hidden = false;
    if (manual) revealField(invalid[0]);
    $('loading').hidden = true;
    document.querySelector('.results').setAttribute('aria-busy','false');
    return;
  }
  updateStatus('กำลังอัปเดตผลคำนวณ…');
  $('calculate').disabled = true;
  try {
    const data = Object.fromEntries(new FormData(form));
    data.profile = collectProfile();
    const response = await fetch('/api/calculate', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data)});
    if (version !== calculationVersion) return;
    const result = await response.json();
    if (version !== calculationVersion) return;
    if (!response.ok) throw Object.assign(new Error(result.error || 'คำนวณไม่สำเร็จ'), {envelope: result});
    render(result);
    latest = result;
    $('liveShell').hidden = true;
    $('download').disabled = false;
    $('result').hidden = false;
    updateStatus(comparisonNeedsReselection ? 'อัปเดตแล้ว · โปรดเลือกรายการเปรียบเทียบใหม่หลังเปลี่ยนข้อมูล' : 'อัปเดตแล้ว · ผลคำนวณตรงกับข้อมูลล่าสุด');
    comparisonNeedsReselection = false;
  } catch (error) {
    if (version !== calculationVersion) return;
    // Baseline/input envelopes name the exact item; generic format advice would misdirect.
    const envelope = error.envelope;
    const scoped = envelope && ['BASELINE_NOT_READY','INPUT_REQUIRED','INVALID_INPUT'].includes(envelope.code);
    $('error').textContent = scoped
      ? `ยังไม่แสดงผลคำนวณ: ${error.message.replace(/\s*\((?:pvd|other_rights|fund_history)\.[a-z_]+\)/g,'')}`
      : `ยังไม่แสดงผลคำนวณ: โปรดตรวจจำนวนเงิน (ไม่ติดลบ ทศนิยมไม่เกิน 2 ตำแหน่ง) งบต้องไม่เกินสินทรัพย์ที่ทราบ และวันที่ต้องอยู่ในปี 2026 ตรวจสิทธิที่ยังไม่ทราบและรายการนอกขอบเขตด้วย — ${error.message}`;
    $('error').hidden = false;
    const c02Errors=new Map();
    (envelope?.missing_fact_ids || []).forEach(fact=>{
      const group=Object.keys(pvdGroups).find(key=>fact===key||fact.startsWith(key+'.'));
      let target=$('error');
      if(group){
        if(!c02Errors.has(group)){
          const details=el('details',undefined,'error-group');
          details.append(el('summary',({pvd:'ข้อมูล PVD',other_rights:'สิทธิอื่นในปีนี้',fund_history:'ประวัติกองทุน'})[group]+' · เปิดดูรายการที่ต้องตรวจ'));
          $('error').append(details);c02Errors.set(group,details);
        }
        target=c02Errors.get(group);
      }
      const input=fieldForFact(fact);
      addErrorLink(input,input ? fieldNames[input.id] || input.labels?.[0]?.textContent || 'ตรวจรายการนี้' : '',target);
    });
    updateStatus('ยังแสดงผลไม่ได้ · ตรวจข้อมูลที่ระบุด้านล่าง');
  } finally {
    if (version === calculationVersion) {
      $('loading').hidden = true;
      $('calculate').disabled = false;
      document.querySelector('.results').setAttribute('aria-busy','false');
    }
  }
}
form.addEventListener('submit', event => { event.preventDefault(); calculate(true); });
$('scenario').addEventListener('change', () => {
  resetProfile();
  const defaults = {salary:'990500',social_security:'10500',assets:'500000',expenses:'50000',budget:'100000',shared_usage:'0',planning_date:'2026-10-14'};
  const variants = {normal:{},tight:{assets:'200000'},unknown:{assets:'',budget:'0'},zero:{salary:'200000'},family:{},debt:{},commitment:{}};
  Object.entries({...defaults,...variants[$('scenario').value]}).forEach(([key,value]) => { $(key).value = value; });
  if ($('scenario').value==='family') {
    addRecord('parents',{relationship:'father',eligible:'true'});
    addRecord('children',{child_id:'child-1',order:'1',birth_year:'2015',legally_eligible:'true'});
    addRecord('children',{child_id:'child-2',order:'2',birth_year:'2020',legally_eligible:'true'});
    $('mortgage_interest').value='140000';$('mortgage_eligible').value='true';
  }
  if ($('scenario').value==='debt') addRecord('debts',{debt_id:'card-1',category:'CREDIT_CARD',balance:'120000',apr_percent:'24',minimum_payment:'5000',secured:'false'});
  if ($('scenario').value==='commitment') addRecord('commitments',{need_id:'tuition',amount:'300000',due_date:'2026-11-01',mandatory:'true',description:'ค่าเรียนตัวอย่าง'});
  showTab(false);
  calculate();
});
$('download').addEventListener('click', () => {
  const exported = comparisonExport();
  if (!exported) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(exported,null,2)], {type:'application/json'}));
  const link = el('a');
  link.href = url;
  link.download = 'tax-gps-demo-2026.json';
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
initProfile();
initPvdProfile(invalidateResults);
calculate();
