'use strict';

const annualFields = {
  cutoff_date: 'cutoff_date',
  confirmed_for: 'confirmCutoff',
  social_security: 'annual_social_security',
  'opportunity_facts.shared_limit_usage': 'annual_shared_usage',
  pvd_forecast_single_employer: 'pvd_forecast_single_employer',
  'rmf.assessment_date': 'cutoff_date',
};
const annualPeriodFields = ['wages','bonus','withholding','outside_coverage'];
let lastCutoff = '';
let confirmedCutoff = '';

function annualMode() {
  return $('calculationMode').value === 'annual';
}

function hasAnnualPvdForecast() {
  return $('cutoff_date').value !== '2026-12-31' && $('pvd_presence').value === 'true';
}

function annualRequest() {
  const {personal_eligible,mortgage_interest,mortgage_eligible,retirement_usage,
    parents,children,pvd,other_rights,fund_history,rmf} = collectProfile();
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

function updateEstimateMode() {
  const active = annualMode();
  $('annualInputs').hidden = $('annualInputs').disabled = !active;
  $('financeGroup').hidden = active;
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
}
