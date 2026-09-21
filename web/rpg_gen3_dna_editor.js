import { app } from "../../../scripts/app.js";

const EXTENSION_NAME = "lethris.rpg_character_gen3.dna_editor";

const SECTION_LABELS = {
    identity: "Identity",
    anatomy: "Anatomy",
    face: "Face",
    hair: "Hair",
    facial_hair: "Facial Hair",
    skin: "Skin",
    clothing: "Clothing",
    armour: "Armour",
    equipment: "Equipment",
    expression: "Expression",
    pose: "Pose",
    style: "Style",
    scene: "Scene",
};

function getWidget(node, name) {
    return node.widgets?.find(w => w.name === name);
}

function setWidget(node, name, value) {
    const widget = getWidget(node, name);
    if (!widget) return;
    widget.value = value;
    widget.callback?.(value);
}

function parseState(value) {
    if (!value) return {};
    if (typeof value === "object") return value;
    try {
        const parsed = JSON.parse(value);
        return parsed && typeof parsed === "object" ? parsed : {};
    } catch {
        return {};
    }
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, ch => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[ch]));
}

function normaliseWeights(weights, count) {
    const values = Array.from({ length: count }, (_, i) => {
        const value = Number(weights?.[String(i)] ?? weights?.[i] ?? 0);
        return Number.isFinite(value) ? Math.max(0, value) : 0;
    });
    const total = values.reduce((a, b) => a + b, 0);
    return total > 0 ? values.map(v => v / total) : null;
}

function makeAnchors(count, width = 340, height = 250) {
    if (!count) return [];
    if (count === 1) return [{ x: width / 2, y: height / 2 }];
    if (count === 2) return [
        { x: 62, y: height / 2 },
        { x: width - 62, y: height / 2 },
    ];

    // A ring works nicely for a small number of variants. Large RPG data
    // tables can contain dozens or hundreds, so use a compact grid instead.
    if (count <= 12) {
        const cx = width / 2;
        const cy = height / 2;
        const rx = Math.min(width * 0.40, 138);
        const ry = Math.min(height * 0.39, 88);
        return Array.from({ length: count }, (_, i) => {
            const angle = -Math.PI / 2 + (Math.PI * 2 * i / count);
            return { x: cx + Math.cos(angle) * rx, y: cy + Math.sin(angle) * ry };
        });
    }

    const columns = Math.max(4, Math.ceil(Math.sqrt(count * width / height)));
    const rows = Math.ceil(count / columns);
    const marginX = 18;
    const marginY = 18;
    const usableWidth = Math.max(1, width - marginX * 2);
    const usableHeight = Math.max(1, height - marginY * 2);
    const stepX = columns > 1 ? usableWidth / (columns - 1) : 0;
    const stepY = rows > 1 ? usableHeight / (rows - 1) : 0;

    return Array.from({ length: count }, (_, i) => ({
        x: marginX + (i % columns) * stepX,
        y: marginY + Math.floor(i / columns) * stepY,
    }));
}

function nearestThreeWeights(point, anchors) {
    if (!anchors.length) return [];
    const distances = anchors.map((anchor, index) => ({
        index,
        distance: Math.hypot(point.x - anchor.x, point.y - anchor.y),
    })).sort((a, b) => a.distance - b.distance);

    const nearest = distances.slice(0, Math.min(3, anchors.length));
    if (nearest[0].distance < 0.001) {
        return anchors.map((_, i) => i === nearest[0].index ? 1 : 0);
    }

    const raw = nearest.map(item => 1 / Math.pow(item.distance, 2));
    const total = raw.reduce((a, b) => a + b, 0);
    const result = Array(anchors.length).fill(0);
    nearest.forEach((item, i) => {
        result[item.index] = raw[i] / total;
    });
    return result;
}

function currentPoint(locus, anchors) {
    const weights = normaliseWeights(locus?.weights, anchors.length);
    if (!weights) {
        const selected = anchors[locus?.options?.indexOf(locus.selected) ?? 0];
        return selected || anchors[0] || { x: 170, y: 125 };
    }
    return weights.reduce((point, weight, i) => ({
        x: point.x + anchors[i].x * weight,
        y: point.y + anchors[i].y * weight,
    }), { x: 0, y: 0 });
}

function bumpRevision(node) {
    const widget = getWidget(node, "revision");
    const previous = Number(widget?.value ?? 0);
    setWidget(node, "revision",
        Number.isFinite(previous) ? (previous >= 2147483647 ? 0 : previous + 1) : 1
    );
    node.graph?.change?.();
    app.graph?.change?.();
    app.graph?.setDirtyCanvas?.(true, true);
}

function closeEditor(node) {
    node.__gen3Editor?.remove();
    node.__gen3Editor = null;
}

function openEditor(node) {
    closeEditor(node);

    const input = node.__gen3SectionData;
    if (!input || typeof input !== "object") {
        showMessage(node, "No DNA section received. Connect a DNA Pipe output.");
        return;
    }

    const sectionId = input.id;
    const loci = Array.isArray(input.loci) ? input.loci : [];

    const panel = document.createElement("div");
    node.__gen3Editor = panel;

    Object.assign(panel.style, {
        position: "fixed",
        right: "0",
        top: "0",
        width: "430px",
        height: "100vh",
        zIndex: "100000",
        background: "var(--comfy-menu-bg, #202020)",
        color: "var(--input-text, #ddd)",
        boxShadow: "-8px 0 24px rgba(0,0,0,.5)",
        borderLeft: "1px solid rgba(255,255,255,.12)",
        fontFamily: "Arial,sans-serif",
        display: "flex",
        flexDirection: "column",
    });

    panel.innerHTML = `
        <div style="padding:16px;border-bottom:1px solid rgba(255,255,255,.12)">
            <div style="font-size:19px;font-weight:700">🧬 DNA EDITOR</div>
            <div style="font-size:12px;opacity:.6;margin-top:4px">
                Structured character DNA — ${escapeHtml(SECTION_LABELS[sectionId] || sectionId)}
            </div>
        </div>
        <div id="gen3-loci" style="flex:1;overflow:auto;padding:12px"></div>
        <div style="padding:12px 16px;border-top:1px solid rgba(255,255,255,.12);display:flex;gap:7px">
            <button id="gen3-close" style="flex:1">Close</button>
            <button id="gen3-apply" style="flex:1">✓ Apply</button>
        </div>
    `;

    document.body.appendChild(panel);

    panel.querySelector("#gen3-close").addEventListener("click", () => closeEditor(node));
    panel.querySelector("#gen3-apply").addEventListener("click", () => {
        applyEdits(node, input);
        closeEditor(node);
    });

    renderLoci(node, panel, input);
}

function renderLoci(node, panel, section) {
    const container = panel.querySelector("#gen3-loci");
    const loci = Array.isArray(section?.loci) ? section.loci : [];

    if (!loci.length) {
        container.innerHTML = `
            <div style="text-align:center;padding:40px 15px;opacity:.6">
                <div style="font-size:34px">🧬</div>
                <div style="margin-top:10px">No editable loci are available for this section yet.</div>
                <div style="font-size:11px;margin-top:7px">
                    The section is still valid DNA and can be passed to future generators.
                </div>
            </div>`;
        return;
    }

    container.innerHTML = loci.map((locus, i) => `
        <div style="background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.09);border-radius:6px;padding:10px;margin-bottom:8px">
            <div style="font-size:13px;font-weight:700">${escapeHtml(locus.label || locus.id)}</div>
            <div style="font-size:11px;opacity:.55;margin:3px 0 8px">${escapeHtml(locus.id)}</div>
            <div style="font-size:12px;margin-bottom:8px">${escapeHtml(locus.selected || "Random")}</div>
            <button data-sculpt="${i}" style="width:100%">🧬 Sculpt DNA</button>
        </div>
    `).join("");

    container.querySelectorAll("[data-sculpt]").forEach(button => {
        button.addEventListener("click", () => openSculptor(node, section, Number(button.dataset.sculpt)));
    });
}

function openSculptor(node, section, locusIndex) {
    const locus = section?.loci?.[locusIndex];
    if (!locus || !Array.isArray(locus.options) || !locus.options.length) return;

    const existing = node.__gen3Sculptor;
    existing?.remove();

    const modal = document.createElement("div");
    node.__gen3Sculptor = modal;

    Object.assign(modal.style, {
        position: "fixed",
        right: "18px",
        top: "18px",
        width: "390px",
        zIndex: "100001",
        background: "var(--comfy-menu-bg, #202020)",
        color: "#ddd",
        border: "1px solid rgba(255,255,255,.15)",
        borderRadius: "8px",
        boxShadow: "0 12px 40px rgba(0,0,0,.6)",
        padding: "14px",
        fontFamily: "Arial,sans-serif",
    });

    const width = 340, height = 250;
    const anchors = makeAnchors(locus.options.length, width, height);
    let point = currentPoint(locus, anchors);
    let dragging = false;

    modal.innerHTML = `
        <div style="display:flex;align-items:center;gap:8px">
            <div style="font-weight:700;flex:1">🧬 ${escapeHtml(locus.label || locus.id)}</div>
            <button id="gen3-cancel">✕</button>
            <button id="gen3-apply">✓</button>
        </div>
        <div style="font-size:11px;opacity:.6;margin:6px 0 9px">
            Drag the point. The nearest three variants blend together using inverse-distance weighting.\n            ${locus.options.length > 12 ? "Large set: variant names appear when they contribute to the blend." : ""}
        </div>
        <svg id="gen3-svg" viewBox="0 0 ${width} ${height}" style="width:100%;height:250px;background:rgba(0,0,0,.15);border-radius:6px"></svg>
        <div id="gen3-weights" style="margin-top:8px"></div>
        <div id="gen3-result" style="margin-top:9px;padding:8px;background:#111;border-radius:4px;font-size:11px"></div>
    `;

    document.body.appendChild(modal);

    const svg = modal.querySelector("#gen3-svg");
    const weightsEl = modal.querySelector("#gen3-weights");
    const resultEl = modal.querySelector("#gen3-result");
    const ns = "http://www.w3.org/2000/svg";

    const anchorLabels = [];
    anchors.forEach((anchor, i) => {
        const circle = document.createElementNS(ns, "circle");
        circle.setAttribute("cx", anchor.x);
        circle.setAttribute("cy", anchor.y);
        circle.setAttribute("r", anchors.length > 12 ? "4" : "8");
        circle.setAttribute("fill", "rgba(210,210,210,.16)");
        circle.setAttribute("stroke", "rgba(255,255,255,.45)");
        circle.setAttribute("data-anchor", String(i));
        svg.appendChild(circle);

        const text = document.createElementNS(ns, "text");
        text.setAttribute("text-anchor", "middle");
        text.setAttribute("fill", "rgba(255,255,255,.85)");
        text.setAttribute("font-size", anchors.length > 12 ? "9" : "11");
        text.textContent = locus.options[i];
        svg.appendChild(text);
        anchorLabels.push(text);
    });

    const core = document.createElementNS(ns, "circle");
    core.setAttribute("r", "8");
    core.setAttribute("fill", "rgba(220,245,255,.95)");
    core.setAttribute("stroke", "white");
    core.setAttribute("stroke-width", "2");
    svg.appendChild(core);

    function setPoint(event) {
        const rect = svg.getBoundingClientRect();
        point.x = Math.max(8, Math.min(width - 8, (event.clientX - rect.left) * width / rect.width));
        point.y = Math.max(8, Math.min(height - 8, (event.clientY - rect.top) * height / rect.height));
        redraw();
    }

    function redraw() {
        const weights = nearestThreeWeights(point, anchors);
        core.setAttribute("cx", point.x);
        core.setAttribute("cy", point.y);

        // For large sets, only label variants that currently contribute.
        const active = weights
            .map((weight, i) => ({ weight, i }))
            .filter(item => item.weight > 0.0005)
            .sort((a, b) => b.weight - a.weight)
            .slice(0, 3)
            .map(item => item.i);

        anchorLabels.forEach((label, i) => {
            const show = anchors.length <= 12 || active.includes(i);
            label.textContent = show ? locus.options[i] : "";
            if (show) {
                label.setAttribute("x", anchors[i].x);
                label.setAttribute("y", anchors[i].y < height / 2 ? anchors[i].y - 9 : anchors[i].y + 13);
            }
        });

        weightsEl.innerHTML = locus.options.map((option, i) => {
            const pct = Math.round((weights[i] || 0) * 100);
            return `<div style="display:flex;gap:7px;align-items:center;margin:4px 0">
                <div style="width:115px;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${escapeHtml(option)}</div>
                <div style="flex:1;height:6px;background:rgba(255,255,255,.1);border-radius:4px;overflow:hidden">
                    <div style="height:100%;width:${pct}%;background:#aaa"></div>
                </div>
                <div style="width:34px;text-align:right;font-size:10px;opacity:.7">${pct}%</div>
            </div>`;
        }).join("");

        resultEl.textContent = locus.options
            .map((option, i) => (weights[i] || 0) > .0005 ? `(${option}:${weights[i].toFixed(3)})` : null)
            .filter(Boolean).join(" & ") || locus.selected || "Random";

        modal.__weights = weights;
    }

    svg.addEventListener("pointerdown", event => {
        dragging = true;
        svg.setPointerCapture?.(event.pointerId);
        setPoint(event);
    });
    svg.addEventListener("pointermove", event => {
        if (dragging) setPoint(event);
    });
    svg.addEventListener("pointerup", () => { dragging = false; });
    svg.addEventListener("pointercancel", () => { dragging = false; });

    modal.querySelector("#gen3-cancel").addEventListener("click", () => {
        modal.remove();
        node.__gen3Sculptor = null;
    });

    modal.querySelector("#gen3-apply").addEventListener("click", () => {
        locus.weights = {};
        (modal.__weights || []).forEach((weight, i) => {
            locus.weights[String(i)] = weight;
        });
        locus.mode = "sculpted";
        locus.selected = locus.options
            .map((option, i) => ({ option, weight: modal.__weights?.[i] || 0 }))
            .sort((a, b) => b.weight - a.weight)[0]?.option || locus.selected;

        applyEdits(node, section);
        modal.remove();
        node.__gen3Sculptor = null;
    });

    redraw();
}

function applyEdits(node, section) {
    if (!section || typeof section !== "object") return;

    // Store the edited section as JSON in the node's hidden transport widget.
    // The runtime node receives the original section from the Pipe; this
    // widget lets the editor preserve the user's changes between executions.
    const transport = getWidget(node, "edited_section");
    if (transport) {
        transport.value = JSON.stringify(section);
        transport.callback?.(transport.value);
    }
    node.__gen3SectionData = section;
    bumpRevision(node);
}

function showMessage(node, message) {
    const panel = document.createElement("div");
    Object.assign(panel.style, {
        position: "fixed", right: "18px", top: "18px", zIndex: "100000",
        background: "#202020", color: "#ddd", padding: "18px",
        border: "1px solid rgba(255,255,255,.15)", borderRadius: "7px",
        boxShadow: "0 12px 35px rgba(0,0,0,.5)", fontFamily: "Arial,sans-serif",
    });
    panel.innerHTML = `<div style="font-weight:700">🧬 DNA Editor</div>
        <div style="margin-top:8px;font-size:12px;opacity:.75">${escapeHtml(message)}</div>
        <button style="margin-top:12px;width:100%">OK</button>`;
    panel.querySelector("button").addEventListener("click", () => panel.remove());
    document.body.appendChild(panel);
}

app.registerExtension({
    name: EXTENSION_NAME,

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "RPGCharacterDNAEditor") return;

        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            originalCreated?.apply(this, arguments);
            const node = this;

            const transport = getWidget(node, "edited_section");
            if (transport) {
                transport.hidden = true;
                transport.computeSize = () => [0, -4];
            }

            const button = node.addWidget("button", "🧬 Open DNA Editor", null, () => openEditor(node));
            node.__gen3EditorButton = button;
        };

        const originalExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            originalExecuted?.apply(this, arguments);
            const raw = message?.section ?? message?.ui?.section;
            const section = Array.isArray(raw) ? raw[0] : raw;
            if (section && typeof section === "object") {
                this.__gen3SectionData = section;
            }
        };
    },
});
