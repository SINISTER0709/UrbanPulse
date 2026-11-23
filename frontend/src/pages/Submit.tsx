import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LocateFixed, ImagePlus, CheckCircle2, Copy, X, MapPin } from 'lucide-react';
import LocationSearch from '../components/LocationSearch';
import { LocationPicker } from '../components/MapView';
import { api } from '../api/client';
import { DEFAULT_CENTER } from '../types/urbanpulse';

export default function Submit() {
  const [text, setText] = useState('');
  const [pos, setPos] = useState<[number, number]>(DEFAULT_CENTER);
  const [address, setAddress] = useState('');
  const [geoLoading, setGeoLoading] = useState(false);
  const [photos, setPhotos] = useState<File[]>([]);
  const [ok, setOk] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [done, setDone] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  // Auto reverse-geocode whenever pos changes
  useEffect(() => {
    let active = true;
    setGeoLoading(true);
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${pos[0]}&lon=${pos[1]}`)
      .then((res) => res.json())
      .then((data) => {
        if (active && data?.display_name) {
          setAddress(data.display_name);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (active) setGeoLoading(false);
      });
    return () => {
      active = false;
    };
  }, [pos[0], pos[1]]);

  const gps = () =>
    navigator.geolocation?.getCurrentPosition(
      (p) => setPos([p.coords.latitude, p.coords.longitude]),
      () => setErr('Could not read your location. Drag the pin instead.')
    );

  const handlePhotoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const selected = Array.from(e.target.files);
    setPhotos((prev) => [...prev, ...selected].slice(0, 3));
  };

  const removePhoto = (idx: number) => {
    setPhotos((prev) => prev.filter((_, i) => i !== idx));
  };

  const send = async () => {
    setBusy(true);
    setErr('');
    const fd = new FormData();
    fd.append('description', text);
    fd.append('lat', String(pos[0]));
    fd.append('lng', String(pos[1]));
    fd.append('latitude', String(pos[0]));
    fd.append('longitude', String(pos[1]));
    fd.append('consent', 'true');
    if (address) fd.append('address', address);
    photos.forEach((f) => fd.append('photos', f));
    if (photos[0]) fd.append('photo', photos[0]);

    try {
      setDone(await api.submit(fd));
    } catch {
      setErr('Could not submit. Check your connection and try again.');
    }
    setBusy(false);
  };

  if (done)
    return (
      <div className="card p-6 text-center space-y-3 mt-6">
        <CheckCircle2 className="mx-auto text-green-600" size={44} />
        <h1 className="text-xl font-bold">Complaint received</h1>
        <p className="text-sm text-slate-600">
          Keep this ID to track progress. Analysis continues in the background.
        </p>
        <p className="font-mono text-2xl bg-brand-light text-brand py-3 rounded-lg">
          {done.report_id}
        </p>
        {address && (
          <p className="text-xs text-slate-500 max-w-md mx-auto truncate">
            📍 {address}
          </p>
        )}
        <div className="flex gap-2 justify-center">
          <button
            className="btn-s"
            onClick={() => {
              navigator.clipboard?.writeText(done.report_id);
              setCopied(true);
            }}
          >
            <Copy size={14} />
            {copied ? 'Copied' : 'Copy ID'}
          </button>
          <Link className="btn-p" to={'/track/' + done.report_id}>
            Track status
          </Link>
        </div>
      </div>
    );

  return (
    <div className="card p-4 space-y-4">
      <h1 className="text-xl font-bold">Report a civic problem</h1>
      <label className="block text-sm font-semibold">
        What is the problem?
        <textarea
          rows={3}
          className="inp mt-1 font-normal"
          placeholder="e.g. Large pothole outside ABC School causing traffic problems"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </label>

      <div>
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-semibold">Pin the location</span>
          <button className="btn-s !py-1" onClick={gps}>
            <LocateFixed size={14} />
            My location
          </button>
        </div>
        <div className="mb-2">
          <LocationSearch onPick={(p: any) => setPos(p)} />
        </div>
        <div className="h-56 rounded-lg overflow-hidden border">
          <LocationPicker pos={pos} set={setPos} />
        </div>
        <div className="text-xs text-slate-500 mt-1">
          <p>
            Drag the pin or tap the map. {pos[0].toFixed(5)}, {pos[1].toFixed(5)}
            {geoLoading && <span className="ml-1 text-slate-400">· Fetching address…</span>}
          </p>
          {address && !geoLoading && (
            <p className="text-slate-700 font-medium mt-0.5 flex items-center gap-1 truncate">
              <MapPin size={12} className="text-brand shrink-0" />
              {address}
            </p>
          )}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold">Add photos (optional, up to 3)</span>
          <span className="text-xs text-slate-400">{photos.length}/3 selected</span>
        </div>
        {photos.length > 0 && (
          <div className="flex gap-3 overflow-x-auto py-1">
            {photos.map((p, idx) => (
              <div key={idx} className="relative shrink-0">
                <img
                  src={URL.createObjectURL(p)}
                  alt={`Upload ${idx + 1}`}
                  className="h-16 w-16 object-cover rounded-lg border border-slate-200"
                />
                <button
                  type="button"
                  className="absolute -top-1.5 -right-1.5 bg-red-600 text-white rounded-full p-0.5 shadow hover:bg-red-700 transition"
                  onClick={() => removePhoto(idx)}
                  title="Remove photo"
                >
                  <X size={12} />
                </button>
              </div>
            ))}
          </div>
        )}
        {photos.length < 3 && (
          <label className="btn-s cursor-pointer inline-flex items-center gap-1.5 text-xs">
            <ImagePlus size={15} />
            {photos.length === 0 ? 'Add photo' : 'Add another photo'}
            <input
              type="file"
              multiple
              accept=".jpg,.jpeg,.png,.webp"
              className="sr-only"
              onChange={handlePhotoSelect}
            />
          </label>
        )}
      </div>

      <label className="flex gap-2 text-sm">
        <input
          type="checkbox"
          checked={ok}
          onChange={(e) => setOk(e.target.checked)}
        />
        I consent to processing my report data for municipal resolution under DPDP regulations.
      </label>

      {err && (
        <p role="alert" className="text-sm text-red-600">
          {err}
        </p>
      )}

      <button
        className="btn-p w-full"
        disabled={busy || !ok || text.trim().length < 5}
        onClick={send}
      >
        {busy ? 'Submitting…' : 'Submit complaint'}
      </button>
    </div>
  );
}
