'use strict';

const annualFields = {
  cutoff_date: 'cutoff_date',
  confirmed_for: 'confirmCutoff',
  social_security: 'annual_social_security',
  'opportunity_facts.shared_limit_usage': 'annual_shared_usage',
  pvd_forecast_single_employer: 'pvd_forecast_single_employer',
  'rmf.assessment_date': 'cutoff_date',
  'thai_esg_what_if.amount': 'thai_esg_amount',
  'financial.liquid_assets': 'assets',
  'financial.monthly_essential_expenses': 'expenses',
};
const annualPeriodFields = ['wages','bonus','withholding','outside_coverage'];
let lastCutoff = '';
// Demo prefill is not the user's data: blank it in the annual route unless edited (D3).
const financePrefill = ['assets','expenses'];
const financeTouched = new Set();
const financeStash = new Map();
let confirmedCutoff = '';

function annualMode() {
  return $('calculationMode').value === 'annual';
}

function hasAnnualPvdForecast() {
  return $('cutoff_date').value !== '2026-12-31' && $('pvd_presence').value === 'true';
}

function annualRequest() {
  const {personal_eligible,mortgage_interest,mortgage_eligible,retirement_usage,
    parents,children,pvd,other_rights,fund_history,rmf,
    debts,commitments,required_coverage,existing_coverage} = collectProfile();
  const period = name => Object.fromEntries(annualPeriodFields.map(key => [key,$(name+'_'+key).value]));
  return {
    cutoff_date: $('cutoff_date').value,
    confirmed_for: confirmedCutoff,
    actual: period('actual'),
    forecast: period('forecast'),
    social_security: $('annual_social_security').value,
    shared_usage: $('annual_shared_usage').value,
    profile: {personal_eligible,mortgage_interest,mortgage_eligible,retirement_usage,
      parents,children,pvd,other_rights,fund_history,rmf},
    pvd_forecast_single_employer: hasAnnualPvdForecast() ? $('pvd_forecast_single_employer').value : '',
    thai_esg_what_if: {amount: $('thai_esg_amount').value, assets: $('assets').value,
      expenses: $('expenses').value, debts, commitments, required_coverage, existing_coverage},
  };
}

function annualFieldForFact(fact) {
  if (Object.hasOwn(annualFields,fact)) return $(annualFields[fact]);
  const [period,key] = fact.split('.');
  return (period === 'actual' || period === 'forecast') && annualPeriodFields.includes(key)
    ? $(period+'_'+key) : null;
}

function updateAnnualCutoff() {
  if (!annualMode()) return;
  const cutoff = $('cutoff_date').value;
  if (lastCutoff !== cutoff) {
    confirmedCutoff = '';
    lastCutoff = cutoff;
  }
  $('confirmCutoff').disabled = !cutoff;
  $('cutoffStatus').textContent = confirmedCutoff
    ? `ยืนยันข้อมูลถึง ${confirmedCutoff} แล้ว`
    : 'โปรดตรวจยอดทั้งสองช่วงและสิทธิ แล้วกดยืนยัน';
  $('annualYearEndHint').hidden = cutoff !== '2026-12-31';
  $('annualPvdAssumption').hidden = !hasAnnualPvdForecast();
}

function updateFinancePrefill(active) {
  for (const id of financePrefill) {
    if (financeTouched.has(id)) continue;
    if (active && !financeStash.has(id)) {
      financeStash.set(id,$(id).value);
      $(id).value = '';
    } else if (!active && financeStash.has(id)) {
      if ($(id).value === '') $(id).value = financeStash.get(id);
      financeStash.delete(id);
    }
  }
}

function updateEstimateMode() {
  const active = annualMode();
  updateFinancePrefill(active);
  $('annualInputs').hidden = $('annualInputs').disabled = !active;
  $('financeGroup').hidden = false;
  $('budgetField').hidden = active;
  $('thaiEsgAmountField').hidden = !active;
  $('legacyBaselineResult').hidden = $('legacyResult').hidden = active;
  $('annualResult').hidden = !active;
  $('pendingMetric1').textContent = active ? 'ภาษีทั้งปีโดยประมาณ' : 'ภาษีเงินได้ปัจจุบัน';
  $('pendingMetric2').textContent = active ? 'ภาษีหัก ณ ที่จ่ายทั้งปีโดยประมาณ' : 'เงินได้สุทธิ';
  $('pendingMetric3').textContent = active ? 'ยอดที่คาดว่าจะชำระเพิ่มหรือคืน' : 'สภาพคล่องใช้เพิ่มได้';
  $('pendingOptions').hidden = active;
  $('auditHint').textContent = active
    ? 'ไฟล์มีข้อมูลการเงินและสิทธิที่กรอก เก็บไว้ในที่ปลอดภัย'
    : 'ไฟล์มีข้อมูลโปรไฟล์และการเงิน รวมรายการที่คุณเลือกมาเทียบ เก็บไว้ในที่ปลอดภัย';
  for (const id of ['salary','social_security','planning_date','other_income','shared_usage']) {
    const field = $(id).closest?.('.field');
    if (field) field.hidden = active;
  }
  document.querySelector('label[for="pvd_single_employer"]').textContent = active
    ? 'นายจ้างเดียวถึงวันตัดข้อมูล' : 'นายจ้างเดียวตลอดปี ไม่มีเปลี่ยนงาน';
  document.querySelector('label[for="mortgage_interest"]').textContent = active
    ? 'ดอกเบี้ยบ้านที่จ่ายจริงถึงวันตัดข้อมูล (บาท)' : 'ดอกเบี้ยบ้านที่จ่ายจริงทั้งปี (บาท)';
  updateAnnualCutoff();
}

function initAnnualEstimate() {
  for (const id of financePrefill) {
    $(id).addEventListener('input', () => { financeTouched.add(id); financeStash.delete(id); });
  }
  $('calculationMode').addEventListener('change', () => {
    updateEstimateMode();
    invalidateResults();
  });
  $('confirmCutoff').addEventListener('click', () => {
    updateAnnualCutoff();
    if (!$('cutoff_date').value) return;
    confirmedCutoff = $('cutoff_date').value;
    invalidateResults();
  });
  updateEstimateMode();
}

function exactEstimateBaht(value) {
  if (value === null) return 'ยังไม่ทราบ';
  const [whole,decimal] = value.split('.');
  const digits = whole.replace(/\B(?=(\d{3})+(?!\d))/g,',');
  return `${digits}.${(decimal || '').padEnd(2,'0')} บาท`;
}

function renderAnnualEstimate(result) {
  const material = result.export.material;
  $('estimateCutoff').textContent = `ข้อมูลถึง ${material.cutoff_date} · ใช้เฉพาะยอดจ่ายสิทธิถึงวันตัดข้อมูล`;
  $('annualPit').textContent = exactEstimateBaht(result.tax.pit);
  $('annualWithholding').textContent = exactEstimateBaht(result.annual_withholding);
  $('annualSettlementLabel').textContent = ({
    PAY_MORE: 'คาดว่าชำระเพิ่ม', REFUND: 'คาดว่าจะได้รับคืน', BALANCED: 'ไม่มียอดเพิ่มหรือคืน',
  })[result.settlement_kind] || 'ยังประมาณยอดเพิ่มหรือคืนไม่ได้';
  $('annualSettlement').textContent = result.settlement_amount === null
    ? '—' : exactEstimateBaht(result.settlement_amount);
  const missing = result.withholding_missing_fact_ids.map(fact =>
    fact === 'actual.withholding' ? 'ภาษีหัก ณ ที่จ่ายจริง' : 'ภาษีหัก ณ ที่จ่ายที่คาดในช่วงที่เหลือ');
  $('annualMissing').textContent = missing.length ? `ยังขาด ${missing.join(' และ ')}` : '';
  const details = $('annualBreakdown');
  details.replaceChildren();
  for (const [period,title] of [['actual','ยอดจริง'],['forecast','ยอดคาดช่วงที่เหลือ']]) {
    const {wages,bonus,withholding} = material[period];
    details.append(row(`${title} · ค่าจ้าง`,exactEstimateBaht(wages)),
      row(`${title} · โบนัส`,exactEstimateBaht(bonus)),
      row(`${title} · ภาษีหัก ณ ที่จ่าย`,exactEstimateBaht(withholding)));
  }
  details.append(row('เงินได้สุทธิที่ใช้คำนวณภาษี',exactEstimateBaht(result.tax.taxable_income)));
  if (material.pvd_forecast_single_employer === true && result.tax.pvd.employee_paid !== '0.00') {
    details.append(row('สมมติฐาน PVD','นายจ้างเดียวตลอดช่วงที่เหลือ'));
  }
  renderRmfResult({
    rmf: result.tax.rmf,
    rmf_conditions: result.tax.rmf_conditions,
    estimate_label: 'ประมาณการภายใต้เงื่อนไข RMF ที่ต้องปฏิบัติต่อเนื่อง',
  }, exactEstimateBaht);
  $('hashes').replaceChildren();
  const {snapshot_hash,engine_version,pack} = result.export;
  [['รหัสตรวจสอบผล',snapshot_hash],['รุ่นตัวคำนวณ',engine_version],
    ['ชุดกฎภาษี',`${pack.rule_pack_id} @ ${pack.version}`],['รหัสตรวจสอบชุดกฎ',pack.content_hash]]
    .forEach(([label,value]) => $('hashes').append(el('dt',label),el('dd',value)));
  renderThaiEsgWhatIf(result.thai_esg_what_if);
}

function renderThaiEsgWhatIf(block) {
  $('thaiEsgResult').hidden = !block;
  if (!block) return;
  const ready = block.status === 'READY';
  const money = value => value === null ? '—' : exactEstimateBaht(value);
  $('thaiEsgStatus').textContent = block.error || '';
  $('thaiEsgPitAfter').textContent = ready ? money(block.impact.pit_after) : '—';
  $('thaiEsgSaving').textContent = ready ? money(block.impact.saving) : '—';
  $('thaiEsgSettlementLabel').textContent = !ready ? 'หลังซื้อเทียบยอดหัก ณ ที่จ่าย' : ({
    PAY_MORE: 'หลังซื้อคาดว่าชำระเพิ่ม', REFUND: 'หลังซื้อคาดว่าจะได้รับคืน',
    BALANCED: 'หลังซื้อไม่มียอดเพิ่มหรือคืน',
  })[block.settlement_after_kind] || 'หลังซื้อยังประมาณยอดเพิ่มหรือคืนไม่ได้ เพราะยอดหักยังไม่ครบ';
  $('thaiEsgSettlement').textContent = ready ? money(block.settlement_after_amount) : '—';
  $('thaiEsgCapacity').textContent = block.capacity ? money(block.capacity.remaining_capacity) : '—';
  $('thaiEsgOutflow').textContent = ready ? money(block.amount) : '—';
  $('thaiEsgGuardrailLimit').textContent = block.guardrail
    ? money(block.guardrail.max_feasible_allocation) : '—';
  $('thaiEsgCapacityNote').textContent = block.capacity_basis === 'CONSERVATIVE_AFTER_PVD_EXEMPTION'
    ? 'วงเงินแบบระมัดระวัง: คิด 30% จากเงินได้หลังหักส่วนที่ยกเว้นของ PVD ยังไม่ใช่สิทธิสูงสุดตามกฎหมาย' : '';
  const conditions = $('thaiEsgConditions');
  conditions.replaceChildren(
    el('li','ผลนี้คำนวณจากจำนวนที่คุณเลือก ไม่ใช่คำแนะนำให้ซื้อ และไม่ได้เลือกกองทุนให้'),
    el('li','เป็นประมาณการจากยอดจริงและยอดคาดที่กรอก การซื้อต้องเกิดภายในปีภาษี 2569'));
  if (block.lockup) {
    conditions.append(el('li',`ต้องถือหน่วยลงทุนอย่างน้อย ${block.lockup.minimum_holding_years} ปี นับจากวันซื้อ`));
  }
  if (block.evidence_requirements.length) conditions.append(el('li','ต้องมีหลักฐานการซื้อหน่วยลงทุน'));
}
