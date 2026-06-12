import type { DashboardSummary } from "../types/netpulse";

export async function api<T>(path: string, token: string): Promise<T> {
  const response = await fetch(path, {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function connectDashboardSocket(
  token: string,
  onMessage: (summary: DashboardSummary) => void
): () => void {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${window.location.host}/api/v1/ws/dashboard?token=${token}`);
  socket.onmessage = (event) => onMessage(JSON.parse(event.data));
  return () => socket.close();
}
