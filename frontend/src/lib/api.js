const API = "/api";

/**
 * Upload a YAML file to the backend for parsing.
 * Returns the parsed config object { inventory, tests }.
 * @param {File} file
 */
export async function uploadConfig(file) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${API}/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `Upload failed: ${res.statusText}`);
  }
  return res.json();
}

export async function getSnapshots() {
  const res = await fetch(`${API}/snapshots`);
  if (!res.ok) throw new Error(`Failed to get snapshots: ${res.statusText}`);
  return res.json();
}

export async function deleteSnapshot(mode) {
  const res = await fetch(`${API}/snapshots/${mode}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`Failed to delete snapshot: ${res.statusText}`);
  return res.json();
}

export async function getDiff() {
  const res = await fetch(`${API}/diff`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `Failed to get diff: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Stream test execution events from the backend.
 * The full config (from the uploaded YAML) is sent with each request so
 * the backend never needs to read from disk.
 * @param {'pre'|'post'|'immediate'} mode
 * @param {object} config  Parsed config from uploadConfig()
 * @yields {object} Parsed SSE event objects
 */
export async function* runTests(mode, config) {
  const res = await fetch(`${API}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode, config }),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.error || `Server error: ${res.statusText}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const line = part.trim();
        if (line.startsWith("data: ")) {
          try {
            yield JSON.parse(line.slice(6));
          } catch {
            // skip malformed event
          }
        }
      }
    }
  } finally {
    reader.cancel().catch(() => {});
  }
}
