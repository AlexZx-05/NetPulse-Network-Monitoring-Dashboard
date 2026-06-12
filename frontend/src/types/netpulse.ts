export interface DashboardSummary {
  total_devices: number;
  up: number;
  degraded: number;
  down: number;
  unknown: number;
  uptime_percentage: number;
  avg_latency_ms: number | null;
}

export interface Device {
  id: string;
  name: string;
  target: string;
  status: "up" | "degraded" | "down" | "unknown";
  tags: Record<string, string>;
  created_at: string;
}

export interface Metric {
  id: string;
  job_id: string;
  status: string;
  latency_ms: number | null;
  packet_loss: number;
  detail: Record<string, unknown>;
  created_at: string;
}

export interface Incident {
  id: string;
  device_id: string;
  title: string;
  status: string;
  severity: string;
  opened_at: string;
  resolved_at: string | null;
}
