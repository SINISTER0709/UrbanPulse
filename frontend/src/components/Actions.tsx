import {useState,useEffect} from 'react';import {Modal,Field} from './ui';import {api} from '../api/client';import {CATEGORIES,CATEGORY_LABELS,CATEGORY_DEPARTMENTS,SEVERITIES,STATUSES,DEPARTMENTS,dist,fmt} from '../types/urbanpulse';
function Form({title,onClose,onSubmit,ok,label,children}:any){const [busy,setBusy]=useState(false);const [err,setErr]=useState('');
return <Modal title={title} onClose={onClose}>{children}{err&&<p role="alert" className="text-sm text-red-600">{err}</p>}<div className="flex justify-end gap-2 pt-1"><button className="btn-s" onClick={onClose}>Cancel</button>
<button className="btn-p" disabled={!ok||busy} onClick={async()=>{setBusy(true);try{await onSubmit()}catch{setErr('Request failed. Please try again.');setBusy(false)}}}>{busy?'Saving…':label}</button></div></Modal>}
export function OverrideModal({inc,onClose,onDone}:any){const [sev,setSev]=useState(inc.severity);const [cat,setCat]=useState(inc.category);const [reason,setReason]=useState('');
return <Form title="Override AI decision" label="Apply override" onClose={onClose} ok={reason.trim().length>3} onSubmit={async()=>{await api.override(inc.id,{severity:sev,category:cat,reason});onDone()}}>
<Field label="New severity"><select className="inp" value={sev} onChange={e=>setSev(e.target.value)}>{SEVERITIES.map(s=><option key={s}>{s}</option>)}</select></Field>
<Field label="New category"><select className="inp" value={cat} onChange={e=>setCat(e.target.value)}>{CATEGORIES.map(c=><option key={c} value={c}>{CATEGORY_LABELS[c]}</option>)}</select></Field>
<p className="text-xs text-slate-500">Suggested department: {CATEGORY_DEPARTMENTS[cat as keyof typeof CATEGORY_DEPARTMENTS]}</p>
<Field label="Reason for override (required, audited)"><textarea rows={3} className="inp" placeholder="e.g. School bus route blocked during morning rush" value={reason} onChange={e=>setReason(e.target.value)}/></Field></Form>}
export function AssignModal({inc,onClose,onDone}:any){const [d,setD]=useState(inc.assignments?.[0]?.department_name||CATEGORY_DEPARTMENTS[inc.category as keyof typeof CATEGORY_DEPARTMENTS]);const [notes,setNotes]=useState('');
return <Form title="Assign department" label="Assign" onClose={onClose} ok onSubmit={async()=>{await api.assign(inc.id,{department_name:d,notes});onDone()}}>
<Field label="Department"><select className="inp" value={d} onChange={e=>setD(e.target.value)}>{DEPARTMENTS.map(x=><option key={x}>{x}</option>)}</select></Field>
<Field label="Notes"><input className="inp" value={notes} onChange={e=>setNotes(e.target.value)} placeholder="e.g. Assigned to North Ward repair crew"/></Field></Form>}
export function StatusModal({inc,onClose,onDone}:any){const [s,setS]=useState(inc.status==='triaged'?'assigned':inc.status);const [notes,setNotes]=useState('');
return <Form title="Update status" label="Update" onClose={onClose} ok={s!==inc.status} onSubmit={async()=>{await api.setStatus(inc.id,{status:s,notes});onDone()}}>
<Field label="Status"><select className="inp" value={s} onChange={e=>setS(e.target.value)}>{STATUSES.filter(x=>x!=='triaged').map(x=><option key={x} value={x}>{x.replace('_',' ')}</option>)}</select></Field>
<Field label="Notes"><input className="inp" value={notes} onChange={e=>setNotes(e.target.value)} placeholder="e.g. Field repair team dispatched"/></Field></Form>}
export function DuplicatesModal({inc,onClose,onDone}:any){const [d,setD]=useState<any>(null);const load=()=>api.incident(inc.id).then(setD);useEffect(()=>{load()},[]);
const c=d?.reports?.filter((r:any,idx:number)=>r.status==='duplicate_pending_review'||(idx>0&&r.status!=='duplicate_confirmed'))||[];
const act=async(r:string,ok:boolean)=>{await api.duplicate(inc.id,{report_id:r,is_duplicate:ok});onDone();load()};
return <Modal title="Duplicate review" wide onClose={onClose}>{!d?<p>Loading…</p>:!c.length?<p className="text-sm text-slate-600">No duplicate candidates are waiting for review.</p>:c.map((r:any)=><div key={r.id} className="border rounded-lg p-3 space-y-2">
<div className="grid sm:grid-cols-2 gap-3 text-sm"><div className="bg-slate-50 rounded p-2"><p className="text-xs font-semibold text-slate-500">THIS INCIDENT</p><p>{d.summary_text}</p><p className="text-xs text-slate-500">{d.address?`${d.address} · `:''}{d.location?.latitude??d.latitude}, {d.location?.longitude??d.longitude} · {fmt(d.created_at)}</p></div>
<div className="bg-attn-light rounded p-2"><p className="text-xs font-semibold text-attn">CANDIDATE {r.id}</p><p>{r.description}</p><p className="text-xs text-slate-500">{r.address?`${r.address} · `:''}{r.latitude}, {r.longitude} · {dist(d.location||d,r)} m away · {fmt(r.created_at)}</p></div></div>
<div className="flex gap-2"><button className="btn-p" onClick={()=>act(r.id,true)}>Confirm duplicate</button><button className="btn-s" onClick={()=>act(r.id,false)}>Reject / split</button></div></div>)}</Modal>}
