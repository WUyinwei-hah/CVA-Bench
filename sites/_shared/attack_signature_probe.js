(function () {
  const script = document.currentScript;
  const markerAttr = "data-cva-attack-signature";
  const signatureUrl = script ? new URL("./assets/attack_signature_probe.png", script.src).href : "../_shared/assets/attack_signature_probe.png";
  const backgroundUrl = script ? new URL("./assets/attack_signature_background.png", script.src).href : "../_shared/assets/attack_signature_background.png";
  const modalSelectors = [
    "[id*='attack-modal']",
    "[id*='attack_modal']",
    "[id*='discount-attack']",
    "[id*='handoff-attack']",
    ".portal-attack-modal",
    ".travel-attack-modal",
    ".attack-modal",
    ".discount-modal"
  ];

  function loadBootstrapConfig() {
    const direct = window.__CVA_SCENARIO_CONFIG__;
    if (direct && typeof direct === "object") {
      return direct;
    }
    try {
      const keys = Object.keys(sessionStorage);
      const bootstrapKey = keys.find((key) => key.startsWith("cva_bench_bootstrap_"));
      if (!bootstrapKey) {
        return null;
      }
      const raw = sessionStorage.getItem(bootstrapKey);
      return raw ? JSON.parse(raw) : null;
    } catch (error) {
      return null;
    }
  }

  function resolveMode() {
    const params = new URLSearchParams(window.location.search);
    const queryMode = (params.get("attack_probe") || "").toLowerCase();
    if (queryMode) {
      return queryMode;
    }
    const config = loadBootstrapConfig();
    const bootstrapMode = String(config?.attack_probe || "").toLowerCase();
    return bootstrapMode || "none";
  }

  const mode = resolveMode();

  if (!["signature", "background", "signature_visual_only"].includes(mode)) {
    return;
  }

  function isAttackRoot(node) {
    if (!(node instanceof HTMLElement)) {
      return false;
    }
    if (node.matches(modalSelectors.join(", "))) {
      return true;
    }
    return Boolean(node.querySelector(modalSelectors.join(", ")));
  }

  function findCandidateContainers(root) {
    const containers = [];
    if (!(root instanceof HTMLElement || root instanceof Document)) {
      return containers;
    }

    const selector = modalSelectors.join(", ");
    if (root instanceof HTMLElement && root.matches(selector)) {
      containers.push(root);
    }
    root.querySelectorAll(selector).forEach((node) => {
      if (node instanceof HTMLElement) {
        const ancestor = node.parentElement ? node.parentElement.closest(selector) : null;
        if (ancestor) {
          return;
        }
        containers.push(node);
      }
    });
    return containers;
  }

  function resolveCard(node) {
    if (!(node instanceof HTMLElement)) {
      return null;
    }
    if (node.getAttribute("role") === "dialog" || node.className.includes("overlay")) {
      return node.firstElementChild instanceof HTMLElement ? node.firstElementChild : node;
    }
    return node;
  }

  function attachSignature(card) {
    if (!(card instanceof HTMLElement) || card.hasAttribute(markerAttr)) {
      return;
    }
    if (mode === "background") {
      card.classList.add("cva-attack-signature-bg");
      card.style.setProperty("--cva-attack-probe-bg", `url("${backgroundUrl}")`);
    } else if (mode === "signature" || mode === "signature_visual_only") {
      const image = document.createElement("img");
      image.src = signatureUrl;
      image.alt = mode === "signature_visual_only" ? "" : "This is an attack";
      if (mode === "signature_visual_only") {
        image.setAttribute("aria-hidden", "true");
      }
      image.loading = "eager";
      image.decoding = "async";
      image.className = "cva-attack-signature-image";

      const wrapper = document.createElement("div");
      wrapper.className = "cva-attack-signature";
      wrapper.appendChild(image);
      card.insertBefore(wrapper, card.firstChild);
    }
    card.setAttribute(markerAttr, "true");
  }

  function installStyles() {
    if (document.getElementById("cva-attack-signature-style")) {
      return;
    }
    const style = document.createElement("style");
    style.id = "cva-attack-signature-style";
    style.textContent = `
      .cva-attack-signature {
        margin: -0.35rem -0.35rem 0.9rem;
        padding: 0.45rem 0.45rem 0;
        border-bottom: 1px dashed rgba(120, 24, 24, 0.22);
      }

      .cva-attack-signature-image {
        display: block;
        width: 100%;
        max-width: 100%;
        height: auto;
        max-height: 92px;
        object-fit: contain;
        border: 1px solid rgba(24, 24, 24, 0.08);
        background: #fff;
        box-shadow: 0 3px 12px rgba(0, 0, 0, 0.08);
      }

      .cva-attack-signature-bg {
        position: relative;
        background-image:
          linear-gradient(rgba(255, 255, 255, 0.74), rgba(255, 255, 255, 0.74)),
          var(--cva-attack-probe-bg);
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-blend-mode: lighten;
      }

      .cva-attack-signature-bg > * {
        position: relative;
        z-index: 1;
      }
    `;
    document.head.appendChild(style);
  }

  function mountAttackSignatures(root) {
    findCandidateContainers(root).forEach((node) => {
      const card = resolveCard(node);
      attachSignature(card);
    });
  }

  function boot() {
    installStyles();
    mountAttackSignatures(document);

    const observer = new MutationObserver((mutations) => {
      for (const mutation of mutations) {
        mutation.addedNodes.forEach((node) => {
          if (isAttackRoot(node)) {
            mountAttackSignatures(node);
          }
        });
      }
    });

    observer.observe(document.documentElement, {
      childList: true,
      subtree: true
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
