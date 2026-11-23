import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Check, Clock, MapPin, ChevronRight, AlertCircle, RefreshCw, Image } from 'lucide-react';
import { api } from '../api/client';
import { CatIcon, StatusPill } from '../components/ui';
import { CATEGORY_LABELS, fmt } from '../types/urbanpulse';

const STEPS = ['Received', 'Triaged & clustered', 'Department dispatched', 'Resolved'];
const IDX: Record<string, number> = {
  received_pending_ai: 0,
  processing: 0,
  open: 1,
  triaged: 1,
  duplicate_pending_review: 1,
  assigned: 2,
  in_progress: 2,
  resolved: 3,
  closed: 3,
};

export default function Track() {
  const { id } = useParams();
  const nav = useNavigate();
  const [q, setQ] = useState(id || '');
  const [r, setR] = useState<any>();
  const [myList, setMyList] = useState<any[]>([]);
  const [loadingList, setLoadingList] = useState(true);

  const fetchMyComplaints = () => {
    setLoadingList(true);
    api.myComplaints()
      .then((items) => setMyList(items || []))
      .catch(() => setMyList([]))
      .finally(() => setLoadingList(false));
  };

  useEffect(() => {
    fetchMyComplaints();
  }, []);

  useEffect(() => {
    setR(undefined);
    if (id) {
      setQ(id);
      api.track(id).then(setR).catch(() => setR(null));
    }
  }, [id]);

  const effectiveStatus = r ? (r.incident_status || r.status || 'open') : 'open';
  const i = IDX[effectiveStatus] ?? 0;

  return (
    <div className="space-y-6">
      {/* Search Input Bar */}
      <div className="card p-3 flex gap-2">
        <input
          className="inp"
          aria-label="Report ID"
          placeholder="Enter report ID, e.g. rpt_104"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && q && nav('/track/' + q.trim())}
        />
        <button className="btn-p" onClick={() => q && nav('/track/' + q.trim())}>Track</button>
      </div>

      {r === null && (
        <div className="card p-4 text-center text-red-600 text-sm flex items-center justify-center gap-2">
          <AlertCircle size={16} /> No report found with ID "{q}".
        </div>
      )}

      {/* Progress Stepper Card */}
      {r && (
        <div className="card p-5 space-y-4 border-2 border-brand/20 anim-fade">
          <div className="flex flex-wrap items-start justify-between gap-2 border-b pb-3">
            <div>
              <p className="font-mono font-bold text-navy text-lg">{r.id || r.report_id}</p>
              <p className="text-xs text-slate-500">Submitted on {fmt(r.created_at)}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded font-medium">
                {CATEGORY_LABELS[r.category as keyof typeof CATEGORY_LABELS] || 'Civic Issue'}
              </span>
              <StatusPill v={effectiveStatus} />
            </div>
          </div>
          {r.description && <p className="text-sm font-medium text-slate-800">{r.description}</p>}
          {r.address && (
            <p className="text-xs text-slate-500 flex items-center gap-1">
              <MapPin size={13} className="text-slate-400 shrink-0" /> {r.address}
            </p>
          )}

          {/* Uploaded Photos Section if any */}
          {r.photos && r.photos.length > 0 && (
            <div className="pt-2 border-t border-slate-100">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                <Image size={13} /> Uploaded Photos ({r.photos.length})
              </p>
              <div className="flex flex-wrap gap-2">
                {r.photos.map((p: string, idx: number) => (
                  <a
                    key={idx}
                    href={p}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block w-20 h-20 rounded-lg overflow-hidden border border-slate-200 bg-slate-50 hover:opacity-90 transition shadow-sm"
                  >
                    <img
                      src={p}
                      alt={`Photo ${idx + 1}`}
                      className="w-full h-full object-cover"
                      onError={(e: any) => {
                        if (!e.target.src.includes('127.0.0.1:8080')) {
                          e.target.src = 'http://127.0.0.1:8080' + p;
                        }
                      }}
                    />
                  </a>
                ))}
              </div>
            </div>
          )}

          <div className="pt-2">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Resolution Progress</p>
            <ol className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {STEPS.map((s, k) => (
                <li
                  key={s}
                  className={`p-3 rounded-lg border flex flex-col gap-1.5 transition ${
                    k <= i
                      ? 'bg-green-50 border-green-200 text-green-900'
                      : 'bg-slate-50 border-slate-200 text-slate-400'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={`w-6 h-6 rounded-full grid place-items-center text-xs font-bold ${
                        k <= i ? 'bg-green-600 text-white' : 'bg-slate-200 text-slate-500'
                      }`}
                    >
                      {k <= i ? <Check size={13} /> : k + 1}
                    </span>
                    <span className="text-xs font-bold">{k <= i ? 'Completed' : 'Pending'}</span>
                  </div>
                  <span className={`text-xs ${k <= i ? 'font-medium' : ''}`}>{s}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}

      {/* Citizen's Past Complaints List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold">Your Submitted Complaints</h2>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">{myList.length} total</span>
            <button
              onClick={fetchMyComplaints}
              className="p-1 rounded text-slate-400 hover:text-slate-600 transition"
              title="Refresh"
            >
              <RefreshCw size={13} className={loadingList ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        {loadingList ? (
          <p className="text-sm text-slate-500 py-4">Loading your complaints…</p>
        ) : myList.length === 0 ? (
          <div className="card p-6 text-center text-slate-500 space-y-1">
            <p className="font-semibold text-sm">No complaints submitted yet</p>
            <p className="text-xs">Any reports you file will show up here so you can track them easily.</p>
          </div>
        ) : (
          <div className="space-y-2 stagger">
            {myList.map((item) => {
              const isSelected = r && (r.id === item.id || r.report_id === item.id);
              return (
                <div
                  key={item.id}
                  onClick={() => nav('/track/' + item.id)}
                  className={`card p-3.5 cursor-pointer hover:border-brand/40 hover:shadow-sm transition flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                    isSelected ? 'ring-2 ring-brand border-transparent bg-brand-light/30' : ''
                  }`}
                >
                  <div className="flex items-start gap-3 min-w-0">
                    <CatIcon c={item.category || 'other'} />
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-xs font-bold text-navy">{item.id}</span>
                        <StatusPill v={item.status} />
                      </div>
                      <p className="text-sm font-medium text-slate-800 truncate mt-0.5">
                        {item.description}
                      </p>
                      <div className="flex items-center gap-3 text-xs text-slate-400 mt-1 flex-wrap">
                        <span>{CATEGORY_LABELS[item.category as keyof typeof CATEGORY_LABELS] || 'Civic Issue'}</span>
                        <span>·</span>
                        <span className="flex items-center gap-1"><Clock size={11} /> {fmt(item.created_at)}</span>
                        {item.address && (
                          <>
                            <span>·</span>
                            <span className="truncate max-w-xs flex items-center gap-1"><MapPin size={11} /> {item.address}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="shrink-0 flex items-center gap-2 self-end sm:self-center text-xs font-semibold text-brand">
                    <span>{isSelected ? 'Viewing' : 'View progress'}</span>
                    <ChevronRight size={14} />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
