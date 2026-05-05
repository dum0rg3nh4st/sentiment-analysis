const $ = (id) => document.getElementById(id);
const textEl = $("text");
const analyzeBtn = $("analyzeBtn");
const btnLabel = $("btnLabel");
const spinner = $("spinner");
const statusEl = $("status");
const resultEl = $("result");
const confidenceEl = $("confidence");
const timeEl = $("time");

function setLoading(isLoading) {
  analyzeBtn.disabled = isLoading;
  spinner.classList.toggle("hidden", !isLoading);
  btnLabel.textContent = isLoading ? "Analyzing..." : "Analyze";
}

function showStatus(kind, message) {
  statusEl.classList.remove("hidden");
  statusEl.className =
    "mt-4 rounded-xl border px-4 py-3 text-sm " +
    (kind === "error"
      ? "border-red-200 bg-red-50 text-red-800"
      : kind === "success"
        ? "border-emerald-200 bg-emerald-50 text-emerald-800"
        : "border-sky-200 bg-sky-50 text-sky-900");
  statusEl.textContent = message;
}

function clearStatus() {
  statusEl.classList.add("hidden");
  statusEl.textContent = "";
}

function formatConfidence(score) {
  if (typeof score !== "number" || Number.isNaN(score)) return "—";
  return `${(score * 100).toFixed(2)}%`;
}

async function predict(text) {
  const res = await fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json() : await res.text();
  if (!res.ok) {
    const msg = typeof data === "object" && data ? data.detail || JSON.stringify(data) : String(data);
    throw new Error(msg || `HTTP ${res.status}`);
  }
  return data;
}

analyzeBtn.addEventListener("click", async () => {
  clearStatus();
  resultEl.textContent = "—";
  confidenceEl.textContent = "Confidence: —";
  timeEl.textContent = "Logged at: —";

  const text = (textEl.value || "").trim();
  if (!text) {
    showStatus("error", "Please enter some text to analyze.");
    return;
  }

  setLoading(true);
  try {
    const data = await predict(text);
    resultEl.textContent = data.sentiment_label;
    confidenceEl.textContent = `Confidence: ${formatConfidence(data.score)}`;
    timeEl.textContent = `Logged at: ${data.timestamp}`;
    showStatus("success", "Done.");
  } catch (e) {
    showStatus("error", e?.message || String(e));
  } finally {
    setLoading(false);
  }
});

textEl.addEventListener("keydown", (e) => {
  const isMac = navigator.platform.toLowerCase().includes("mac");
  if ((isMac ? e.metaKey : e.ctrlKey) && e.key === "Enter") analyzeBtn.click();
});
