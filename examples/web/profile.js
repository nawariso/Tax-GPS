'use strict';
// UI records preserve explicit caller facts; no eligibility or financial formulas here.
const profileScalars = ['personal_eligible','mortgage_interest','mortgage_eligible','required_coverage','existing_coverage','other_income','retirement_usage'];
const profileRecords = {parents:[],children:[],debts:[],commitments:[]};
const yesNo = [['unknown','ยังไม่ทราบ'],['true','ใช่ · ตรวจเงื่อนไขแล้ว'],['false','ไม่ใช่']];
const recordSchema = {
  parents:[['relationship','ความสัมพันธ์ / รหัสรายการ','text'],['eligible','เข้าเงื่อนไขสิทธิ','select',yesNo]],
  children:[['child_id','รหัสบุตร (ไม่ต้องใช้ชื่อจริง)','text'],['order','ลำดับบุตรตามกฎหมาย','number'],['birth_year','ปีเกิด ค.ศ.','number'],['legally_eligible','เข้าเงื่อนไขสิทธิ','select',yesNo]],
  debts:[['debt_id','รหัสหนี้','text'],['category','ประเภทหนี้','select',[['','เลือกประเภท'],['CREDIT_CARD','บัตรเครดิต'],['PERSONAL_LOAN','สินเชื่อส่วนบุคคล'],['CASH_CARD','บัตรกดเงินสด'],['AUTO_LOAN','รถยนต์'],['MORTGAGE','บ้าน'],['STUDENT_LOAN','การศึกษา'],['OTHER','อื่น ๆ']]],['balance','ยอดคงเหลือ (บาท)','decimal'],['apr_percent','ดอกเบี้ย APR ต่อปี (%)','decimal'],['minimum_payment','ยอดจ่ายขั้นต่ำต่อเดือน (บาท)','decimal'],['secured','มีหลักประกัน','select',yesNo]],
  commitments:[['need_id','รหัสภาระจ่าย','text'],['amount','จำนวนเงิน (บาท)','decimal'],['due_date','วันที่ต้องจ่าย','date'],['mandatory','เป็นรายจ่ายที่จำเป็นต้องจ่าย','select',yesNo],['description','รายละเอียด (ไม่ใส่ข้อมูลระบุตัวบุคคล)','text']],
};
let recordSequence = 0;
function addRecord(group, values = {}) {
  const card = el('fieldset',undefined,'profile-record');
  const legend = el('legend',`${{parents:'บิดา / มารดา',children:'บุตร',debts:'หนี้',commitments:'ภาระจ่าย'}[group]} · รายการใหม่`);
  card.append(legend);
  const fields = {};
  recordSchema[group].forEach(([key,label,type,options])=>{
    const wrapper=el('div');
    const input=el(type==='select'?'select':'input');
    input.id=`profile-record-${++recordSequence}`;
    const title=el('label',label); title.htmlFor=input.id;
    if(type==='select') options.forEach(([value,text])=>{const option=el('option',text);option.value=value;input.append(option);});
    else {input.type=type==='date'?'date':'text';input.inputMode=['number','decimal'].includes(type)?'decimal':'text';}
    input.value=values[key] ?? (type==='select'?options[0][0]:'');
    input.required=key!=='description';
    fields[key]=input;
    wrapper.append(title,input);card.append(wrapper);
  });
  const entry={card,fields};profileRecords[group].push(entry);
  const remove=el('button','ลบรายการนี้','secondary');remove.type='button';
  remove.addEventListener('click',()=>{profileRecords[group]=profileRecords[group].filter(item=>item!==entry);card.remove();invalidateResults();});
  card.append(remove);$(group+'Records').append(card);invalidateResults();
  return entry;
}
function collectProfile() {
  const profile=Object.fromEntries(profileScalars.map(key=>[key,$(key).value]));
  Object.entries(profileRecords).forEach(([group,records])=>{
    profile[group]=records.map(entry=>Object.fromEntries(Object.entries(entry.fields).map(([key,input])=>[key,input.value])));
  });
  return profile;
}
function resetProfile() {
  const defaults={personal_eligible:'true',mortgage_interest:'0',mortgage_eligible:'false',required_coverage:'',existing_coverage:'',other_income:'0',retirement_usage:'0'};
  Object.entries(defaults).forEach(([key,value])=>{$(key).value=value;});
  Object.keys(profileRecords).forEach(group=>{profileRecords[group]=[];$(group+'Records').replaceChildren();});
}
function initProfile() {
  Object.keys(profileRecords).forEach(group=>{$('add'+group).addEventListener('click',()=>addRecord(group));});
}
function updateGroupSummaries() {
  const rights = profileRecords.parents.length + profileRecords.children.length;
  const obligations = profileRecords.debts.length + profileRecords.commitments.length;
  $('rightsCount').textContent = `${rights} รายการครอบครัว · ${$('mortgage_eligible').value === 'true' ? 'ใช้สิทธิดอกเบี้ยบ้าน' : $('mortgage_eligible').value === 'unknown' ? 'สิทธิดอกเบี้ยบ้านยังไม่ทราบ' : 'ไม่ใช้สิทธิดอกเบี้ยบ้าน'}`;
  $('financeCount').textContent = `${obligations} รายการหนี้ / ภาระจ่าย · ${$('assets').value === '' || $('expenses').value === '' ? 'สภาพคล่องยังไม่ทราบ' : 'ตรวจตามข้อมูลที่กรอก'}`;
}
function renderProfile(data) {
  const dl=$('profileBreakdown');dl.replaceChildren();
  const financial=data.financial;
  [['เงินสำรองฉุกเฉินขั้นต่ำ',financial.emergency_reserve_floor],['ภาระจ่ายจำเป็นในช่วงใกล้',financial.near_term_committed_cash],['ยอดหนี้ดอกเบี้ยสูง',financial.critical_debt_balance],['ช่องว่างความคุ้มครองชีวิต',financial.protection_gap]].forEach(([label,value])=>dl.append(row(label,baht(value))));
  const names={personal:'ส่วนตัว',social_security:'ประกันสังคม',parents:'บิดา / มารดา',children:'บุตร',mortgage_interest:'ดอกเบี้ยบ้าน',total:'รวมสิทธิเดิม'};
  Object.entries(data.tax_state.allowances).forEach(([key,value])=>dl.append(row(names[key]||key,baht(value))));
  $('financialReasons').textContent=financial.reason_codes.map(code=>({CRITICAL_DEBT_PRESENT:'พบหนี้ดอกเบี้ยสูง: engine ไม่เปิดให้ใช้เงินใหม่เพื่อภาษี',LIQUIDITY_COMMITMENT_CONFLICT:'กันเงินสำหรับภาระจ่ายใกล้ถึงกำหนดก่อน',PROTECTION_GAP:'มีช่องว่างความคุ้มครอง: ข้อมูลประกอบ ไม่ใช่คำแนะนำซื้อประกัน',PROTECTION_NEED_UNKNOWN:'ยังไม่ทราบความคุ้มครองที่ต้องการ',FINANCIAL_INPUT_REQUIRED:'สภาพคล่องยังไม่ครบ ต้องตรวจข้อมูลเพิ่ม',EMERGENCY_FUND_PRESERVED:'รักษาเงินสำรองฉุกเฉินตาม policy',EMERGENCY_FUND_BELOW_FLOOR:'เงินสำรองต่ำกว่าขั้นต่ำ',NO_SPENDABLE_SURPLUS:'ไม่มีสภาพคล่องสำหรับใช้เงินเพิ่ม',ZERO_ESSENTIAL_EXPENSE_BASE:'ค่าใช้จ่ายจำเป็นระบุเป็นศูนย์'}[code]||code)).join(' · ');
}
