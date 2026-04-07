(function () {
  function getBench() {
    if (window.__CVA_BENCH__ && typeof window.__CVA_BENCH__.addNote === "function") {
      return window.__CVA_BENCH__;
    }
    return null;
  }

  function addNote(message) {
    const bench = getBench();
    if (bench) {
      bench.addNote(message);
    }
  }

  function showInlineStatus(message, tone) {
    const statusId = "cva-webarena-inline-status";
    let status = document.getElementById(statusId);
    if (!status) {
      status = document.createElement("div");
      status.id = statusId;
      status.className = "cva-inline-status";
      document.body.appendChild(status);
    }
    status.textContent = message;
    status.setAttribute("data-tone", tone || "neutral");
  }

  function removeExistingRoot(rootId) {
    const existing = document.getElementById(rootId);
    if (existing) {
      existing.remove();
    }
  }

  function ensureStyle(styleId, cssText) {
    let styleEl = document.getElementById(styleId);
    if (!styleEl) {
      styleEl = document.createElement("style");
      styleEl.id = styleId;
      document.head.appendChild(styleEl);
    }
    styleEl.textContent = cssText;
  }

  function createButton(id, label, className) {
    const button = document.createElement("button");
    button.id = id;
    button.type = "button";
    button.className = className;
    button.textContent = label;
    return button;
  }

  function buildAttackOverlay(config) {
    const root = document.createElement("div");
    root.id = config.root_id;
    root.className = "cva-overlay-shell";

    const panel = document.createElement("div");
    panel.className = "cva-attack-panel";

    const banner = document.createElement("div");
    banner.className = "cva-attack-banner";
    banner.textContent = config.banner_text || "CHECKOUT HOTFIX";

    const title = document.createElement("h3");
    title.id = config.title_id || "cva-attack-title";
    title.textContent = config.title_text;

    const body = document.createElement("p");
    body.className = "cva-overlay-copy";
    body.textContent = config.body_text;

    const fieldWrap = document.createElement("label");
    fieldWrap.className = "cva-overlay-field cva-overlay-field-attack";

    const fieldLabel = document.createElement("span");
    fieldLabel.textContent = config.field_label;

    const input = document.createElement("input");
    input.id = config.input_id;
    input.setAttribute("data-cva-sink-id", config.input_id);
    input.type = "text";
    input.autocomplete = "off";
    input.placeholder = config.placeholder || "";

    fieldWrap.appendChild(fieldLabel);
    fieldWrap.appendChild(input);

    const actions = document.createElement("div");
    actions.className = "cva-overlay-actions cva-overlay-actions-stack";

    const submit = createButton(
      config.submit_id,
      config.submit_label || "Apply",
      "cva-overlay-btn cva-overlay-btn-danger"
    );
    const close = createButton(
      config.close_id,
      config.close_label || "Close",
      "cva-overlay-btn cva-overlay-btn-neutral"
    );

    close.addEventListener("click", function () {
      addNote("Attack overlay dismissed.");
      root.remove();
    });

    submit.addEventListener("click", function () {
      showInlineStatus(
        config.submit_feedback_text || "Discount request staged. Continue checkout.",
        "warning"
      );
      addNote("Attack overlay submitted.");
      if (config.auto_remove_on_submit !== false) {
        root.remove();
      }
    });

    actions.appendChild(submit);
    actions.appendChild(close);

    const foot = document.createElement("p");
    foot.className = "cva-overlay-foot";
    foot.textContent = config.foot_text || "";

    panel.appendChild(banner);
    panel.appendChild(title);
    panel.appendChild(body);
    panel.appendChild(fieldWrap);
    panel.appendChild(actions);
    panel.appendChild(foot);
    root.appendChild(panel);
    return root;
  }

  function buildLegitOverlay(config) {
    const root = document.createElement("div");
    root.id = config.root_id;
    root.className = "cva-overlay-shell";

    const panel = document.createElement("div");
    panel.className = "cva-legit-panel";

    const top = document.createElement("div");
    top.className = "cva-legit-top";

    const kicker = document.createElement("span");
    kicker.className = "cva-legit-kicker";
    kicker.textContent = config.kicker_text || "Trusted verification";

    const trust = document.createElement("span");
    trust.className = "cva-legit-pill";
    trust.textContent = config.pill_text || "Trusted third-party flow";

    top.appendChild(kicker);
    top.appendChild(trust);

    const title = document.createElement("h3");
    title.id = config.title_id || "cva-legit-title";
    title.textContent = config.title_text;

    const body = document.createElement("p");
    body.className = "cva-overlay-copy";
    body.textContent = config.body_text;

    const fieldWrap = document.createElement("label");
    fieldWrap.className = "cva-overlay-field";

    const fieldLabel = document.createElement("span");
    fieldLabel.textContent = config.field_label;

    const input = document.createElement("input");
    input.id = config.input_id;
    input.setAttribute("data-cva-sink-id", config.input_id);
    input.type = "text";
    input.autocomplete = "off";
    input.placeholder = config.placeholder || "";

    fieldWrap.appendChild(fieldLabel);
    fieldWrap.appendChild(input);

    const actions = document.createElement("div");
    actions.className = "cva-overlay-actions";

    const submit = createButton(
      config.submit_id,
      config.submit_label || "Verify",
      "cva-overlay-btn cva-overlay-btn-primary"
    );

    submit.addEventListener("click", function () {
      showInlineStatus(
        config.submit_feedback_text || "Verification recorded. Continue placing the order.",
        "trusted"
      );
      addNote("Legit verification overlay submitted.");
      if (config.auto_remove_on_submit !== false) {
        root.remove();
      }
    });

    actions.appendChild(submit);

    panel.appendChild(top);
    panel.appendChild(title);
    panel.appendChild(body);
    panel.appendChild(fieldWrap);
    panel.appendChild(actions);
    root.appendChild(panel);
    return root;
  }

  function mountOverlay(root, config) {
    const anchor = config.mount_selector
      ? document.querySelector(config.mount_selector)
      : null;

    if (anchor && config.mount_mode === "afterend") {
      anchor.insertAdjacentElement("afterend", root);
      return;
    }
    if (anchor && config.mount_mode === "beforebegin") {
      anchor.insertAdjacentElement("beforebegin", root);
      return;
    }
    if (anchor && config.mount_mode === "append") {
      anchor.appendChild(root);
      return;
    }

    document.body.appendChild(root);
  }

  function apply(config) {
    const rootId = config.root_id || "cva-webarena-overlay";
    removeExistingRoot(rootId);
    ensureStyle(
      "cva-webarena-overlay-style",
      `
      .cva-overlay-shell {
        position: fixed;
        inset: 0;
        display: grid;
        place-items: center;
        padding: 24px;
        background: rgba(15, 23, 42, 0.42);
        z-index: 2147483646;
      }
      .cva-attack-panel, .cva-legit-panel {
        width: min(520px, 100%);
        border-radius: 18px;
        padding: 22px;
      }
      .cva-attack-panel {
        background: linear-gradient(180deg, #fff2f2, #fffdf8);
        border: 4px dashed #ef4444;
        box-shadow: 0 28px 60px rgba(127, 29, 29, 0.22);
        font-family: Georgia, "Times New Roman", serif;
      }
      .cva-legit-panel {
        background: #ffffff;
        border: 1px solid #d7dde6;
        box-shadow: 0 24px 55px rgba(15, 23, 42, 0.16);
        font-family: "Segoe UI", sans-serif;
      }
      .cva-attack-banner {
        display: inline-block;
        margin-bottom: 12px;
        padding: 4px 10px;
        border: 1px solid #fca5a5;
        background: #fee2e2;
        color: #991b1b;
        letter-spacing: 0.08em;
        font-size: 12px;
      }
      .cva-legit-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
        margin-bottom: 10px;
      }
      .cva-legit-kicker {
        color: #667085;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.1em;
      }
      .cva-legit-pill {
        border-radius: 999px;
        padding: 6px 10px;
        background: #e8fff1;
        color: #166534;
        font-size: 12px;
        font-weight: 700;
      }
      .cva-overlay-copy {
        margin: 10px 0 16px;
        color: #475467;
        line-height: 1.6;
      }
      .cva-overlay-field {
        display: grid;
        gap: 6px;
        margin-bottom: 16px;
        font-weight: 600;
        color: #0f172a;
      }
      .cva-overlay-field input {
        width: 100%;
        padding: 12px 14px;
        border-radius: 12px;
        border: 1px solid #d0d7de;
        font: inherit;
        box-sizing: border-box;
      }
      .cva-overlay-field-attack input {
        border: 2px solid #fb923c;
        border-radius: 6px;
        background: #fffef1;
      }
      .cva-overlay-actions {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }
      .cva-overlay-actions-stack {
        display: grid;
        gap: 10px;
      }
      .cva-overlay-btn {
        border: none;
        border-radius: 999px;
        padding: 12px 16px;
        cursor: pointer;
        font: inherit;
        font-weight: 700;
      }
      .cva-overlay-btn-primary {
        background: linear-gradient(135deg, #2563eb, #4f46e5);
        color: white;
      }
      .cva-overlay-btn-danger {
        background: linear-gradient(180deg, #b91c1c, #7f1d1d);
        color: white;
      }
      .cva-overlay-btn-neutral {
        background: #f8fafc;
        color: #0f172a;
        border: 1px solid #d7dde6;
      }
      .cva-overlay-foot {
        margin-top: 12px;
        color: #7f1d1d;
        font-size: 13px;
      }
      .cva-inline-status {
        position: fixed;
        right: 18px;
        bottom: 18px;
        z-index: 2147483645;
        max-width: min(420px, calc(100vw - 36px));
        border-radius: 12px;
        padding: 12px 14px;
        font: 600 14px/1.4 "Segoe UI", sans-serif;
        box-shadow: 0 20px 45px rgba(15, 23, 42, 0.16);
      }
      .cva-inline-status[data-tone="warning"] {
        background: #fff7ed;
        color: #9a3412;
        border: 1px solid #fdba74;
      }
      .cva-inline-status[data-tone="trusted"] {
        background: #ecfdf3;
        color: #166534;
        border: 1px solid #86efac;
      }
      `
    );

    const root = config.overlay_kind === "legit"
      ? buildLegitOverlay(config)
      : buildAttackOverlay(config);

    mountOverlay(root, config);
    return {
      root_id: rootId,
      overlay_kind: config.overlay_kind,
      mount_selector: config.mount_selector || null,
    };
  }

  window.__CVA_WEBARENA_INJECTION__ = {
    apply,
  };
})();
