import React from "react";
import ReactDOM from "react-dom/client";
import { Activity, Bell, Database, Globe2, ShieldCheck, Server } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import { api, connectDashboardSocket } from "./services/api";
import type { DashboardSummary, Device, Incident, Metric } from "./types/netpulse";
import "./styles.css";

const statusClass: Record<string, string> = {
  up: "text-ok bg-emerald-50 border-emerald-200",
  degraded: "text-warn bg-amber-50 border-amber-200",
  down: "text-bad bg-red-50 border-red-200",
  unknown: "text-slate-600 bg-slate-50 border-slate-200"
};

function App() {
  const [token, setToken] = React.useState(localStorage.getItem("netpulse_token") || "");
  const [summary, setSummary] = React.useState<DashboardSummary | null>(null);
  const [devices, setDevices] = React.useState<Device[]>([]);
  const [metrics, setMetrics] = React.useState<Metric[]>([]);
  const [incidents, setIncidents] = React.useState<Incident[]>([]);

  React.useEffect(() => {
    if (!token) return;
    localStorage.setItem("netpulse_token", token);
    Promise.all([
      api<DashboardSummary>("/api/v1/monitoring/summary", token),
      api<Device[]>("/api/v1/monitoring/devices", token),
      api<Metric[]>("/api/v1/monitoring/metrics", token),
      api<Incident[]>("/api/v1/incidents", token)
    ]).then(([nextSummary, nextDevices, nextMetrics, nextIncidents]) => {
      setSummary(nextSummary);
      setDevices(nextDevices);
      setMetrics(nextMetrics.reverse());
      setIncidents(nextIncidents);
    });
    const close = connectDashboardSocket(token, setSummary);
    return close;
  }, [token]);

  if (!token) return <Login onToken={setToken} />;

  const chartData = metrics.slice(-50).map((metric) => ({
    time: new Date(metric.created_at).toLocaleTimeString(),
    latency: metric.latency_ms || 0,
    packetLoss: metric.packet_loss
  }));

  return (
    <main className="min-h-screen bg-slate-100 text-ink">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Activity className="h-7 w-7 text-ok" />
            <div>
              <h1 className="text-xl font-semibold">NetPulse</h1>
              <p className="text-sm text-slate-500">Real-time network observability</p>
            </div>
          </div>
          <button
            className="rounded-md border border-line px-3 py-2 text-sm hover:bg-slate-50"
            onClick={() => {
              localStorage.removeItem("netpulse_token");
              setToken("");
            }}
          >
            Sign out
          </button>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <div className="grid gap-4 md:grid-cols-4">
          <Stat icon={<Server />} label="Devices" value={summary?.total_devices ?? 0} />
          <Stat icon={<ShieldCheck />} label="Uptime" value={`${summary?.uptime_percentage ?? 100}%`} />
          <Stat icon={<Globe2 />} label="Up" value={summary?.up ?? 0} />
          <Stat icon={<Bell />} label="Down" value={summary?.down ?? 0} tone="bad" />
        </div>

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.5fr_1fr]">
          <section className="rounded-lg border border-line bg-white p-5">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-base font-semibold">Latency and Packet Loss</h2>
              <span className="text-sm text-slate-500">Last {chartData.length} checks</span>
            </div>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d9e2ec" />
                  <XAxis dataKey="time" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Area type="monotone" dataKey="latency" stroke="#2563eb" fill="#dbeafe" />
                  <Area type="monotone" dataKey="packetLoss" stroke="#c83a3a" fill="#fee2e2" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-lg border border-line bg-white p-5">
            <h2 className="mb-4 text-base font-semibold">Open Incidents</h2>
            <div className="space-y-3">
              {incidents.length === 0 && <p className="text-sm text-slate-500">No active incidents.</p>}
              {incidents.map((incident) => (
                <div key={incident.id} className="rounded-md border border-red-200 bg-red-50 p-3">
                  <p className="font-medium text-bad">{incident.title}</p>
                  <p className="text-sm text-slate-600">{incident.severity} · {incident.status}</p>
                </div>
              ))}
            </div>
          </section>
        </div>

        <section className="mt-6 rounded-lg border border-line bg-white">
          <div className="flex items-center gap-2 border-b border-line px-5 py-4">
            <Database className="h-5 w-5 text-slate-600" />
            <h2 className="text-base font-semibold">Device Health</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600">
                <tr>
                  <th className="px-5 py-3">Name</th>
                  <th className="px-5 py-3">Target</th>
                  <th className="px-5 py-3">Status</th>
                  <th className="px-5 py-3">Tags</th>
                </tr>
              </thead>
              <tbody>
                {devices.map((device) => (
                  <tr key={device.id} className="border-t border-line">
                    <td className="px-5 py-3 font-medium">{device.name}</td>
                    <td className="px-5 py-3 text-slate-600">{device.target}</td>
                    <td className="px-5 py-3">
                      <span className={`rounded-full border px-2 py-1 text-xs ${statusClass[device.status]}`}>
                        {device.status}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-600">{Object.keys(device.tags).join(", ") || "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </section>
    </main>
  );
}

function Login({ onToken }: { onToken: (token: string) => void }) {
  const [mode, setMode] = React.useState<"login" | "register">("register");
  const [organizationName, setOrganizationName] = React.useState("Acme Networks");
  const [fullName, setFullName] = React.useState("NetPulse Admin");
  const [email, setEmail] = React.useState("admin@example.com");
  const [password, setPassword] = React.useState("change-me-now");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const path = mode === "register" ? "/api/v1/auth/register" : "/api/v1/auth/login";
    const body =
      mode === "register"
        ? { organization_name: organizationName, full_name: fullName, email, password }
        : { email, password };
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    if (response.ok) {
      const body = await response.json();
      onToken(body.access_token);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-slate-100 px-4">
      <form onSubmit={submit} className="w-full max-w-sm rounded-lg border border-line bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <Activity className="h-7 w-7 text-ok" />
          <h1 className="text-xl font-semibold">NetPulse</h1>
        </div>
        <div className="mb-5 grid grid-cols-2 rounded-md border border-line p-1 text-sm">
          <button type="button" className={`rounded px-3 py-2 ${mode === "register" ? "bg-ink text-white" : "text-slate-600"}`} onClick={() => setMode("register")}>
            Register
          </button>
          <button type="button" className={`rounded px-3 py-2 ${mode === "login" ? "bg-ink text-white" : "text-slate-600"}`} onClick={() => setMode("login")}>
            Login
          </button>
        </div>
        {mode === "register" && (
          <>
            <label className="block text-sm font-medium">Organization</label>
            <input className="mt-1 w-full rounded-md border border-line px-3 py-2" value={organizationName} onChange={(e) => setOrganizationName(e.target.value)} />
            <label className="mt-4 block text-sm font-medium">Full name</label>
            <input className="mt-1 w-full rounded-md border border-line px-3 py-2" value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </>
        )}
        <label className="mt-4 block text-sm font-medium">Email</label>
        <input className="mt-1 w-full rounded-md border border-line px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} />
        <label className="mt-4 block text-sm font-medium">Password</label>
        <input className="mt-1 w-full rounded-md border border-line px-3 py-2" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="mt-6 w-full rounded-md bg-ink px-3 py-2 font-medium text-white hover:bg-slate-700">
          {mode === "register" ? "Create organization" : "Sign in"}
        </button>
      </form>
    </main>
  );
}

function Stat({ icon, label, value, tone = "ok" }: { icon: React.ReactNode; label: string; value: React.ReactNode; tone?: "ok" | "bad" }) {
  return (
    <div className="rounded-lg border border-line bg-white p-5">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-md bg-slate-100 text-slate-700">{icon}</div>
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-semibold ${tone === "bad" ? "text-bad" : "text-ink"}`}>{value}</p>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(<App />);
