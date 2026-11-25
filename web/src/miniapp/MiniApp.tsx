import { useEffect, useMemo, useState } from "react";
import { ApiError, createClient, euro, fmtDateTime, fmtTime, parisDay } from "../lib/api";
import type { Booking, Category, ProDetail, SearchResponse, SearchResult, Service, Slot } from "../lib/types";

const api = createClient("ub_token");

interface TelegramWebApp {
  initData: string;
  ready: () => void;
  expand: () => void;
  HapticFeedback?: { notificationOccurred: (t: string) => void };
}
const tg = (window as unknown as { Telegram?: { WebApp?: TelegramWebApp } }).Telegram?.WebApp;

type View = { name: "home" } | { name: "pro"; id: number } | { name: "bookings" };

const PRESETS: [string, string][] = [
  ["now", "Maintenant"], ["1h", "Dans l'heure"], ["3h", "Dans les 3 h"], ["today", "Aujourd'hui"], ["tomorrow", "Demain"],
];

export default function MiniApp() {
  const [view, setView] = useState<View>({ name: "home" });
  const [authed, setAuthed] = useState<boolean>(!!api.token);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    tg?.ready();
    tg?.expand();
    if (tg?.initData) {
      api.post<{ access_token: string }>("/auth/telegram", { init_data: tg.initData })
        .then((r) => { api.setToken(r.access_token); setAuthed(true); })
        .catch((e) => setAuthError(e.message));
    }
  }, []);

  return (
    <div className="mx-auto min-h-screen max-w-xl px-4 pb-24 pt-4">
      <header className="mb-4 flex items-center justify-between">
        <button className="text-lg font-bold" onClick={() => setView({ name: "home" })}>📅 Universal Booking</button>
        <button className="btn-ghost" onClick={() => setView({ name: "bookings" })}>Mes RDV</button>
      </header>
      {authError && <p className="card mb-3 text-sm text-red-600">Connexion Telegram impossible : {authError}</p>}
      {!tg?.initData && !authed && (
        <p className="card mb-3 text-sm muted">Ouvrez cette page depuis le bot Telegram pour réserver. La recherche reste accessible.</p>
      )}
      {view.name === "home" && <Home onOpen={(id) => setView({ name: "pro", id })} />}
      {view.name === "pro" && <ProPage id={view.id} authed={authed} onBack={() => setView({ name: "home" })}
                                       onBooked={() => setView({ name: "bookings" })} />}
      {view.name === "bookings" && <MyBookings authed={authed} />}
    </div>
  );
}

function Home({ onOpen }: { onOpen: (id: number) => void }) {
  const [text, setText] = useState("");
  const [categories, setCategories] = useState<Category[]>([]);
  const [openCat, setOpenCat] = useState<Category | null>(null);
  const [resp, setResp] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pos, setPos] = useState<{ lat: number; lon: number } | null>(null);
  const [previous, setPrevious] = useState<Record<string, unknown> | null>(null);

  useEffect(() => { api.get<Category[]>("/categories").then(setCategories).catch(() => setCategories([])); }, []);

  async function run(p: Promise<SearchResponse>) {
    setLoading(true); setError(null);
    try { const r = await p; setResp(r); if (r.understood) setPrevious(r.understood); }
    catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  }
  const natural = (t: string) => run(api.post<SearchResponse>("/search/natural", { text: t, previous, ...(pos ?? {}) }));
  const byCategory = (slug: string, available?: string) =>
    run(api.get<SearchResponse>("/search", { category: slug, available, lat: pos?.lat, lon: pos?.lon, radius_km: 20 }));

  function locate() {
    navigator.geolocation?.getCurrentPosition((p) => setPos({ lat: p.coords.latitude, lon: p.coords.longitude }),
      () => setError("Position indisponible"));
  }

  return (
    <div className="space-y-4">
      <form className="card space-y-3" onSubmit={(e) => { e.preventDefault(); if (text.trim()) natural(text); }}>
        <label className="text-sm font-medium" htmlFor="q">Que recherchez-vous ?</label>
        <textarea id="q" className="input min-h-[72px]" value={text} onChange={(e) => setText(e.target.value)}
                  placeholder="Ex : un plombier à Paris disponible demain, coiffeur homme à moins de 30 €…" />
        <div className="flex flex-wrap gap-2">
          <button className="btn-primary" disabled={loading}>{loading ? "Recherche…" : "🔎 Rechercher"}</button>
          <button type="button" className="btn-ghost" onClick={locate}>{pos ? "📍 Position OK" : "📍 Autour de moi"}</button>
          {previous && <button type="button" className="btn-ghost" onClick={() => { setPrevious(null); setResp(null); }}>Nouvelle recherche</button>}
        </div>
        {previous && <p className="text-xs muted">Astuce : écrivez « plutôt samedi » ou « moins de 50 € » pour affiner.</p>}
      </form>

      <section>
        <h2 className="mb-2 text-sm font-semibold muted">⚡ Disponible maintenant</h2>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {PRESETS.map(([k, label]) => (
            <button key={k} className="btn-ghost whitespace-nowrap"
                    onClick={() => run(api.get<SearchResponse>("/search", { available: k, urgent: k === "now", lat: pos?.lat, lon: pos?.lon, radius_km: 20, sort: "soonest" }))}>
              {label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold muted">📂 Catégories</h2>
        <div className="grid grid-cols-2 gap-2">
          {(openCat ? openCat.children : categories).map((c) => (
            <button key={c.id} className="card text-left text-sm hover:ring-2 hover:ring-brand"
                    onClick={() => (c.children.length ? setOpenCat(c) : byCategory(c.slug))}>
              <span className="mr-1">{c.icon}</span>{c.names.fr}
            </button>
          ))}
        </div>
        {openCat && <button className="btn-ghost mt-2" onClick={() => setOpenCat(null)}>⬅️ Toutes les catégories</button>}
      </section>

      {error && <p className="card text-sm text-red-600">{error}</p>}
      {resp && (
        <section className="space-y-3">
          {resp.summary && <p className="text-sm"><b>J'ai compris :</b> {resp.summary}</p>}
          <p className="text-sm muted">{resp.total} professionnel(s)</p>
          {resp.results.map((r) => <ResultCard key={r.professional.id} r={r} onOpen={onOpen} />)}
          {resp.total === 0 && <p className="card text-sm">Aucun professionnel disponible ne correspond. Élargissez la zone ou les dates.</p>}
        </section>
      )}
    </div>
  );
}

function Stars({ avg, count }: { avg: number; count: number }) {
  return <span className="text-sm">{count ? `⭐ ${avg.toFixed(1)} (${count})` : "Nouveau"}</span>;
}

function ResultCard({ r, onOpen }: { r: SearchResult; onOpen: (id: number) => void }) {
  const p = r.professional;
  return (
    <article className="card space-y-2">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h3 className="font-semibold">{p.business_name} {p.is_verified && <span title="Vérifié">✅</span>}</h3>
          <Stars avg={p.rating_avg} count={p.rating_count} />
        </div>
        {r.sponsored && <span className="rounded-full bg-black/5 px-2 py-0.5 text-xs muted dark:bg-white/10">Sponsorisé</span>}
      </div>
      {p.description && <p className="line-clamp-2 text-sm muted">{p.description}</p>}
      <p className="text-sm">📍 {p.city}{r.distance_km !== null && ` · ${r.distance_km.toFixed(1)} km`}
        {r.travel_minutes && ` · ≈ ${r.travel_minutes} min (estimation)`}</p>
      {r.reference_service && <p className="text-sm">💶 {r.reference_service.name} : {euro(r.reference_service.price_cents)}</p>}
      <p className="text-sm">
        🗓 {r.next_slots.length ? r.next_slots.map((s) => `${fmtDateTime(s.start)}`).slice(0, 2).join(" · ")
          : r.on_duty ? "🚨 Intervention urgente possible" : "Pas de créneau sur la période"}
      </p>
      <div className="flex gap-2">
        <button className="btn-primary" onClick={() => onOpen(p.id)}>Voir / Réserver</button>
      </div>
    </article>
  );
}

function ProPage({ id, authed, onBack, onBooked }: { id: number; authed: boolean; onBack: () => void; onBooked: () => void }) {
  const [pro, setPro] = useState<ProDetail | null>(null);
  const [service, setService] = useState<Service | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { api.get<ProDetail>(`/professionals/${id}`).then(setPro).catch((e) => setError(e.message)); }, [id]);
  if (error) return <p className="card text-red-600">{error}</p>;
  if (!pro) return <p className="muted">Chargement…</p>;
  const days = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];
  return (
    <div className="space-y-4">
      <button className="btn-ghost" onClick={onBack}>⬅️ Retour</button>
      <section className="card space-y-2">
        <h1 className="text-xl font-bold">{pro.business_name} {pro.is_verified && "✅"}</h1>
        <Stars avg={pro.rating_avg} count={pro.rating_count} /> <span className="text-sm muted">· {pro.completed_count} prestations</span>
        {pro.description && <p className="text-sm">{pro.description}</p>}
        <p className="text-sm">📍 {[pro.address, pro.postal_code, pro.city].filter(Boolean).join(", ")}</p>
        {pro.work_mode !== "on_site" && <p className="text-sm">🚗 Se déplace jusqu'à {pro.service_radius_km} km</p>}
        {pro.phone && <p className="text-sm">📞 {pro.phone}</p>}
        <details className="text-sm"><summary className="cursor-pointer">🕒 Horaires</summary>
          <ul className="mt-1">{days.map((d, i) => <li key={d}>{d} : {pro.hours[String(i)]?.join(", ") || "fermé"}</li>)}</ul>
        </details>
      </section>
      <section className="card space-y-2">
        <h2 className="font-semibold">Prestations</h2>
        {pro.services.map((s) => (
          <button key={s.id} onClick={() => setService(s)}
                  className={`flex w-full items-center justify-between rounded-xl border px-3 py-2 text-left text-sm ${service?.id === s.id ? "border-brand ring-2 ring-brand" : "border-gray-200 dark:border-gray-700"}`}>
            <span>{s.name} <span className="muted">· {s.duration_min} min{s.location === "at_client" ? " · à domicile" : ""}</span></span>
            <span className="font-medium">{euro(s.price_cents)}</span>
          </button>
        ))}
      </section>
      {service && <BookingPicker pro={pro} service={service} authed={authed} onBooked={onBooked} />}
    </div>
  );
}

function BookingPicker({ pro, service, authed, onBooked }: { pro: ProDetail; service: Service; authed: boolean; onBooked: () => void }) {
  const [slots, setSlots] = useState<Slot[]>([]);
  const [day, setDay] = useState<string | null>(null);
  const [slot, setSlot] = useState<Slot | null>(null);
  const [address, setAddress] = useState("");
  const [note, setNote] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = () => api.get<Slot[]>(`/professionals/${pro.id}/availability`, { service_id: service.id, days: 14 })
    .then((s) => { setSlots(s); setDay((d) => d ?? (s[0] ? parisDay(s[0].start) : null)); });
  useEffect(() => { setSlot(null); setDay(null); load(); }, [service.id]); // eslint-disable-line react-hooks/exhaustive-deps

  const byDay = useMemo(() => {
    const m = new Map<string, Slot[]>();
    slots.forEach((s) => { const d = parisDay(s.start); m.set(d, [...(m.get(d) ?? []), s]); });
    return m;
  }, [slots]);

  async function confirm() {
    if (!slot) return;
    setBusy(true); setStatus(null);
    try {
      const b = await api.post<Booking>("/me/bookings", {
        professional_id: pro.id, service_id: service.id, start_at: slot.start,
        address: service.location === "at_client" ? address : undefined, client_note: note || undefined,
      });
      tg?.HapticFeedback?.notificationOccurred("success");
      setStatus(`✅ Réservation ${b.reference} ${b.status === "confirmed" ? "confirmée" : "envoyée (en attente de validation)"}`);
      setTimeout(onBooked, 1500);
    } catch (e) {
      const err = e as ApiError;
      setStatus(err.status === 409 ? "😕 Ce créneau vient d'être pris. Choisissez-en un autre." : `Erreur : ${err.message}`);
      setSlot(null); load();
    } finally { setBusy(false); }
  }

  const fmtDay = (d: string) => new Intl.DateTimeFormat("fr-FR", { weekday: "short", day: "numeric", month: "short", timeZone: "UTC" }).format(new Date(`${d}T12:00:00Z`));

  return (
    <section className="card space-y-3">
      <h2 className="font-semibold">Choisissez un créneau</h2>
      {!slots.length && <p className="text-sm muted">Aucun créneau libre sur les 14 prochains jours.</p>}
      <div className="flex gap-2 overflow-x-auto pb-1">
        {[...byDay.keys()].map((d) => (
          <button key={d} onClick={() => { setDay(d); setSlot(null); }}
                  className={`whitespace-nowrap rounded-xl px-3 py-2 text-sm ${d === day ? "bg-brand text-white" : "bg-black/5 dark:bg-white/10"}`}>
            {fmtDay(d)}
          </button>
        ))}
      </div>
      <div className="grid grid-cols-4 gap-2">
        {(day ? byDay.get(day) ?? [] : []).map((s) => (
          <button key={s.start} onClick={() => setSlot(s)}
                  className={`rounded-lg px-2 py-2 text-sm ${slot?.start === s.start ? "bg-brand text-white" : "bg-black/5 dark:bg-white/10"}`}>
            {fmtTime(s.start)}{s.freed ? " 🔥" : ""}
          </button>
        ))}
      </div>
      {slot && (
        <div className="space-y-2">
          {service.location === "at_client" && (
            <input className="input" placeholder="Adresse d'intervention" value={address} onChange={(e) => setAddress(e.target.value)} />
          )}
          <input className="input" placeholder="Note pour le professionnel (facultatif, pas de données médicales)"
                 value={note} onChange={(e) => setNote(e.target.value)} maxLength={500} />
          <p className="text-sm">🧾 {service.name} · {fmtDateTime(slot.start)} · {euro(service.price_cents)}</p>
          <button className="btn-primary w-full" disabled={busy || !authed || (service.location === "at_client" && address.length < 5)}
                  onClick={confirm}>
            {authed ? "✅ Confirmer la réservation" : "Ouvrez depuis Telegram pour réserver"}
          </button>
        </div>
      )}
      {status && <p className="text-sm">{status}</p>}
    </section>
  );
}

function MyBookings({ authed }: { authed: boolean }) {
  const [items, setItems] = useState<Booking[] | null>(null);
  const [history, setHistory] = useState(false);
  const load = () => api.get<Booking[]>("/me/bookings", { upcoming: !history }).then(setItems).catch(() => setItems([]));
  useEffect(() => { if (authed) load(); }, [authed, history]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!authed) return <p className="card text-sm">Ouvrez l'application depuis Telegram pour voir vos rendez-vous.</p>;
  const labels: Record<string, string> = { pending: "⏳ En attente", confirmed: "✅ Confirmé", cancelled: "❌ Annulé", completed: "🏁 Terminé", refused: "🚫 Refusé" };
  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <button className={history ? "btn-ghost" : "btn-primary"} onClick={() => setHistory(false)}>À venir</button>
        <button className={history ? "btn-primary" : "btn-ghost"} onClick={() => setHistory(true)}>Historique</button>
      </div>
      {items?.length === 0 && <p className="card text-sm muted">Aucun rendez-vous.</p>}
      {items?.map((b) => (
        <article key={b.id} className="card space-y-1 text-sm">
          <div className="flex justify-between"><b>{b.service_name}</b><span>{labels[b.status] ?? b.status}</span></div>
          <p>🗓 {fmtDateTime(b.start_at)}</p>
          <p className="muted">Réf. {b.reference} · {euro(b.price_cents)}</p>
          {["pending", "confirmed"].includes(b.status) && new Date(b.start_at) > new Date() && (
            <button className="btn-ghost" onClick={async () => {
              if (confirm("Annuler ce rendez-vous ?")) { await api.post(`/me/bookings/${b.id}/cancel`, { reason: "Annulé depuis la Mini App" }); load(); }
            }}>Annuler</button>
          )}
        </article>
      ))}
    </div>
  );
}
