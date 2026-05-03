const serverUrl = document.getElementById("server-url");
const readKey = document.getElementById("read-key");
const responseEl = document.getElementById("response");
const btnFetchAll = document.getElementById("btn-fetch-all");
const btnFetchPath = document.getElementById("btn-fetch-path");
const configPath = document.getElementById("config-path");

function showResult(data) {
  responseEl.innerHTML = `<code>${escapeHtml(JSON.stringify(data, null, 2))}</code>`;
}

function showError(msg) {
  responseEl.innerHTML = `<code class="error">${escapeHtml(msg)}</code>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

async function request(path) {
  const url = serverUrl.value.replace(/\/+$/, "") + path;
  const headers = {};

  const key = readKey.value.trim();
  if (key) {
    headers["read-key"] = key;
  }

  const res = await fetch(url, { headers });

  if (!res.ok) {
    const text = await res.text();
    let detail;
    try {
      detail = JSON.parse(text).detail || text;
    } catch {
      detail = text;
    }
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }

  return res.json();
}

btnFetchAll.addEventListener("click", async () => {
  try {
    const data = await request("/config");
    showResult(data);
  } catch (err) {
    showError(err.message);
  }
});

btnFetchPath.addEventListener("click", async () => {
  const path = configPath.value.trim().replace(/^\/+|\/+$/g, "");
  if (!path) {
    showError("Please enter a config path");
    return;
  }
  try {
    const data = await request(`/config/${path}`);
    showResult(data);
  } catch (err) {
    showError(err.message);
  }
});
