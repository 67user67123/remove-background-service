/* Client-side behavior for upload, validation, processing and comparison. */

(() => {
  "use strict";

  // Configuration
  const MAX_FILE_SIZE = 20 * 1024 * 1024;
  const MAX_IMAGE_PIXELS = 40_000_000;
  const ENDPOINT = "/remove-background";

  // DOM references
  const workspace = document.getElementById("workspace");
  const uploadForm = document.getElementById("uploadForm");
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const errorBox = document.getElementById("errorBox");
  const errorText = document.getElementById("errorText");
  const selectedFilePanel = document.getElementById("selectedFile");
  const fileThumb = document.getElementById("fileThumb");
  const fileName = document.getElementById("fileName");
  const fileMeta = document.getElementById("fileMeta");
  const replaceButton = document.getElementById("replaceButton");
  const processButton = document.getElementById("processButton");
  const processButtonText = document.getElementById("processButtonText");
  const buttonSpinner = document.querySelector(".button-spinner");
  const progressBlock = document.getElementById("progressBlock");
  const progressStatus = document.getElementById("progressStatus");
  const resultSection = document.getElementById("resultSection");
  const resultTitle = document.getElementById("resultTitle");
  const comparison = document.getElementById("comparison");
  const comparisonShell = document.getElementById("comparisonShell");
  const compareRange = document.getElementById("compareRange");
  const splitOutput = document.getElementById("splitOutput");
  const beforeImage = document.getElementById("beforeImage");
  const afterImage = document.getElementById("afterImage");
  const downloadButton = document.getElementById("downloadButton");
  const newImageButton = document.getElementById("newImageButton");

  // Mutable application state
  let selectedFile = null;
  let originalUrl = null;
  let resultUrl = null;
  let imageWidth = 0;
  let imageHeight = 0;
  let isProcessing = false;
  let selectionToken = 0;
  let activeRequest = null;
  let progressTimers = [];
  let dragDepth = 0;

  // UI and image helpers
  const formatBytes = (bytes) => {
    if (bytes < 1024) return `${bytes} Б`;
    if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} КБ`;
    return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} МБ`;
  };

  const revokeUrl = (url) => {
    if (url) URL.revokeObjectURL(url);
  };

  const hideError = () => {
    errorBox.hidden = true;
    errorText.textContent = "";
  };

  const showError = (message) => {
    errorText.textContent = message;
    errorBox.hidden = false;
    errorBox.focus({ preventScroll: true });
  };

  const detectImageFormat = async (file) => {
    const bytes = new Uint8Array(await file.slice(0, 12).arrayBuffer());
    const isJpeg = bytes.length >= 3 && bytes[0] === 0xff && bytes[1] === 0xd8 && bytes[2] === 0xff;
    const pngSignature = [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a];
    const isPng = bytes.length >= 8 && pngSignature.every((value, index) => bytes[index] === value);

    if (isJpeg) return "JPG";
    if (isPng) return "PNG";
    return null;
  };

  const getImageDimensions = (url) => new Promise((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
    image.onerror = () => reject(new Error("decode"));
    image.src = url;
  });

  const clearResult = () => {
    resultSection.hidden = true;
    downloadButton.removeAttribute("href");
    afterImage.removeAttribute("src");
    revokeUrl(resultUrl);
    resultUrl = null;
  };

  const setComparisonRatio = (width, height) => {
    const safeWidth = Math.max(1, width);
    const safeHeight = Math.max(1, height);
    const ratio = safeWidth / safeHeight;
    comparisonShell.style.setProperty("--ratio-number", String(ratio));
    comparison.style.setProperty("--ratio", `${safeWidth} / ${safeHeight}`);
  };

  const updateSplit = () => {
    const value = Number(compareRange.value);
    comparison.style.setProperty("--split", `${value}%`);
    compareRange.setAttribute("aria-valuetext", `${value} процентов: слева до, справа после`);
    splitOutput.value = `Разделитель: ${value}%`;
  };

  // File validation and selection
  const selectFile = async (files) => {
    const token = ++selectionToken;
    hideError();

    if (isProcessing) return;
    if (!files || files.length === 0) return;
    if (files.length !== 1) {
      showError("Выберите только одно изображение за раз.");
      return;
    }

    const file = files[0];
    if (file.size === 0) {
      showError("Файл пуст. Выберите другое изображение.");
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      showError(`Файл весит ${formatBytes(file.size)}. Максимальный размер — 20 МБ.`);
      return;
    }

    let format;
    try {
      format = await detectImageFormat(file);
    } catch {
      showError("Не удалось прочитать файл. Выберите JPG или PNG.");
      return;
    }

    if (token !== selectionToken) return;
    if (!format) {
      showError("Неподдерживаемый формат. Выберите изображение JPG или PNG.");
      return;
    }

    const nextUrl = URL.createObjectURL(file);
    let dimensions;
    try {
      dimensions = await getImageDimensions(nextUrl);
    } catch {
      revokeUrl(nextUrl);
      showError("Изображение повреждено или не читается. Попробуйте другой файл.");
      return;
    }

    if (token !== selectionToken) {
      revokeUrl(nextUrl);
      return;
    }
    if (dimensions.width * dimensions.height > MAX_IMAGE_PIXELS) {
      revokeUrl(nextUrl);
      showError("Слишком большое разрешение. Выберите изображение до 40 мегапикселей.");
      return;
    }

    clearResult();
    fileThumb.removeAttribute("src");
    beforeImage.removeAttribute("src");
    revokeUrl(originalUrl);

    const expectedMime = format === "JPG" ? "image/jpeg" : "image/png";
    selectedFile = file.type === expectedMime
      ? file
      : new File([file], file.name, { type: expectedMime, lastModified: file.lastModified });
    originalUrl = nextUrl;
    imageWidth = dimensions.width;
    imageHeight = dimensions.height;

    fileThumb.src = originalUrl;
    beforeImage.src = originalUrl;
    fileName.textContent = file.name || `Изображение.${format.toLowerCase()}`;
    fileMeta.textContent = `${format} · ${formatBytes(file.size)} · ${imageWidth} × ${imageHeight} px`;
    selectedFilePanel.hidden = false;
    processButton.disabled = false;
    compareRange.value = "50";
    updateSplit();
    setComparisonRatio(imageWidth, imageHeight);
  };

  // API error normalization
  const fallbackApiMessage = (status) => {
    if (status === 400 || status === 422) return "Сервис не смог прочитать изображение. Проверьте файл и попробуйте снова.";
    if (status === 413) return "Изображение слишком большое для сервиса. Выберите файл до 20 МБ.";
    if (status === 429) return "Слишком много запросов. Подождите немного и повторите попытку.";
    if (status === 503) return "Модель ещё загружается или временно недоступна. Попробуйте чуть позже.";
    if (status >= 500) return "Не удалось удалить фон. Попробуйте другое изображение или повторите позже.";
    return `Сервис вернул ошибку ${status}. Попробуйте ещё раз.`;
  };

  const normalizeApiDetail = (detail) => {
    if (typeof detail === "string") {
      const message = detail.trim();
      if (message === "Upload a valid JPG or PNG image no larger than 20 MiB.") {
        return "Сервис не принял файл. Выберите корректный JPG или PNG размером до 20 МБ.";
      }
      if (message === "Background removal failed.") {
        return "Модель не смогла обработать изображение. Попробуйте другой файл.";
      }
      return message;
    }
    if (Array.isArray(detail)) {
      return detail
        .map((item) => typeof item === "string" ? item : item?.msg)
        .filter(Boolean)
        .join("; ");
    }
    if (detail && typeof detail === "object") {
      if (typeof detail.message === "string") return detail.message.trim();
      if (typeof detail.msg === "string") return detail.msg.trim();
    }
    return "";
  };

  const readApiError = async (response) => {
    const fallback = fallbackApiMessage(response.status);
    try {
      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const payload = await response.json();
        const message = normalizeApiDetail(payload?.detail ?? payload?.message ?? payload?.error);
        return message ? message.slice(0, 500) : fallback;
      }

      const message = (await response.text()).trim();
      return message && message.length <= 500 ? message : fallback;
    } catch {
      return fallback;
    }
  };

  // Processing state and download naming
  const setProcessing = (processing) => {
    isProcessing = processing;
    workspace.classList.toggle("is-processing", processing);
    processButton.setAttribute("aria-busy", String(processing));
    dropZone.classList.toggle("is-disabled", processing);
    fileInput.disabled = processing;
    replaceButton.disabled = processing;
    processButton.disabled = processing || !selectedFile;
    progressBlock.hidden = !processing;
    processButtonText.textContent = processing ? "Обработка…" : "Удалить фон";
    buttonSpinner.className = processing ? "button-spinner spinner" : "button-spinner";
    buttonSpinner.hidden = !processing;

    progressTimers.forEach(window.clearTimeout);
    progressTimers = [];
    if (processing) {
      progressStatus.textContent = "Обработка…";
      progressTimers.push(window.setTimeout(() => {
        progressStatus.textContent = "Модель отделяет объект от фона…";
      }, 1200));
      progressTimers.push(window.setTimeout(() => {
        progressStatus.textContent = "Уточняем края изображения…";
      }, 4800));
    }
  };

  const safeDownloadName = (name) => {
    const base = (name || "image")
      .replace(/\.[^.]+$/, "")
      .replace(/[<>:"/\\|?*\u0000-\u001f]/g, "-")
      .trim()
      .slice(0, 90);
    return `${base || "image"}-без-фона.png`;
  };

  // Background-removal request and result presentation
  const processImage = async () => {
    if (!selectedFile || isProcessing) return;

    hideError();
    clearResult();
    setProcessing(true);
    activeRequest = new AbortController();

    try {
      const formData = new FormData();
      formData.append("file", selectedFile, selectedFile.name);

      const response = await fetch(ENDPOINT, {
        method: "POST",
        body: formData,
        signal: activeRequest.signal
      });

      if (!response.ok) {
        throw new Error(await readApiError(response));
      }

      const contentType = (response.headers.get("content-type") || "").toLowerCase();
      if (!contentType.includes("image/png")) {
        throw new Error("Сервис вернул неожиданный формат. Ожидался прозрачный PNG.");
      }

      const resultBlob = await response.blob();
      if (resultBlob.size === 0) {
        throw new Error("Сервис вернул пустой файл. Повторите попытку.");
      }

      const nextResultUrl = URL.createObjectURL(resultBlob);
      try {
        await getImageDimensions(nextResultUrl);
      } catch {
        revokeUrl(nextResultUrl);
        throw new Error("Полученный PNG повреждён. Повторите попытку.");
      }

      resultUrl = nextResultUrl;
      afterImage.src = resultUrl;
      downloadButton.href = resultUrl;
      downloadButton.download = safeDownloadName(selectedFile.name);
      resultSection.hidden = false;
      compareRange.value = "50";
      updateSplit();

      const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      resultSection.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
      window.setTimeout(() => resultTitle.focus({ preventScroll: true }), reduceMotion ? 0 : 450);
    } catch (error) {
      if (error?.name !== "AbortError") {
        const message = error instanceof TypeError
          ? "Не удалось связаться с сервисом. Проверьте подключение и попробуйте снова."
          : (error?.message || "Не удалось обработать изображение. Попробуйте снова.");
        showError(message);
      }
    } finally {
      activeRequest = null;
      setProcessing(false);
    }
  };

  // Event wiring and resource cleanup
  fileInput.addEventListener("change", () => {
    const files = Array.from(fileInput.files || []);
    fileInput.value = "";
    void selectFile(files);
  });

  uploadForm.addEventListener("submit", (event) => {
    event.preventDefault();
    void processImage();
  });

  replaceButton.addEventListener("click", () => fileInput.click());
  newImageButton.addEventListener("click", () => {
    fileInput.click();
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (event) => {
      event.preventDefault();
      if (isProcessing) return;
      if (eventName === "dragenter") dragDepth += 1;
      dropZone.classList.add("is-dragging");
      if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
    });
  });

  dropZone.addEventListener("dragleave", (event) => {
    event.preventDefault();
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) dropZone.classList.remove("is-dragging");
  });

  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dragDepth = 0;
    dropZone.classList.remove("is-dragging");
    if (isProcessing) return;
    void selectFile(Array.from(event.dataTransfer?.files || []));
  });

  document.addEventListener("dragover", (event) => {
    if (Array.from(event.dataTransfer?.types || []).includes("Files")) event.preventDefault();
  });

  document.addEventListener("drop", (event) => {
    if (Array.from(event.dataTransfer?.types || []).includes("Files")) event.preventDefault();
  });

  compareRange.addEventListener("input", updateSplit);
  compareRange.addEventListener("focus", () => comparison.classList.add("is-focused"));
  compareRange.addEventListener("blur", () => comparison.classList.remove("is-focused"));

  window.addEventListener("beforeunload", () => {
    activeRequest?.abort();
    revokeUrl(originalUrl);
    revokeUrl(resultUrl);
  });

  buttonSpinner.hidden = true;
  updateSplit();
})();

