const form = document.getElementById("summary-form");
const fileInput = document.getElementById("pdf-file");
const fileLabel = document.getElementById("file-label");
const statusCard = document.getElementById("status-card");
const statusTitle = document.getElementById("status-title");
const statusDetail = document.getElementById("status-detail");
const statusHint = document.getElementById("status-hint");
const statusElapsed = document.getElementById("status-elapsed");
const statusProgress = document.getElementById("status-progress");
const statusProgressBar = document.getElementById("status-progress-bar");
const summaryOutput = document.getElementById("summary-output");
const statsList = document.getElementById("stats-list");
const keywordList = document.getElementById("keyword-list");
const engineTag = document.getElementById("engine-tag");
const sourceTag = document.getElementById("source-tag");
const exportBtn = document.getElementById("export-btn");
const resetBtn = document.getElementById("reset-btn");
const submitBtn = document.getElementById("submit-btn");

let latestResult = null;
let loadingTimerId = null;

function setStatusState({
  title,
  detail,
  hint = "",
  elapsed = "",
  type = "info",
  loading = false,
}) {
  statusCard.className = `status-card ${type}`;
  statusTitle.textContent = title;
  statusDetail.innerHTML = detail;
  statusHint.textContent = hint;
  statusElapsed.textContent = elapsed;
  statusProgress.classList.toggle("visible", loading);
  statusProgressBar.classList.toggle("loading", loading);
}

function clearLoadingTimer() {
  if (loadingTimerId !== null) {
    window.clearInterval(loadingTimerId);
    loadingTimerId = null;
  }
}

function startLoadingStatus({ hasPdf }) {
  clearLoadingTimer();

  const startedAt = Date.now();

  function tick() {
    const elapsedSeconds = Math.max(1, Math.floor((Date.now() - startedAt) / 1000));
    let title = "Generating summary";
    let detail = "Your request is being processed.";
    let hint = "Please keep this tab open until the summary appears.";

    if (hasPdf) {
      if (elapsedSeconds <= 4) {
        title = "Uploading and validating PDF";
        detail = "The system is checking the file format, size, and basic readability.";
        hint = "This usually takes only a few seconds.";
      } else if (elapsedSeconds <= 11) {
        title = "Extracting text from PDF";
        detail = "The document text is being pulled out page by page before summarization.";
        hint = "Larger PDFs can take a bit longer during extraction.";
      } else if (elapsedSeconds <= 24) {
        title = "Running AI summarization";
        detail = "The extracted text is being summarized by the local AI model.";
        hint = "CPU-based summarization may take around 15-60 seconds for long PDFs.";
      } else {
        title = "Still processing a large PDF";
        detail = "The request is still active and the model is working through the document.";
        hint = "If the PDF is long, waiting a little longer is normal.";
      }
    } else {
      if (elapsedSeconds <= 5) {
        title = "Preparing your text";
        detail = "The input is being cleaned and prepared for summarization.";
        hint = "Short text usually finishes quickly.";
      } else if (elapsedSeconds <= 16) {
        title = "Running AI summarization";
        detail = "The model is generating the summary now.";
        hint = "Longer text can take a little more time on CPU.";
      } else {
        title = "Still processing your text";
        detail = "The request is still active and the model is finalizing the response.";
        hint = "Please wait a few more seconds.";
      }
    }

    setStatusState({
      title,
      detail,
      hint,
      elapsed: `${elapsedSeconds}s elapsed`,
      type: "info",
      loading: true,
    });
  }

  tick();
  loadingTimerId = window.setInterval(tick, 1000);
}

function updateStats(stats) {
  statsList.innerHTML = `
    <li>Original words: ${stats.original_words}</li>
    <li>Summary words: ${stats.summary_words}</li>
    <li>Compression ratio: ${stats.compression_ratio}</li>
    <li>Reading time: ${stats.estimated_read_time_minutes} min</li>
  `;
}

function updateKeywords(keywords) {
  if (!keywords.length) {
    keywordList.innerHTML = `<span class="keyword muted">No keywords found</span>`;
    return;
  }

  keywordList.innerHTML = keywords
    .map((keyword) => `<span class="keyword">${keyword}</span>`)
    .join("");
}

function resetResults() {
  latestResult = null;
  summaryOutput.textContent = "Your summary will appear here.";
  statsList.innerHTML = `
    <li>Original words: -</li>
    <li>Summary words: -</li>
    <li>Compression ratio: -</li>
    <li>Reading time: -</li>
  `;
  keywordList.innerHTML = `<span class="keyword muted">No keywords yet</span>`;
  engineTag.textContent = "Engine pending";
  sourceTag.textContent = "Source pending";
  exportBtn.disabled = true;
}

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileLabel.textContent = file ? file.name : "No file selected";
});

resetBtn.addEventListener("click", () => {
  form.reset();
  fileLabel.textContent = "No file selected";
  clearLoadingTimer();
  setStatusState({
    title: "Ready to summarize",
    detail: "Enter text or upload a PDF, then click <strong>Generate Summary</strong>.",
    hint: "Large PDFs may take longer because text extraction and AI summarization both run locally.",
    type: "info",
    loading: false,
  });
  resetResults();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const inputText = document.getElementById("input-text").value.trim();
  const file = fileInput.files[0];

  if (!inputText && !file) {
    setStatusState({
      title: "Input required",
      detail: "Please provide text or upload a PDF before generating a summary.",
      hint: "You can paste content directly or choose a PDF file from your device.",
      type: "error",
      loading: false,
    });
    return;
  }

  const formData = new FormData();
  formData.append("input_text", inputText);
  formData.append("summary_size", document.getElementById("summary-size").value);
  formData.append("output_format", document.getElementById("output-format").value);

  if (file) {
    formData.append("pdf_file", file);
  }

  submitBtn.disabled = true;
  exportBtn.disabled = true;
  startLoadingStatus({ hasPdf: Boolean(file) });
  summaryOutput.textContent = "Generating summary...";
  engineTag.textContent = "Processing...";
  sourceTag.textContent = file ? "PDF upload detected" : "Direct text detected";

  try {
    const response = await fetch("/api/summarize", {
      method: "POST",
      body: formData,
    });

    const isJson = response.headers.get("content-type")?.includes("application/json");
    const data = isJson ? await response.json() : null;
    if (!response.ok) {
      throw new Error(data?.detail || "Summarization failed.");
    }

    latestResult = data;
    summaryOutput.textContent = data.summary;
    engineTag.textContent = data.engine_used;
    sourceTag.textContent = `${data.source_type.toUpperCase()} | ${data.model_name}`;
    updateStats(data.stats);
    updateKeywords(data.keywords);
    clearLoadingTimer();

    if (data.warning) {
      setStatusState({
        title: "Summary generated with fallback mode",
        detail: data.warning,
        hint: "The result is still usable, but the app switched away from the full transformer path for this request.",
        type: "info",
        loading: false,
      });
    } else {
      setStatusState({
        title: "Summary generated successfully",
        detail: "The summary, keywords, and document statistics are ready to review.",
        hint: "You can now export the summary as PDF if needed.",
        type: "success",
        loading: false,
      });
    }

    exportBtn.disabled = false;
  } catch (error) {
    clearLoadingTimer();
    resetResults();
    setStatusState({
      title: "Summary generation failed",
      detail: error.message || "Something went wrong while generating the summary.",
      hint: "Try a smaller input, check whether the PDF contains selectable text, or retry once more.",
      type: "error",
      loading: false,
    });
  } finally {
    submitBtn.disabled = false;
  }
});

exportBtn.addEventListener("click", async () => {
  if (!latestResult) {
    return;
  }

  exportBtn.disabled = true;
  setStatusState({
    title: "Preparing PDF export",
    detail: "The summary is being converted into a downloadable PDF file.",
    hint: "This should finish quickly.",
    type: "info",
    loading: true,
  });

  try {
    const response = await fetch("/api/export", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: "AI Summary Export",
        source_name: latestResult.source_type === "pdf" ? "Uploaded PDF" : "Direct Text Input",
        summary: latestResult.summary,
        keywords: latestResult.keywords,
        format: latestResult.format,
        engine_used: latestResult.engine_used,
      }),
    });

    if (!response.ok) {
      throw new Error("Export could not be generated.");
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "summary_export.pdf";
    anchor.click();
    window.URL.revokeObjectURL(url);
    setStatusState({
      title: "Summary export downloaded",
      detail: "Your PDF export was generated successfully.",
      hint: "You can review or share the downloaded summary file.",
      type: "success",
      loading: false,
    });
  } catch (error) {
    setStatusState({
      title: "Export failed",
      detail: error.message || "Export failed.",
      hint: "Retry once more. If the problem continues, regenerate the summary and try again.",
      type: "error",
      loading: false,
    });
  } finally {
    exportBtn.disabled = false;
  }
});

resetResults();
setStatusState({
  title: "Ready to summarize",
  detail: "Enter text or upload a PDF, then click <strong>Generate Summary</strong>.",
  hint: "Large PDFs may take longer because text extraction and AI summarization both run locally.",
  type: "info",
  loading: false,
});
