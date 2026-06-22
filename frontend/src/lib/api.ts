const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("token");

  const res = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || "Request failed");
  }

  return res.json();
}

export const auth = {
  signup: (email: string, password: string, full_name?: string) =>
    apiRequest("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: async (email: string, password: string) => {
    const data = await apiRequest<{ access_token: string; token_type: string }>(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ email, password }) }
    );
    localStorage.setItem("token", data.access_token);
    return data;
  },

  me: () => apiRequest("/auth/me"),

  logout: () => localStorage.removeItem("token"),
};
