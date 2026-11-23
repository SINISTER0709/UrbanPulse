import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  ChevronDown,
  ShieldAlert,
  Copy,
  UserPlus,
  RefreshCw,
  CheckCircle2,
  FolderCheck,
} from 'lucide-react';
import { api } from '../api/client';
import { useAuth } from '../context/Auth';
import { CatIcon, SevPill, StatusPill, UrgentPill, ScoreBreakdown } from '../components/ui';
import {
  OverrideModal,
  AssignModal,
  StatusModal,
  DuplicatesModal,
} from '../components/Actions';
import {
  CATEGORIES,
  CATEGORY_LABELS,
  PRIORITIES,
  STATUSES,
  fmt,
} from '../types/urbanpulse';

const MODALS: any = {
  override: OverrideModal,
  assign: AssignModal,
  status: StatusModal,
  dups: DuplicatesModal,
};

export default function Queue() {
  const { user } = useAuth();
  const [sp] = useSearchParams();
  const [f, setF] = useState<any>({
    category: '',
    priority: '',
    status: '',
    urgent_only: sp.get('urgent') === '1',
  });
  const [d, setD] = useState<any[]>([]);
  const [open, setOpen] = useState('');
  const [m, setM] = useState<any>(null);
  const [showResolved, setShowResolved] = useState(true);

  const load = () => api.incidents(f).then(setD);
  useEffect(() => {
    load();
  }, [f]);
  const s = (k: string) => (e: any) => setF({ ...f, [k]: e.target.value });

  const sorted = [...d].sort(
    (a, b) => +b.urgent_review_flag - +a.urgent_review_flag || b.priority_score - a.priority_score
  );

  // If status is explicitly filtered, show all matching.
  // Otherwise, split into Active vs Resolved/Closed to keep the active queue clean and uncluttered.
  const isStatusFiltered = Boolean(f.status);
  const activeList = isStatusFiltered
    ? sorted
    : sorted.filter((i) => !['resolved', 'closed'].includes(i.status));
  const resolvedList = isStatusFiltered
    ? []
    : sorted.filter((i) => ['resolved', 'closed'].includes(i.status));

  const Modal = m && MODALS[m.k];

  const renderCard = (i: any, isResolvedSection = false) => (
    <div
      key={i.id}
      className={`card p-3 transition-all ${
        i.urgent_review_flag && !['resolved', 'closed'].includes(i.status)
          ? 'border-l-4 border-l-red-600'
          : isResolvedSection
          ? 'bg-slate-50/70 border-slate-200'
          : ''
      }`}
    >
      <div className="flex flex-wrap items-center gap-3">
        <CatIcon c={i.category} />
        <div className="flex-1 min-w-[12rem]">
          <Link
            to={'/admin/map/' + i.id}
            className="font-semibold text-sm hover:underline hover:text-brand transition"
          >
            {i.summary_text}
          </Link>
          <p className="text-xs text-slate-500">
            {CATEGORY_LABELS[i.category as keyof typeof CATEGORY_LABELS]} ·{' '}
            {i.assignments?.[0]?.department_name || 'Unassigned'} · {fmt(i.created_at)}
          </p>
        </div>
        {i.urgent_review_flag && !['resolved', 'closed'].includes(i.status) && <UrgentPill />}
        <SevPill v={i.severity} />
        <StatusPill v={i.status} />
        <button
          className="px-2.5 py-1 rounded-full bg-brand-light text-brand text-sm font-bold flex items-center gap-1 hover:bg-brand-light/80 transition"
          aria-expanded={open === i.id}
          aria-label={`Score ${i.priority_score}, show breakdown`}
          onClick={() => setOpen(open === i.id ? '' : i.id)}
        >
          {i.priority_score}
          <ChevronDown
            size={14}
            className={`transition-transform duration-200 ${open === i.id ? 'rotate-180' : ''}`}
          />
        </button>
      </div>

      {open === i.id && (
        <div className="mt-3">
          <ScoreBreakdown i={i} />
        </div>
      )}

      <div className="flex flex-wrap gap-2 mt-3">
        <button className="btn-s !py-1" onClick={() => setM({ k: 'override', i })}>
          <ShieldAlert size={14} />
          Override
        </button>
        <button className="btn-s !py-1" onClick={() => setM({ k: 'dups', i })}>
          <Copy size={14} />
          Triage duplicates
        </button>
        <button className="btn-s !py-1" onClick={() => setM({ k: 'assign', i })}>
          <UserPlus size={14} />
          Assign
        </button>
        <button className="btn-s !py-1" onClick={() => setM({ k: 'status', i })}>
          <RefreshCw size={14} />
          Update status
        </button>
      </div>
    </div>
  );

  return (
    <div className="space-y-4 max-w-6xl mx-auto">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold">Priority queue</h1>
        <span className="text-xs text-slate-500 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm">
          {activeList.length} active · {resolvedList.length} resolved / closed
        </span>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap gap-2 items-center bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
        <select
          aria-label="Category"
          className="inp !w-auto"
          value={f.category}
          onChange={s('category')}
        >
          <option value="">All categories</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {CATEGORY_LABELS[c]}
            </option>
          ))}
        </select>
        <select
          aria-label="Priority"
          className="inp !w-auto"
          value={f.priority}
          onChange={s('priority')}
        >
          <option value="">All priorities</option>
          {PRIORITIES.map((p) => (
            <option key={p}>{p}</option>
          ))}
        </select>
        <select
          aria-label="Status"
          className="inp !w-auto"
          value={f.status}
          onChange={s('status')}
        >
          <option value="">All statuses</option>
          {STATUSES.map((p) => (
            <option key={p} value={p}>
              {p.replace('_', ' ')}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-2 text-sm font-medium ml-2 cursor-pointer">
          <input
            type="checkbox"
            checked={f.urgent_only}
            onChange={(e) => setF({ ...f, urgent_only: e.target.checked })}
          />
          Urgent only
        </label>
      </div>

      {/* Active Issues Section */}
      <div className="space-y-2.5 stagger">
        {!isStatusFiltered && (
          <div className="flex items-center justify-between pt-1">
            <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Active Issues ({activeList.length})
            </h2>
          </div>
        )}
        {activeList.map((i) => renderCard(i, false))}
        {!activeList.length && (
          <div className="card p-8 text-center text-slate-500">
            <p className="font-semibold text-sm">No active issues match these filters.</p>
            <p className="text-xs text-slate-400 mt-1">All issues may be resolved or under different criteria.</p>
          </div>
        )}
      </div>

      {/* Resolved & Closed Issues Section (Separated so report queue is uncluttered) */}
      {!isStatusFiltered && resolvedList.length > 0 && (
        <div className="mt-8 pt-6 border-t border-slate-200 space-y-3">
          <div className="flex items-center justify-between bg-slate-100/80 px-4 py-2.5 rounded-xl border border-slate-200">
            <div className="flex items-center gap-2">
              <FolderCheck size={18} className="text-green-600" />
              <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Resolved & Closed Issues ({resolvedList.length})
              </h2>
            </div>
            <button
              onClick={() => setShowResolved(!showResolved)}
              className="text-xs font-semibold text-brand hover:underline flex items-center gap-1 cursor-pointer"
            >
              {showResolved ? 'Hide section' : 'Show section'}
              <ChevronDown
                size={14}
                className={`transition-transform duration-200 ${
                  showResolved ? 'rotate-180' : ''
                }`}
              />
            </button>
          </div>

          {showResolved && (
            <div className="space-y-2.5 stagger">
              {resolvedList.map((i) => renderCard(i, true))}
            </div>
          )}
        </div>
      )}

      {m && Modal && (
        <Modal
          inc={m.i}
          onClose={() => setM(null)}
          onDone={() => {
            m.k !== 'dups' && setM(null);
            load();
          }}
        />
      )}
    </div>
  );
}
