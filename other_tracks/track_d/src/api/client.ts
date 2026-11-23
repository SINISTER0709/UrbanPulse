import axios from 'axios';
export const MOCK =
  import.meta.env.VITE_USE_MOCK === 'true' ||
  (typeof window !== 'undefined' && window.location.hostname.includes('github.io'));
const http = axios.create({ baseURL: import.meta.env.VITE_API_URL || '/api' });
http.interceptors.request.use(c=>{const t=localStorage.getItem('up_token');if(t)c.headers.Authorization='Bearer '+t;return c});
const wait=(v:any)=>new Promise<any>(r=>setTimeout(()=>r(v),150));const iso=(h:number)=>new Date(Date.now()-h*36e5).toISOString();
const mk=(id:string,category:string,severity:string,score:number,urgent:boolean,status:string,summary:string,lat:number,lng:number,h:number,b:any,reports:any[]=[],dept?:string)=>({id,category,severity,priority:severity.toLowerCase(),priority_score:score,urgent_review_flag:urgent,score_breakdown:b,status,summary_text:summary,location:{latitude:lat,longitude:lng},created_at:iso(h),reports:[{id:'rpt_'+id.slice(-3),description:summary,latitude:lat,longitude:lng,status:'triaged',created_at:iso(h)},...reports],assignments:dept?[{id:'asgn_'+id,department_name:dept,status:'pending'}]:[],admin_reviews:[]});
let M:any[]=[
mk('inc_a2333ca716','road_damage','Critical',75,true,'open','Large pothole outside ABC School causing traffic problems.',28.4506,77.5842,3,{S:40,R:20,T:0,L:15,E:0},[{id:'rpt_105',description:'Big hole on the road in front of ABC school',latitude:28.4509,longitude:77.5844,status:'duplicate_pending_review',created_at:iso(2)}]),
mk('inc_b1','streetlight_electrical','Critical',71,true,'in_progress','Exposed live wire hanging near the bus stop.',28.447,77.575,9,{S:40,R:10,T:8,L:13,E:0},[],'Electricity Board'),
mk('inc_b2','water_supply','High',49,false,'open','No water supply for two days in Sector 12.',28.46,77.57,30,{S:30,R:12,T:12,L:3,E:0}),
mk('inc_b3','garbage_sanitation','Medium',38.5,false,'assigned','Garbage not collected for a week near the market.',28.452,77.59,50,{S:20,R:12,T:6,L:0.5,E:0},[],'Sanitation & Waste Management'),
mk('inc_b4','drainage_flooding','Medium',34,false,'resolved','Drain overflowing onto the road after rain.',28.455,77.58,75,{S:20,R:10,T:4,L:0,E:0},[],'Stormwater Drainage Department'),
mk('inc_b5','streetlight_electrical','Low',18,false,'open','Streetlight flickering on park road.',28.449,77.583,20,{S:10,R:5,T:3,L:0,E:0})];
const tracked:any={};let n=200;
function normIncident(i:any){if(!i)return i;const lat=i.location?.latitude??i.latitude??28.4506;const lng=i.location?.longitude??i.longitude??77.5842;const p=(i.priority?.value||i.priority||'medium').toLowerCase();return{...i,priority:p,location:{latitude:lat,longitude:lng},reports:i.reports||i.linked_reports||[],assignments:i.assignments||[],admin_reviews:i.admin_reviews||[]};}
export const api={
async login(email:string,password:string){if(MOCK){const role=email.startsWith('admin')?'Admin':email.startsWith('dep')?'Department':'Citizen';localStorage.setItem('up_token','mock');return wait({email,full_name:email.split('@')[0],role})}
const {data}=await http.post('/auth/login',{email,password});localStorage.setItem('up_token',data.access_token);return (await http.get('/auth/me')).data},
async register(b:any){if(!MOCK)await http.post('/auth/register',b)},
async submit(fd:FormData){if(MOCK){const id='rpt_'+(++n);tracked[id]='received_pending_ai';return wait({report_id:id,status:'received_pending_ai',created_at:new Date().toISOString()})}
try{return (await http.post('/complaints',fd)).data}catch(e:any){if(e?.response?.status===401||!fd.has('photo'))throw e;fd.delete('photo');return (await http.post('/complaints',fd)).data}},
async track(id:string){if(MOCK){const r=M.flatMap(i=>i.reports).find((r:any)=>r.id===id);if(tracked[id])return wait({id,status:tracked[id]});if(r)return wait(r);throw new Error('nf')}return (await http.get('/complaints/'+id)).data},
async myComplaints(){if(MOCK)return wait(M.flatMap(i=>i.reports));const res=(await http.get('/complaints')).data;return res?.items||[];},
async incidents(p:any={}){if(MOCK){return wait(M.filter(i=>(!p.category||i.category===p.category)&&(!p.priority||i.priority===p.priority)&&(!p.status||i.status===p.status)&&(!p.urgent_only||i.urgent_review_flag)).sort((a,b)=>b.priority_score-a.priority_score))}
const q:any={};Object.entries(p).forEach(([k,v])=>v&&(q[k]=v));const res=(await http.get('/incidents',{params:q})).data;return (Array.isArray(res)?res:[]).map(normIncident)},
async incident(id:string){if(MOCK)return wait(structuredClone(M.find(i=>i.id===id)));const res=(await http.get('/incidents/'+id)).data;return normIncident(res)},
async override(id:string,b:any){if(MOCK){const i=M.find(x=>x.id===id);Object.assign(i,{severity:b.severity,category:b.category,priority:b.severity.toLowerCase()});i.admin_reviews.push({id:'rev_'+Date.now(),decision:'override',notes:b.reason});return wait(1)}return http.patch(`/incidents/${id}/override`,b)},
async setStatus(id:string,b:any){if(MOCK){M.find(x=>x.id===id).status=b.status;return wait(1)}return http.patch(`/incidents/${id}/status`,b)},
async assign(id:string,b:any){if(MOCK){const i=M.find(x=>x.id===id);i.assignments=[{id:'asgn_'+Date.now(),department_name:b.department_name,status:'pending'}];if(i.status==='open'||i.status==='triaged')i.status='assigned';return wait(1)}return http.post(`/incidents/${id}/assign`,b)},
async duplicate(id:string,b:any){if(MOCK){const i=M.find(x=>x.id===id);i.reports.find((r:any)=>r.id===b.report_id).status=b.is_duplicate?'triaged':'received_pending_ai';return wait(1)}return http.post(`/incidents/${id}/duplicate`,b)},
async brief(id:string){if(MOCK)return wait({brief:'Place warning cones and dispatch road crew within 24h.',sources:[{doc:'road_sop.pdf',excerpt:'Section 4.2: High-severity school-zone potholes require barricading and repair within 24 hours.'}],disclaimer:'Advisory only, not municipal policy.'});return (await http.post(`/incidents/${id}/action-brief`)).data}};
