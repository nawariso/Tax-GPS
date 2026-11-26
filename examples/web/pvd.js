'use strict';
// Explicit answers only; all readiness and arithmetic come from the domain.
const pvdGroups = {
  pvd:['employee_paid','wage_basis','fund_name','registered_fund','credited_in_tax_year','single_employer','single_fund','ordinary_article_rate','normal_remittance'],
  other_rights:['rmf','thai_esg','thai_esgx','gpf','teacher_fund','nsf','pension_insurance','ssf','spouse_pvd_claim','other_retirement_right'],
  fund_history:['prior_conditional_rights','disposal_withdrawal_transfer','retirement_or_recapture','ltf_carryforward']
};
function collectPvdProfile() {
  const data=Object.fromEntries(Object.entries(pvdGroups).map(([group,names])=>[
    group,Object.fromEntries(names.map(name=>[name,document.getElementById(group+'_'+name).value]))
  ]));
  const presence=document.getElementById('pvd_presence').value;
  data.pvd.employee_paid=presence==='false'?'0':presence==='true'?data.pvd.employee_paid:'';
  return data;
}
function updatePvdVisibility() {
  const positive=document.getElementById('pvd_presence').value==='true';
  document.getElementById('pvdDetails').hidden=!positive;
  document.getElementById('budget').required=!(positive||document.getElementById('other_rights_rmf').value==='true');
}
function renderPvdProfile(data) {
  const pvd=data.pvd;
  document.getElementById('pvd_presence').value=pvd?.employee_paid==='0'?'false':pvd?.employee_paid?'true':'';
  Object.entries(pvdGroups).forEach(([group,names])=>names.forEach(name=>{
    document.getElementById(group+'_'+name).value=data[group]?.[name]??'';
  }));
  updatePvdVisibility();
}
function initPvdProfile(onChange) {
  document.getElementById('pvd_presence').addEventListener('change',updatePvdVisibility);
  ['other_rights','fund_history'].forEach(group=>{
    document.getElementById(group+'None').addEventListener('click',()=>{
      pvdGroups[group].filter(name=>!(group==='other_rights'&&name==='rmf')).forEach(name=>{document.getElementById(group+'_'+name).value='false';});
      onChange();
    });
  });
  updatePvdVisibility();
}
function pvdFieldForFact(fact) {
  if(fact==='pvd.employee_paid')return document.getElementById(document.getElementById('pvd_presence').value==='true'?'pvd_employee_paid':'pvd_presence');
  for(const [group,names] of Object.entries(pvdGroups)) {
    if(fact===group)return document.getElementById(group+'_'+names[0]);
    const name=fact.startsWith(group+'.')?fact.slice(group.length+1):null;
    if(names.includes(name))return document.getElementById(group+'_'+name);
  }
  return null;
}
