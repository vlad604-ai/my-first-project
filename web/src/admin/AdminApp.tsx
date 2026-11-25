import { useCallback, useEffect, useState } from "react";
import { NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import { createClient, euro, fmtDateTime } from "../lib/api";
import type { Booking, Category, Page, Review, User } from "../lib/types";
import { DailyBars } from "./BarChart";

export const adminApi = createClient("ub_admin_token");

interface Stats {
  users_total: number; users_new: number; professionals: Record<string, number>; bookings: Record<string, number>;
  bookings_total: number; gmv_cents: number; reviews_pending: number; reports_open: number; quote_requests: number;
  daily_bookings: { day: string; count: number }[]; top_categories: { slug: string; name: string; bookings: number }[];
}

function useLoad<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const reload = useCallback(() => { fn().then(setData).catch((e) => setError(e.message)); }, deps); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(reload, [reload]);
  return { data, error, reload };
}

export default function AdminApp() {
  const [token, setToken] = useState(adminApi.token);
  if (!token) return <Login onLogin={(t) => { adminApi.setToken(t); setToken(t); }} />;
  const links: [string, string][] = [
    ["", "📊 Tableau de bord"], ["pros", "💼 Professionnels"], ["reviews", "⭐ Avis"], ["reports", "🚩 Signalements"],
    ["bookings", "📅 Réservations"], ["users", "👥 Utilisateurs"], ["categories", "📂 Catégories"],
    ["billing", "💶 Abonnements"], ["audit", "🧾 Journal"],
  ];
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      <nav className="flex gap-1 overflow-x-auto p-3 md:w-56 md:flex-col" style={{ background: "var(--surface-1)" }}>
        <p className="mb-2 hidden px-2 font-bold md:block">🛡 Admin</p>
        {links.map(([to, label]) => (
          <NavLink key={to} to={to} end className={({ isActive }) =>
            `whitespace-nowrap rounded-lg px-3 py-2 text-sm ${isActive ? "bg-brand text-white" : "hover:bg-black/5 dark:hover:bg-white/10"}`}>
            {label}
          </NavLink>
        ))}
        <button className="mt-auto rounded-lg px-3 py-2 text-left text-sm muted"
                onClick={() => { adminApi.setToken(null); setToken(null); }}>Se déconnecter</button>
      </nav>
      <main className="flex-1 space-y-4 p-4 md:p-6">
        <Routes>
          <Route index element={<Dashboard />} />
          <Route path="pros" element={<Pros />} />
          <Route path="reviews" element={<Reviews />} />
          <Route path="reports" element={<Reports />} />
          <Route path="bookings" element={<Bookings />} />
          <Route path="users" element={<Users />} />
          <Route path="categories" element={<Categories />} />
          <Route path="billing" element={<Billing />} />
          <Route path="audit" element={<Audit />} />
          <Route path="*" element={<Navigate to="" />} />
        </Routes>
      </main>
    </div>
  );
}

function Login({ onLogin }: { onLogin: (token: string) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <form className="card w-full max-w-sm space-y-3" onSubmit={async (e) => {
        e.preventDefault();
        try {
          const r = await adminApi.post<{ access_token: string; user: User }>("/auth/login", { email, password });
          if (!r.user.is_admin) { setError("Ce compte n'est pas administrateur."); return; }
          onLogin(r.access_token);
        } catch (err) { setError((err as Error).message); }
      }}>
        <h1 className="text-lg font-bold">🛡 Administration</h1>
        <input className="input" type="email" placeholder="E-mail" value={email} onChange={(e) => setEmail(e.target.value)} required />
        <input className="input" type="password" placeholder="Mot de passe" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="btn-primary w-full">Se connecter</button>
      </form>
    </div>
  );
}

function Tile({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="card">
      <p className="text-xs muted">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      {sub && <p className="text-xs muted">{sub}</p>}
    </div>
  );
}

function Dashboard() {
  const [days, setDays] = useState(30);
  const { data: s, error } = useLoad(() => adminApi.get<Stats>("/admin/stats", { days }), [days]);
  const nav = useNavigate();
  if (error) return <p className="text-red-600">{error}</p>;
  if (!s) return <p className="muted">Chargement…</p>;
  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Tableau de bord</h1>
        <select className="input" style={{ width: "auto" }} value={days} onChange={(e) => setDays(Number(e.target.value))}>
          {[7, 30, 90, 365].map((d) => <option key={d} value={d}>{d} derniers jours</option>)}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Tile label="Utilisateurs" value={s.users_total} sub={`+${s.users_new} sur la période`} />
        <Tile label="Professionnels actifs" value={s.professionals.active ?? 0} sub={`${s.professionals.pending ?? 0} en attente de validation`} />
        <Tile label="Réservations" value={s.bookings_total} sub={`${s.bookings.cancelled ?? 0} annulées`} />
        <Tile label="Volume réservé" value={euro(s.gmv_cents)} sub="confirmées + terminées" />
      </div>
      <div className="grid gap-3 lg:grid-cols-3">
        <div className="lg:col-span-2"><DailyBars data={s.daily_bookings} title="Réservations par jour" /></div>
        <div className="card space-y-2">
          <p className="text-sm font-semibold">À traiter</p>
          <button className="btn-ghost w-full justify-between" onClick={() => nav("pros")}>Pros à valider <b>{s.professionals.pending ?? 0}</b></button>
          <button className="btn-ghost w-full justify-between" onClick={() => nav("reviews")}>Avis à modérer <b>{s.reviews_pending}</b></button>
          <button className="btn-ghost w-full justify-between" onClick={() => nav("reports")}>Signalements <b>{s.reports_open}</b></button>
          <p className="pt-2 text-sm font-semibold">Catégories les plus réservées</p>
          <ul className="text-sm">{s.top_categories.map((c) => <li key={c.slug} className="flex justify-between"><span>{c.name}</span><span className="muted">{c.bookings}</span></li>)}</ul>
          <p className="text-sm muted">Demandes de devis : {s.quote_requests}</p>
        </div>
      </div>
    </>
  );
}

interface AdminPro {
  id: number; business_name: string; category: string; city: string | null; work_mode: string; status: string;
  is_verified: boolean; rating_avg: number; rating_count: number; completed_count: number; description: string | null; phone: string | null;
}

function Pros() {
  const [status, setStatus] = useState("pending");
  const [q, setQ] = useState("");
  const { data, reload } = useLoad(() => adminApi.get<Page<AdminPro>>("/admin/professionals", { status, q }), [status, q]);
  const act = async (id: number, s: string, verify?: boolean) => {
    await adminApi.post(`/admin/professionals/${id}/status`, { status: s, verify }); reload();
  };
  return (
    <>
      <h1 className="text-xl font-bold">Professionnels</h1>
      <div className="flex flex-wrap gap-2">
        {["pending", "active", "suspended", "rejected", ""].map((s) => (
          <button key={s} className={status === s ? "btn-primary" : "btn-ghost"} onClick={() => setStatus(s)}>{s || "tous"}</button>
        ))}
        <input className="input max-w-xs" placeholder="Rechercher un nom…" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <p className="text-sm muted">{data?.total ?? 0} résultat(s)</p>
      <div className="space-y-2">
        {data?.items.map((p) => (
          <div key={p.id} className="card flex flex-wrap items-center justify-between gap-2">
            <div className="min-w-0">
              <p className="font-semibold">{p.business_name} {p.is_verified && "✅"} <span className="text-xs muted">#{p.id} · {p.status}</span></p>
              <p className="text-sm muted">{p.category} · {p.city ?? "-"} · {p.work_mode} · ⭐ {p.rating_avg.toFixed(1)} ({p.rating_count}) · {p.completed_count} prestations</p>
              {p.description && <p className="line-clamp-1 text-sm">{p.description}</p>}
            </div>
            <div className="flex flex-wrap gap-2">
              {p.status !== "active" && <button className="btn-primary" onClick={() => act(p.id, "active")}>Valider</button>}
              {!p.is_verified && <button className="btn-ghost" onClick={() => act(p.id, "active", true)}>Valider + badge</button>}
              {p.status === "active" && <button className="btn-ghost" onClick={() => act(p.id, "suspended")}>Suspendre</button>}
              {p.status === "pending" && <button className="btn-ghost" onClick={() => act(p.id, "rejected")}>Refuser</button>}
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

function Reviews() {
  const [status, setStatus] = useState("pending");
  const { data, reload } = useLoad(() => adminApi.get<Review[]>("/admin/reviews", { status }), [status]);
  return (
    <>
      <h1 className="text-xl font-bold">Modération des avis</h1>
      <div className="flex gap-2">{["pending", "published", "rejected"].map((s) => (
        <button key={s} className={status === s ? "btn-primary" : "btn-ghost"} onClick={() => setStatus(s)}>{s}</button>))}
      </div>
      {data?.length === 0 && <p className="muted">Rien à afficher.</p>}
      {data?.map((r) => (
        <div key={r.id} className="card space-y-1">
          <p>{"⭐".repeat(r.rating)} <span className="text-xs muted">pro #{r.professional_id} · {fmtDateTime(r.created_at)}</span></p>
          <p className="text-sm">{r.comment ?? <i className="muted">Sans commentaire</i>}</p>
          {r.moderation_reason && <p className="text-xs muted">Motif de mise en attente : {r.moderation_reason}</p>}
          <div className="flex gap-2">
            {r.status !== "published" && <button className="btn-primary" onClick={async () => { await adminApi.post(`/admin/reviews/${r.id}/moderate`, undefined, { approve: true }); reload(); }}>Publier</button>}
            {r.status !== "rejected" && <button className="btn-ghost" onClick={async () => { await adminApi.post(`/admin/reviews/${r.id}/moderate`, undefined, { approve: false }); reload(); }}>Rejeter</button>}
          </div>
        </div>
      ))}
    </>
  );
}

function Reports() {
  const { data, reload } = useLoad(() => adminApi.get<{ id: number; target_type: string; target_id: string; reason: string; created_at: string }[]>("/admin/reports"));
  return (
    <>
      <h1 className="text-xl font-bold">Signalements ouverts</h1>
      {data?.length === 0 && <p className="muted">Aucun signalement 🎉</p>}
      {data?.map((r) => (
        <div key={r.id} className="card space-y-1">
          <p className="text-sm"><b>{r.target_type}</b> #{r.target_id} · <span className="muted">{fmtDateTime(r.created_at)}</span></p>
          <p className="text-sm">{r.reason}</p>
          <div className="flex gap-2">
            <button className="btn-primary" onClick={async () => { await adminApi.post(`/admin/reports/${r.id}`, undefined, { status: "resolved" }); reload(); }}>Traité</button>
            <button className="btn-ghost" onClick={async () => { await adminApi.post(`/admin/reports/${r.id}`, undefined, { status: "dismissed" }); reload(); }}>Ignorer</button>
            {r.target_type === "professional" && <button className="btn-ghost" onClick={async () => { await adminApi.post(`/admin/professionals/${r.target_id}/status`, { status: "suspended" }); reload(); }}>Suspendre le pro</button>}
          </div>
        </div>
      ))}
    </>
  );
}

function Bookings() {
  const [status, setStatus] = useState("");
  const { data } = useLoad(() => adminApi.get<Page<Booking>>("/admin/bookings", { status, limit: 100 }), [status]);
  return (
    <>
      <h1 className="text-xl font-bold">Réservations</h1>
      <div className="flex flex-wrap gap-2">{["", "pending", "confirmed", "completed", "cancelled", "refused"].map((s) => (
        <button key={s} className={status === s ? "btn-primary" : "btn-ghost"} onClick={() => setStatus(s)}>{s || "toutes"}</button>))}
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="muted"><tr><th className="text-left">Réf.</th><th className="text-left">Prestation</th><th className="text-left">Date</th><th>Statut</th><th className="text-right">Prix</th></tr></thead>
          <tbody>{data?.items.map((b) => (
            <tr key={b.id} className="border-t border-black/5 dark:border-white/10">
              <td className="py-1 font-mono">{b.reference}</td><td>{b.service_name}</td><td>{fmtDateTime(b.start_at)}</td>
              <td className="text-center">{b.status}</td><td className="text-right">{euro(b.price_cents)}</td>
            </tr>))}
          </tbody>
        </table>
        <p className="mt-2 text-xs muted">{data?.total ?? 0} réservation(s)</p>
      </div>
    </>
  );
}

function Users() {
  const [q, setQ] = useState("");
  const { data, reload } = useLoad(() => adminApi.get<Page<User>>("/admin/users", { q }), [q]);
  return (
    <>
      <h1 className="text-xl font-bold">Utilisateurs</h1>
      <input className="input max-w-xs" placeholder="Nom, @username, e-mail…" value={q} onChange={(e) => setQ(e.target.value)} />
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="muted"><tr><th className="text-left">#</th><th className="text-left">Nom</th><th className="text-left">Telegram</th><th>Inscrit</th><th /></tr></thead>
          <tbody>{data?.items.map((u) => (
            <tr key={u.id} className="border-t border-black/5 dark:border-white/10">
              <td className="py-1">{u.id}</td><td>{[u.first_name, u.last_name].filter(Boolean).join(" ")} {u.is_admin && "🛡"}</td>
              <td>{u.username ? `@${u.username}` : u.telegram_id ?? "-"}</td>
              <td className="text-center">{new Date(u.created_at).toLocaleDateString("fr-FR")}</td>
              <td className="text-right">{!u.is_admin && (
                <button className="btn-ghost" onClick={async () => { await adminApi.post(`/admin/users/${u.id}/ban`, undefined, { banned: !u.is_banned }); reload(); }}>
                  {u.is_banned ? "Réactiver" : "Suspendre"}
                </button>)}
              </td>
            </tr>))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Categories() {
  const { data, reload } = useLoad(() => adminApi.get<Category[]>("/admin/categories"));
  const [form, setForm] = useState({ slug: "", fr: "", en: "", icon: "", parent_id: "", keywords: "", mode: "on_site", quotes: false });
  const [error, setError] = useState<string | null>(null);
  const roots = (data ?? []).filter((c) => c.parent_id === null);
  return (
    <>
      <h1 className="text-xl font-bold">Catégories & métiers</h1>
      <form className="card grid gap-2 md:grid-cols-4" onSubmit={async (e) => {
        e.preventDefault(); setError(null);
        try {
          await adminApi.post("/admin/categories", {
            slug: form.slug, names: { fr: form.fr, en: form.en || form.fr }, icon: form.icon || null,
            parent_id: form.parent_id ? Number(form.parent_id) : null, default_work_mode: form.mode, supports_quotes: form.quotes,
            keywords: form.keywords.split(",").map((k) => k.trim().toLowerCase()).filter(Boolean),
          });
          setForm({ ...form, slug: "", fr: "", en: "", icon: "", keywords: "" }); reload();
        } catch (err) { setError((err as Error).message); }
      }}>
        <input className="input" placeholder="slug (ex: toiletteur)" value={form.slug} onChange={(e) => setForm({ ...form, slug: e.target.value })} required />
        <input className="input" placeholder="Nom FR" value={form.fr} onChange={(e) => setForm({ ...form, fr: e.target.value })} required />
        <input className="input" placeholder="Nom EN" value={form.en} onChange={(e) => setForm({ ...form, en: e.target.value })} />
        <input className="input" placeholder="Icône (emoji)" value={form.icon} onChange={(e) => setForm({ ...form, icon: e.target.value })} />
        <select className="input" value={form.parent_id} onChange={(e) => setForm({ ...form, parent_id: e.target.value })}>
          <option value="">— Catégorie racine —</option>
          {roots.map((r) => <option key={r.id} value={r.id}>{r.icon} {r.names.fr}</option>)}
        </select>
        <select className="input" value={form.mode} onChange={(e) => setForm({ ...form, mode: e.target.value })}>
          <option value="on_site">En établissement</option><option value="mobile">Se déplace</option><option value="both">Les deux</option>
        </select>
        <input className="input md:col-span-2" placeholder="Mots-clés IA, séparés par des virgules" value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })} />
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={form.quotes} onChange={(e) => setForm({ ...form, quotes: e.target.checked })} /> Demandes de devis</label>
        <button className="btn-primary">Ajouter</button>
        {error && <p className="text-sm text-red-600 md:col-span-4">{error}</p>}
      </form>
      <div className="grid gap-3 md:grid-cols-2">
        {roots.map((r) => (
          <div key={r.id} className="card">
            <p className="font-semibold">{r.icon} {r.names.fr} <span className="text-xs muted">{r.slug}</span></p>
            <ul className="mt-1 text-sm">{(data ?? []).filter((c) => c.parent_id === r.id).map((c) => (
              <li key={c.id}>{c.icon} {c.names.fr} <span className="text-xs muted">· {c.default_work_mode}{c.supports_quotes ? " · devis" : ""}{c.is_health ? " · santé" : ""}</span></li>))}
            </ul>
          </div>
        ))}
      </div>
    </>
  );
}

interface Plan { id: number; code: string; name: string; price_cents_monthly: number; commission_bps: number; ranking_boost: number; features: Record<string, unknown>; is_active: boolean }

function Billing() {
  const { data, reload } = useLoad(() => adminApi.get<Plan[]>("/admin/plans"));
  const { data: commission, reload: reloadCommission } = useLoad(() => adminApi.get<{ default_bps?: number }>("/admin/settings/commission"));
  const [bps, setBps] = useState("");
  return (
    <>
      <h1 className="text-xl font-bold">Abonnements & commissions</h1>
      <p className="text-sm muted">Le paiement n'est pas activé dans cette version (PAYMENTS_ENABLED=false) : ces formules sont configurables et prêtes à être branchées sur un prestataire de paiement.</p>
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        {data?.map((p) => (
          <div key={p.id} className="card space-y-1">
            <p className="font-semibold">{p.name} <span className="text-xs muted">{p.code}</span></p>
            <p className="text-2xl font-semibold">{euro(p.price_cents_monthly)}<span className="text-sm muted">/mois</span></p>
            <p className="text-sm muted">Commission : {(p.commission_bps / 100).toFixed(1)} % · Boost : {p.ranking_boost}</p>
            <pre className="whitespace-pre-wrap text-xs muted">{JSON.stringify(p.features)}</pre>
            <button className="btn-ghost" onClick={async () => { await adminApi.post("/admin/plans", { ...p, is_active: !p.is_active }); reload(); }}>
              {p.is_active ? "Désactiver" : "Activer"}
            </button>
          </div>
        ))}
      </div>
      <form className="card flex flex-wrap items-end gap-2" onSubmit={async (e) => {
        e.preventDefault(); await adminApi.put("/admin/settings/commission", { default_bps: Number(bps) }); setBps(""); reloadCommission();
      }}>
        <label className="text-sm">Commission par défaut sur les réservations payantes (points de base, 100 = 1 %)
          <input className="input mt-1" type="number" min={0} max={5000} value={bps} onChange={(e) => setBps(e.target.value)}
                 placeholder={String(commission?.default_bps ?? 0)} required />
        </label>
        <button className="btn-primary">Enregistrer</button>
        <span className="text-sm muted">Actuelle : {((commission?.default_bps ?? 0) / 100).toFixed(2)} %</span>
      </form>
    </>
  );
}

function Audit() {
  const { data } = useLoad(() => adminApi.get<{ id: number; actor_user_id: number | null; action: string; entity: string; entity_id: string | null; created_at: string }[]>("/admin/audit"));
  return (
    <>
      <h1 className="text-xl font-bold">Journal d'audit</h1>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="muted"><tr><th className="text-left">Date</th><th className="text-left">Action</th><th className="text-left">Entité</th><th className="text-left">Acteur</th></tr></thead>
          <tbody>{data?.map((a) => (
            <tr key={a.id} className="border-t border-black/5 dark:border-white/10">
              <td className="py-1">{fmtDateTime(a.created_at)}</td><td className="font-mono">{a.action}</td>
              <td>{a.entity} {a.entity_id}</td><td>{a.actor_user_id ?? "système"}</td>
            </tr>))}
          </tbody>
        </table>
      </div>
    </>
  );
}
