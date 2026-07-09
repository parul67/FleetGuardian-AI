const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

export type TokenResponse = {
  access_token: string;
  token_type: string;
  refresh_token: string;
};

export type DashboardSummary = {
  total_drivers?: number;
  total_vehicles?: number;
  total_alerts?: number;
  active_trips?: number;
  fleet_safety_score?: number;
  recent_alerts?: Array<{
    id?: number;
    type?: string;
    severity?: string;
    status?: string;
    description?: string;
    created_at?: string;
  }>;
  recent_trips?: Array<{
    id?: number;
    driver_name?: string;
    vehicle_name?: string;
    score?: number;
    status?: string;
  }>;
  driver_scores?: Array<{
    name?: string;
    score?: number;
  }>;
};

export type AlertStat = {
  type?: string;
  count?: number;
};

export type DailyTrend = {
  date: string;
  total_alerts: number;
  total_trips: number;
  average_score: number;
};

async function request<T>(path: string, init?: RequestInit, token?: string): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      if (typeof payload?.detail === "string") detail = payload.detail;
      else if (payload?.message) detail = payload.message;
    } catch {
      // ignore json parse errors
    }
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

export function login(email: string, password: string) {
  return request<TokenResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function loginWithGoogle(idToken: string) {
  return request<TokenResponse>("/auth/google", {
    method: "POST",
    body: JSON.stringify({ id_token: idToken }),
  });
}

export function getDashboard(token: string) {
  return request<DashboardSummary>("/dashboard/", { method: "GET" }, token);
}

export function getAlertStats(token: string) {
  return request<AlertStat[]>("/alerts/stats", { method: "GET" }, token);
}

export function getDailyTrends(token: string) {
  return request<DailyTrend[]>("/analytics/daily?days=7", { method: "GET" }, token);
}

export function getCurrentUser(token: string) {
  return request<Record<string, unknown>>("/auth/me", { method: "GET" }, token);
}
