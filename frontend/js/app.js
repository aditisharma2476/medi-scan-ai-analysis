/* ═══════════════════════════════════════════════════════════════════
   MediScan AI — Main Application Logic (Skin & Nail Analysis)
   ═══════════════════════════════════════════════════════════════════ */

(function () {
  "use strict";

  // ── Current Mode ───────────────────────────────────────────────
  let currentMode = "skin"; // "skin" or "nail"

  // ── DOM References ─────────────────────────────────────────────
  const $ = (sel) => document.querySelector(sel);
  const uploadZone = $("#upload-zone");
  const uploadContent = $("#upload-zone-content");
  const imageInput = $("#image-input");
  const cameraBtn = $("#camera-btn");
  const cameraPreview = $("#camera-preview");
  const cameraActions = $("#camera-actions");
  const captureBtn = $("#capture-btn");
  const closeCameraBtn = $("#close-camera-btn");
  const previewSection = $("#preview-section");
  const previewImage = $("#preview-image");
  const removeImageBtn = $("#remove-image-btn");
  const analyzeBtn = $("#analyze-btn");
  const loadingSection = $("#loading-section");
  const resultsSection = $("#results-section");
  const newAnalysisBtn = $("#new-analysis-btn");

  // Section references
  const uploadSection = $("#upload-section");

  // Results fields
  const resultImage = $("#result-image");
  const diseaseName = $("#disease-name");
  const probabilityBar = $("#probability-bar");
  const probabilityValue = $("#probability-value");
  const confidenceBar = $("#confidence-bar");
  const confidenceValue = $("#confidence-value");
  const accuracyBar = $("#accuracy-bar");
  const accuracyValue = $("#accuracy-value");
  const riskBar = $("#risk-bar");
  const riskValue = $("#risk-value");
  const severity = $("#severity");
  const contagious = $("#contagious");
  const description = $("#description");
  const symptomsList = $("#symptoms-list");
  const causesList = $("#causes-list");
  const treatmentsList = $("#treatments-list");
  const consultAlert = $("#consult-alert");

  // Dynamic text elements
  const pageSubtitle = $("#page-subtitle");
  const uploadHeading = $("#upload-heading");
  const loadingText = $("#loading-text");

  // Navigation
  const navSkin = $("#nav-skin");
  const navNail = $("#nav-nail");

  // Install banner
  const installBanner = $("#install-banner");
  const installBtn = $("#install-btn");
  const dismissInstall = $("#dismiss-install");

  // ── Mode-specific configuration ─────────────────────────────────
  const MODE_CONFIG = {
    skin: {
      subtitle: "AI-Powered Skin Disease Detection",
      uploadHeading: "Upload a Skin Image",
      loadingText: "Analyzing your skin image...",
      analyzeBtnText:
        '<i class="fa-solid fa-flask"></i> Analyze Skin Condition',
      apiEndpoint: "/analyze",
      consultDoctorText: "Consult a Dermatologist",
    },
    nail: {
      subtitle: "AI-Powered Nail Disease Detection",
      uploadHeading: "Upload a Nail Image",
      loadingText: "Analyzing your nail image...",
      analyzeBtnText:
        '<i class="fa-solid fa-flask"></i> Analyze Nail Condition',
      apiEndpoint: "/analyze-nail",
      consultDoctorText: "Consult a Dermatologist",
    },
  };

  // ── State ──────────────────────────────────────────────────────
  let currentFile = null;
  let mediaStream = null;
  let deferredPrompt = null;

  // // ── API Base URL (Local)───────────────────────────────────────────────
  // const API_BASE = window.location.origin.includes("localhost")
  //   ? "http://localhost:5000"
  //   : window.location.origin;

  // ── API Base URL (Production)───────────────────────────────────────────────
  const API_BASE = window.location.origin.includes("localhost")
    ? "https://api-medi-scan-ai-analysis.onrender.com"
    : window.location.origin;

  // ── Navigation ─────────────────────────────────────────────────
  function switchMode(mode) {
    if (mode === currentMode) return;

    // Reset any ongoing state before switching
    stopCamera();
    resetUploadState();

    currentMode = mode;

    // Update tab active states
    navSkin.classList.toggle("active", mode === "skin");
    navNail.classList.toggle("active", mode === "nail");

    // Update dynamic text
    const config = MODE_CONFIG[mode];
    pageSubtitle.textContent = config.subtitle;
    uploadHeading.textContent = config.uploadHeading;
    loadingText.textContent = config.loadingText;
    analyzeBtn.innerHTML = config.analyzeBtnText;
  }

  navSkin.addEventListener("click", () => switchMode("skin"));
  navNail.addEventListener("click", () => switchMode("nail"));

  // ── PWA Install Prompt ─────────────────────────────────────────
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e;
    installBanner.classList.remove("hidden");
  });

  installBtn.addEventListener("click", async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const result = await deferredPrompt.userChoice;
    if (result.outcome === "accepted") {
      installBanner.classList.add("hidden");
    }
    deferredPrompt = null;
  });

  dismissInstall.addEventListener("click", () => {
    installBanner.classList.add("hidden");
  });

  // ── Upload Zone: Click to browse ───────────────────────────────
  uploadZone.addEventListener("click", () => imageInput.click());

  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.classList.add("drag-over");
  });

  uploadZone.addEventListener("dragleave", () => {
    uploadZone.classList.remove("drag-over");
  });

  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("drag-over");
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  });

  imageInput.addEventListener("change", () => {
    if (imageInput.files.length > 0) handleFile(imageInput.files[0]);
  });

  // ── Camera ─────────────────────────────────────────────────────
  cameraBtn.addEventListener("click", async () => {
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "environment",
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      cameraPreview.srcObject = mediaStream;
      cameraPreview.classList.remove("hidden");
      cameraActions.classList.remove("hidden");
      cameraBtn.classList.add("hidden");
      uploadContent.style.display = "none";
    } catch (err) {
      alert(
        "Camera access denied or not available. Please upload an image instead.",
      );
      console.error("Camera error:", err);
    }
  });

  captureBtn.addEventListener("click", () => {
    const canvas = document.createElement("canvas");
    canvas.width = cameraPreview.videoWidth;
    canvas.height = cameraPreview.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(cameraPreview, 0, 0);
    canvas.toBlob(
      (blob) => {
        const file = new File([blob], "capture.jpg", { type: "image/jpeg" });
        stopCamera();
        handleFile(file);
      },
      "image/jpeg",
      0.92,
    );
  });

  closeCameraBtn.addEventListener("click", stopCamera);

  function stopCamera() {
    if (mediaStream) {
      mediaStream.getTracks().forEach((t) => t.stop());
      mediaStream = null;
    }
    cameraPreview.classList.add("hidden");
    cameraPreview.srcObject = null;
    cameraActions.classList.add("hidden");
    cameraBtn.classList.remove("hidden");
    uploadContent.style.display = "";
  }

  // ── File Handler ───────────────────────────────────────────────
  function handleFile(file) {
    // Validate
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
      alert("Please upload a JPG, PNG, or WEBP image.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      alert("Image is too large. Maximum size is 10 MB.");
      return;
    }

    currentFile = file;

    // Show preview
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImage.src = e.target.result;
      previewSection.classList.remove("hidden");
      uploadContent.style.display = "none";
    };
    reader.readAsDataURL(file);
  }

  // ── Remove Image ───────────────────────────────────────────────
  removeImageBtn.addEventListener("click", resetUpload);

  function resetUploadState() {
    currentFile = null;
    previewImage.src = "";
    resultImage.src = "";
    previewSection.classList.add("hidden");
    uploadContent.style.display = "";
    imageInput.value = "";
    resultsSection.classList.add("hidden");
    loadingSection.classList.add("hidden");
    consultAlert.classList.add("hidden");
    uploadSection.classList.remove("hidden");
  }

  function resetUpload() {
    resetUploadState();
  }

  // ── Analyze ────────────────────────────────────────────────────
  analyzeBtn.addEventListener("click", analyzeImage);

  async function analyzeImage() {
    if (!currentFile) return;

    const config = MODE_CONFIG[currentMode];

    // Show loading
    loadingSection.classList.remove("hidden");
    resultsSection.classList.add("hidden");
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML =
      '<i class="fa-solid fa-spinner fa-spin"></i> Analyzing...';

    try {
      const formData = new FormData();
      formData.append("image", currentFile);

      const response = await fetch(`${API_BASE}${config.apiEndpoint}`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || `Server error: ${response.status}`);
      }

      const data = await response.json();
      displayResults(data);
    } catch (err) {
      alert(`Analysis failed: ${err.message}`);
      console.error("Analysis error:", err);
    } finally {
      loadingSection.classList.add("hidden");
      analyzeBtn.disabled = false;
      analyzeBtn.innerHTML = config.analyzeBtnText;
    }
  }

  // ── Display Results ────────────────────────────────────────────
  function displayResults(data) {
    // Hide the entire upload section and show results
    uploadSection.classList.add("hidden");

    // Copy the preview image to the results section
    resultImage.src = previewImage.src;

    // Disease name
    diseaseName.textContent = data.disease_name || "Unknown";

    // Probability
    const prob = Math.min(100, Math.max(0, data.probability || 0));
    probabilityBar.style.width = `${prob}%`;
    probabilityValue.textContent = `${prob}%`;

    // Confidence
    const conf = Math.min(100, Math.max(0, data.confidence || 0));
    confidenceBar.style.width = `${conf}%`;
    confidenceValue.textContent = `${conf}%`;

    // Accuracy (derived from confidence and probability average)
    const acc = Math.round((prob + conf) / 2);
    accuracyBar.style.width = `${acc}%`;
    accuracyValue.textContent = `${acc}%`;

    // Risk level (inverse of accuracy, capped)
    const risk = Math.min(100, Math.max(0, 100 - acc));
    riskBar.style.width = `${risk}%`;
    riskValue.textContent = `${risk}%`;

    // Severity
    severity.textContent = data.severity || "Unknown";

    // Contagious
    if (data.contagious === true) {
      contagious.textContent = "Yes";
      contagious.style.color = "var(--danger)";
    } else if (data.contagious === false) {
      contagious.textContent = "No";
      contagious.style.color = "var(--success)";
    } else {
      contagious.textContent = "Unknown";
      contagious.style.color = "var(--text-muted)";
    }

    // Description
    description.textContent = data.description || "No description available.";

    // Symptoms
    populateList(symptomsList, data.symptoms);

    // Causes
    populateList(causesList, data.causes);

    // Treatments
    populateList(treatmentsList, data.treatments);

    // Consult alert
    if (data.consult_doctor === true) {
      consultAlert.classList.remove("hidden");
    } else {
      consultAlert.classList.add("hidden");
    }

    // Show results
    resultsSection.classList.remove("hidden");
    resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function populateList(listEl, items) {
    listEl.innerHTML = "";
    if (!items || !Array.isArray(items) || items.length === 0) {
      const li = document.createElement("li");
      li.textContent = "No information available.";
      li.style.color = "var(--text-muted)";
      listEl.appendChild(li);
      return;
    }
    items.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      listEl.appendChild(li);
    });
  }

  // ── New Analysis ───────────────────────────────────────────────
  newAnalysisBtn.addEventListener("click", resetUpload);

  // ── Register Service Worker ────────────────────────────────────
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker
        .register("sw.js")
        .then(() => console.log("SW registered"))
        .catch((err) => console.error("SW registration failed:", err));
    });
  }

  // ── Network status indicator ───────────────────────────────────
  window.addEventListener("online", () => {
    document.body.classList.remove("offline");
  });
  window.addEventListener("offline", () => {
    document.body.classList.add("offline");
    // Show a toast-like notification
    const toast = document.createElement("div");
    toast.className = "offline-toast";
    toast.innerHTML =
      '<i class="fa-solid fa-wifi-slash"></i> You are offline. Some features may be limited.';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
  });
})();
