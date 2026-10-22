'use strict';
// Transport and presentation only; all conditions and amounts come from the domain.
const rmfFields=['own_purchase_paid','fund_name','amc_name','first_purchase_date','reporting_status','ordinary_own_purchase_confirmed','single_fund','single_amc','first_ever_purchase_in_tax_year','paid_through_assessment_date','declaration_completed','no_distributions_or_borrowing','no_known_reporting_problem','future_obligations_acknowledged'];
const rmfReportFields=['fund_name','amc_name','tax_year','cumulative_paid','confirmed_on'];
function collectRmfProfile() {
  const result=Object.fromEntries(rmfFields.map(k=>[k,document.getElementById('rmf_'+k).value]));
  if(document.getElementById('other_rights_rmf').value==='false')return null;
  result.report_confirmation=result.reporting_status==='CONFIRMED_SUBMITTED'?Object.fromEntries(rmfReportFields.map(k=>[k,document.getElementById('rmf_report_'+k).value])):null;
  return result;
}
function updateRmfVisibility() {
  const positive=document.getElementById('other_rights_rmf').value==='true';
  document.getElementById('rmfDetails').hidden=!positive;
  document.getElementById('rmfReport').hidden=document.getElementById('rmf_reporting_status').value!=='CONFIRMED_SUBMITTED';
  document.getElementById('budget').required=!(positive||document.getElementById('pvd_presence').value==='true');
}
function renderRmfProfile(data) {
  rmfFields.forEach(k=>{document.getElementById('rmf_'+k).value=data?.[k]??'';});
  rmfReportFields.forEach(k=>{document.getElementById('rmf_report_'+k).value=data?.report_confirmation?.[k]??'';});
  updateRmfVisibility();
}
function initRmfProfile(onChange) {
  ['other_rights_rmf','pvd_presence','rmf_reporting_status'].forEach(id=>document.getElementById(id).addEventListener('change',updateRmfVisibility));
  ['own_purchase_paid','fund_name','amc_name'].forEach(k=>document.getElementById('rmf_'+k).addEventListener('input',()=>{
    document.getElementById('rmf_reporting_status').value='';
    rmfReportFields.forEach(key=>{document.getElementById('rmf_report_'+key).value='';});
    updateRmfVisibility();onChange();
  }));
  updateRmfVisibility();
}
function rmfFieldForFact(fact) {
  if(fact==='rmf.assessment_date')return document.getElementById('planning_date');
  if(fact==='rmf')return document.getElementById('rmf_own_purchase_paid');
  if(fact==='rmf.report_confirmation')return document.getElementById('rmf_report_fund_name');
  return fact.startsWith('rmf.')&&rmfFields.includes(fact.slice(4))?document.getElementById('rmf_'+fact.slice(4)):null;
}
function renderRmfResult(data) {
  const c=data.rmf_conditions;
  document.getElementById('rmfResult').hidden=!c;
  document.getElementById('rmfEstimate').textContent=c?data.estimate_label:'';
  const list=document.getElementById('rmfConditions');list.replaceChildren();
  if(!c)return;
  const labels={RMF_CONTINUITY_REQUIRED:`ต้องซื้อต่อเนื่อง โดยเว้นซื้อได้ไม่เกิน ${c.maximum_purchase_gap_years} ปีติดต่อกัน`,RMF_HOLDING_REDEMPTION_REQUIRED:`เงื่อนไขถือครองอย่างน้อย ${c.minimum_holding_years} ปี และไถ่ถอนเมื่ออายุไม่น้อยกว่า ${c.minimum_redemption_age} ปีตามเงื่อนไข`,RMF_NO_DISTRIBUTIONS_REQUIRED:'ต้องไม่รับเงินปันผลหรือเงินอื่นจากกองทุน',RMF_NO_BORROWING_WITHDRAWAL_REQUIRED:'ต้องไม่กู้ยืมหรือถอนเงินจากกองทุน',RMF_AMC_REPORTING_PENDING:`รายงานของ บลจ. ยังไม่ถึงกำหนดปกติ ${c.reporting_due_date} · ยังไม่ได้ยืนยันว่ารายงานเสร็จแล้ว`};
  list.append(el('p',`ข้อมูลสะสมถึง ${c.assessment_date} · การรับทราบไม่ใช่หลักฐานว่าปฏิบัติในอนาคตครบแล้ว`));
  c.obligation_codes.forEach(code=>list.append(el('p',labels[code]||code)));
  if(c.report_confirmation)list.append(el('p',`ผู้ใช้ยืนยันรายงานยอดปัจจุบัน ณ ${c.report_confirmation.confirmed_on} · ไม่ใช่การตรวจระบบ บลจ.`));
  const dl=document.getElementById('rmfBreakdown');dl.replaceChildren();
  [['ยอดซื้อที่จ่ายแล้ว',data.rmf.own_purchase_paid],['เพดานตามฐานเงินได้',data.rmf.percentage_cap],['สิทธิหลังค่าใช้จ่าย',data.rmf.claimed],['ยอดเกินสิทธิ',data.rmf.excess]].forEach(([label,value])=>dl.append(row(label,baht(value))));
}
