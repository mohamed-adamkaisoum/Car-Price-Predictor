const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

async function getErrorMessage(response: Response): Promise<string> {
  const text = await response.text();
  if (!text) return `Erreur API ${response.status}.`;

  try {
    const payload = JSON.parse(text) as { detail?: unknown };
    if (typeof payload.detail === "string") return payload.detail;
  } catch {
    // Fall back to the raw response body below.
  }

  return text;
}

export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json();
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    throw new Error(await getErrorMessage(response));
  }
  return response.json();
}
