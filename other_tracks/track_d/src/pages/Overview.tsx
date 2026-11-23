import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  ClipboardList,
  Clock,
  CheckCircle2,
  ChevronDown,
  TrendingUp,
  ShieldAlert,
} from 'lucide-react';
import Notifications from '../components/Notifications';
import { api } from '../api/client';
import { useAuth } from '../context/Auth';
import { CatIcon, SevPill, StatusPill } from '../components/ui';
import { LiveMap, liveState, LIVE_COLORS } from '../components/MapView';
import { CATEGORY_LABELS, DEPARTMENTS, fmt } from '../types/urbanpulse';

const SLA: any = { critical: 24, high: 48, medium: 72, low: 120 };
const age = (i: any) => (Date.now() - new Date(i.created_at).getTime()) / 36e5;
const left = (i: any) => {
  const p = (i.priority?.value || i.priority || 'medium').toLowerCase();
  return (SLA[p] || 72) - age(i);
};
const ageStr = (h: number) =>
  h < 24 ? Math.max(1, Math.round(h)) + 'h' : Math.floor(h / 24) + 'd';
const leftStr = (h: number) =>
  h < 0 ? 'Overdue' : h >= 48 ? Math.floor(h / 24) + 'd left' : Math.round(h) + 'h left';

export default function Overview() {
  const { user } = useAuth();
  const [d, setD] = useState<any[]>([]);
  const [tab, setTab] = useState('all');

  const load = () => api.incidents({}).then(setD);
  useEffect(() => {
    load();
  }, []);

  const act = d.filter((i) => !['resolved', 'closed'].includes(i.status));
  const hpAll = act.filter((i) => ['critical', 'high'].includes((i.priority || '').toLowerCase()));
  const hp = [...hpAll].sort((a, b) => left(a) - left(b)).slice(0, 5);

  const urgentCount = d.filter((i) => i.urgent_review_flag && !['resolved', 'closed'].includes(i.status)).length;
  const openCount = d.filter((i) => i.status === 'open').length;
  const inProgressCount = d.filter((i) => ['in_progress', 'assigned'].includes(i.status)).length;
  const resolvedCount = d.filter((i) => ['resolved', 'closed'].includes(i.status)).length;
  const totalCount = d.length;

  const cnt = (s: string) => d.filter((i) => i.status === s).length;
  const rec = tab === 'all' ? d : d.filter((i) => i.status === tab);

  const K = [
    [
      ShieldAlert,
      'bg-red-50 text-red-600',
      'URGENT ISSUES',
      urgentCount,
      `${urgentCount} require immediate action`,
    ],
    [
      ClipboardList,
      'bg-blue-50 text-blue-600',
      'OPEN ISSUES',
      openCount,
      `${d.filter((i) => i.status === 'open' && age(i) < 168).length} new in the last 7 days`,
    ],
    [
      Clock,
      'bg-amber-50 text-amber-600',
      'IN-PROGRESS',
      inProgressCount,
      `${inProgressCount} actively being addressed`,
    ],
    [
      CheckCircle2,
      'bg-green-50 text-green-600',
      'RESOLVED ISSUES',
      resolvedCount,
      `${resolvedCount} resolved or closed`,
    ],
    [
      TrendingUp,
      'bg-purple-50 text-purple-600',
      'TOTAL ISSUES',
      totalCount,
      `${totalCount} lifetime registered tickets`,
    ],
  ];

  const assign = async (i: any, dep: string) => {
    if (dep) {
      await api.assign(i.id, { department_name: dep, notes: 'Assigned from overview' });
      load();
    }
  };

  const L = [
    ['open', LIVE_COLORS.open, 'Open'],
    ['progress', LIVE_COLORS.progress, 'In progress'],
    ['unassigned', LIVE_COLORS.unassigned, 'Unassigned'],
    ['resolved', LIVE_COLORS.resolved, 'Resolved'],
  ];

  return (
    <div className="space-y-5 max-w-7xl mx-auto">
      <div className="flex justify-between items-start gap-3">
        <div>
          <h1 className="text-2xl font-bold">Operations Center</h1>
          <p className="text-sm text-slate-500">Here's what's happening in your city today.</p>
        </div>
        <div className="flex items-center gap-2">
          <span className="card px-3 py-2 text-sm flex items-center gap-2">
            <Calendar size={16} />
            {new Date().toLocaleDateString('en-IN', {
              weekday: 'long',
              month: 'long',
              day: 'numeric',
            })}
          </span>
          <Notifications />
        </div>
      </div>

      {/* 5 Main Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 stagger">
        {K.map(([I, t, l, v, s]: any) => (
          <div key={l} className="card p-4">
            <span className={`w-9 h-9 rounded-lg grid place-items-center ${t}`}>
              <I size={18} />
            </span>
            <p className="text-[11px] font-semibold tracking-wide text-slate-500 mt-2">{l}</p>
            <p className="text-2xl font-bold">{v}</p>
            <p className="text-xs text-slate-500 flex items-center gap-1 mt-1">
              <TrendingUp size={12} />
              {s}
            </p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-4 stagger">
        {/* High-priority issues list */}
        <section className="card">
          <div className="flex items-center gap-2 p-4 pb-3">
            <h2 className="font-bold">High-priority issues</h2>
            <span className="text-xs font-semibold text-red-600 bg-red-50 px-2 py-0.5 rounded-full">
              ● High
            </span>
            <Link className="ml-auto text-sm text-brand" to="/admin/queue">
              View all
            </Link>
          </div>
          {hp.map((i) => (
            <div key={i.id} className="border-t px-4 py-3 flex items-center gap-3 flex-wrap">
              <CatIcon c={i.category} />
              <div className="flex-1 min-w-[9rem]">
                <Link
                  to={'/admin/map/' + i.id}
                  className="font-semibold text-sm hover:underline hover:text-brand transition"
                >
                  {i.summary_text}
                </Link>
                <p className="text-xs text-slate-500">
                  {i.location?.latitude ?? i.latitude}, {i.location?.longitude ?? i.longitude}
                </p>
              </div>
              <SevPill v={i.severity} />
              <span
                className={`text-xs ${
                  left(i) < 0 ? 'text-red-600 font-semibold' : 'text-slate-600'
                }`}
              >
                {leftStr(left(i))}
              </span>
              <StatusPill v={i.status} />
              <div className="relative">
                <select
                  aria-label={'Assign ' + i.id}
                  className="btn-s !py-1 !pr-7 appearance-none cursor-pointer"
                  value=""
                  onChange={(e) => assign(i, e.target.value)}
                >
                  <option value="">{i.assignments?.[0] ? 'Reassign' : 'Assign'}</option>
                  {DEPARTMENTS.map((x) => (
                    <option key={x}>{x}</option>
                  ))}
                </select>
                <ChevronDown
                  size={12}
                  className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none"
                />
              </div>
            </div>
          ))}
          {!hp.length && (
            <p className="p-4 text-sm text-slate-500 border-t">No high-priority issues right now.</p>
          )}
          <p className="px-4 py-3 border-t text-xs text-slate-500">
            Showing {hp.length ? 1 : 0}–{hp.length} of {hpAll.length} high-priority issues
          </p>
        </section>

        {/* Live map preview */}
        <section className="card p-4 flex flex-col">
          <div className="flex justify-between mb-2">
            <h2 className="font-bold">Live map</h2>
            <Link className="text-sm text-brand" to="/admin/map">
              View full map
            </Link>
          </div>
          <div className="flex-1 min-h-[18rem] rounded-lg overflow-hidden">
            <LiveMap items={d} />
          </div>
          <div className="flex flex-wrap gap-4 text-xs mt-3">
            {L.map(([k, c, l]) => (
              <span key={k} className="flex items-center gap-1.5">
                <i className="w-2.5 h-2.5 rounded-full" style={{ background: c }} />
                {d.filter((i) => liveState(i) === k).length} {l}
              </span>
            ))}
          </div>
        </section>
      </div>

      {/* Recent reports list with tabs */}
      <section className="card p-4">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <h2 className="font-bold mr-3">Recent reports</h2>
          {[
            ['all', 'All', d.length],
            ['open', 'Open', cnt('open')],
            ['in_progress', 'In progress', cnt('in_progress')],
            ['resolved', 'Resolved', cnt('resolved')],
          ].map(([k, l, c]: any) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                tab === k ? 'bg-brand text-white border-brand' : 'bg-white text-slate-600'
              }`}
            >
              {l} {c}
            </button>
          ))}
          <Link to="/admin/queue" className="ml-auto text-sm text-brand">
            View all
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-left text-slate-500 text-xs">
              <tr>
                {['Issue', 'Location', 'Category', 'Status', 'Priority', 'Reported', 'Age'].map(
                  (h) => (
                    <th key={h} className="py-2 pr-3 font-medium">
                      {h}
                    </th>
                  )
                )}
              </tr>
            </thead>
            <tbody>
              {rec.map((i) => (
                <tr key={i.id} className="border-t">
                  <td className="py-2.5 pr-3">
                    <Link className="font-medium hover:underline text-navy" to={'/admin/map/' + i.id}>
                      {i.summary_text}
                    </Link>
                  </td>
                  <td className="pr-3 text-slate-600 whitespace-nowrap">
                    {i.location?.latitude ?? i.latitude}, {i.location?.longitude ?? i.longitude}
                  </td>
                  <td className="pr-3">
                    {CATEGORY_LABELS[i.category as keyof typeof CATEGORY_LABELS]}
                  </td>
                  <td className="pr-3">
                    <StatusPill v={i.status} />
                  </td>
                  <td className="pr-3">
                    <SevPill v={i.severity} />
                  </td>
                  <td className="pr-3 whitespace-nowrap">{fmt(i.created_at)}</td>
                  <td>{ageStr(age(i))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
