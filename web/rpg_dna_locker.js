import { app } from "../../../scripts/app.js";

const EXTENSION_NAME = "lethris.rpg_character_selector.dna_locker";

function getWidget(node, name) {
    return node.widgets?.find(w => w.name === name);
}

function setWidgetValue(node, name, value) {
    const widget = getWidget(node, name);
    if (!widget) return;
    widget.value = value;
    widget.callback?.(value);
}

function randomSeed() {
    return Math.floor(Math.random() * 0x100000000);
}

// Lightweight deterministic hash for immediate client-side previews. The
// selected preview is persisted in dna_rerolls, so the backend will use
// exactly what the user sees when Run is pressed.
function previewIndex(seed, locusId, count) {
    if (!count) return 0;
    let h = (Number(seed) >>> 0) ^ 0x9e3779b9;
    const text = String(locusId);
    for (let i = 0; i < text.length; i++) {
        h ^= text.charCodeAt(i);
        h = Math.imul(h, 16777619);
        h ^= h >>> 13;
    }
    h = Math.imul(h ^ (h >>> 16), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    h ^= h >>> 16;
    return (h >>> 0) % count;
}

function refreshAllRandomPreviews(node, seed) {
    const groups = node.__dnaGroups || [];
    node.__dnaRerolls = {};
    node.__dnaSelections = {};
    for (const group of groups) {
        if (!Array.isArray(group.options) || !group.options.length) continue;
        const index = previewIndex(seed, group.id, group.options.length);
        const preview = group.options[index];
        node.__dnaRerolls[group.id] = { count: 0, avoid: null, preview };
        node.__dnaSelections[group.id] = preview;
        group.selected = preview;
    }
}

function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, ch => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    }[ch]));
}

const DNA_QUOTES = [
    '“Life finds a way.” — Dr. Ian Malcolm',
    '“Do not meddle in the affairs of wizards…” — A very sensible wizard',
    '“The mixture is stable. Probably.” — Anonymous Alchemist',
    '“By my calculations, this should only explode a little.” — Apprentice Alchemist',
    '“Randomness is merely destiny with better paperwork.” — The Archivist',
    '“One does not simply reroll the paladin.” — Some unfortunate party member',
    '“The dice know what you are. We merely document it.” — Dungeon Master',
    '“A wizard is never late. Their initiative roll is merely complicated.” — Arcane proverb',
    '“There are no mistakes, only highly experimental character builds.” — Alchemical proverb',
    '“Your character has been genetically… adventurously optimised.” — The Locker',
];

function randomDnaQuote() {
    return DNA_QUOTES[Math.floor(Math.random() * DNA_QUOTES.length)];
}

function normaliseWeights(weights, count) {
    const values = Array.from({ length: count }, (_, i) => {
        const v = Number(weights?.[String(i)] ?? weights?.[i] ?? 0);
        return Number.isFinite(v) ? Math.max(0, v) : 0;
    });
    const total = values.reduce((a, b) => a + b, 0);
    return total > 0 ? values.map(v => v / total) : null;
}


function pickRerollVariant(group, previous) {
    const options = Array.isArray(group?.options) ? group.options : [];
    if (!options.length) return previous ?? group?.selected ?? "";
    const alternatives = options.filter(option => option !== previous);
    const pool = alternatives.length ? alternatives : options;
    return pool[Math.floor(Math.random() * pool.length)];
}

function rerollStateFor(node, id, selected) {
    const state = node.__dnaRerolls?.[id];
    const count = typeof state === "object"
        ? Number(state.count || 0)
        : Number(state || 0);
    return {
        count: (Number.isFinite(count) ? Math.max(0, Math.floor(count)) : 0) + 1,
        avoid: selected,
        preview: pickRerollVariant(node.__dnaGroups?.find(g => g.id === id), selected),
    };
}

function weightedDescription(options, weights) {
    const normalised = normaliseWeights(weights, options.length);
    if (!normalised) return "Random";
    return options
        .map((option, i) => ({ option, weight: normalised[i] }))
        .filter(x => x.weight > 0.0005)
        .map(x => `${x.option} ${(x.weight * 100).toFixed(0)}%`)
        .join(" / ");
}

app.registerExtension({
    name: EXTENSION_NAME,

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "RPGCharacterSelector") return;

        const originalOnNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            originalOnNodeCreated?.apply(this, arguments);

            const node = this;
            node.__dnaGroups = [];
            node.__dnaWeights = {};
            node.__dnaPreviewWeights = {};
            node.__dnaRerolls = {};
            node.__dnaSelections = {};
            node.__dnaDrawer = null;
            node.__dnaEditor = null;
            node.__dnaQuote = null;

            // Keep the transport widgets in the graph so the state is saved
            // with the workflow, but hide them from the normal node UI.
            for (const name of ["dna_seed", "dna_revision", "dna_locks", "dna_weights", "dna_rerolls"]) {
                const widget = getWidget(node, name);
                if (widget) {
                    widget.hidden = true;
                    widget.computeSize = () => [0, -4];
                }
            }

            const lockerButton = node.addWidget(
                "button",
                "🧬 DNA Locker",
                null,
                () => toggleDrawer(node)
            );

            // Move the button to the top of the widget stack.
            const index = node.widgets.indexOf(lockerButton);
            if (index > 0) {
                node.widgets.splice(index, 1);
                node.widgets.unshift(lockerButton);
            }

            node.__dnaLockerButton = lockerButton;
            node.setDirtyCanvas(true, true);
        };

        const originalOnExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            originalOnExecuted?.apply(this, arguments);

            // ComfyUI sends custom UI fields as arrays.  Accept both the
            // current list form and the older/direct-object form so the
            // locker remains tolerant of cached outputs and frontend changes.
            const rawDna = message?.dna ?? message?.ui?.dna ?? message?.output?.dna;
            const dna = Array.isArray(rawDna) ? rawDna[0] : rawDna;
            if (!dna || typeof dna !== "object") return;

            // If the backend had to materialise the initial -1 seed, persist
            // that actual seed back into the hidden widget. Otherwise the
            // Locker would display a fresh fake random number every time it
            // redraws, and the backend would keep seeing -1 on later queues.
            if (Number.isFinite(Number(dna.seed))) {
                const seedWidget = getWidget(this, "dna_seed");
                if (seedWidget && Number(seedWidget.value) !== Number(dna.seed)) {
                    seedWidget.value = Number(dna.seed);
                }
            }

            this.__dnaGroups = Array.isArray(dna.groups) ? dna.groups : [];
            const storedLocks = parseState(getWidget(this, "dna_locks")?.value);
            const embeddedRerolls = parseState(storedLocks.__dna_rerolls);
            this.__dnaWeights = parseState(getWidget(this, "dna_weights")?.value);
            this.__dnaPreviewWeights = {};
            const explicitRerolls = parseState(getWidget(this, "dna_rerolls")?.value);
            this.__dnaRerolls = Object.keys(explicitRerolls).length
                ? explicitRerolls
                : embeddedRerolls;
            // Execution is the authoritative backend result.  Clear any
            // client-side preview overrides now that the node has caught up.
            this.__dnaSelections = {};

            if (this.__dnaDrawer) {
                renderDrawer(this);
            }
        };
    },
});

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

function saveState(node) {
    const rerolls = node.__dnaRerolls || {};

    // dna_locks is retained only as a compatibility transport for older
    // workflow payloads. The V2.4 UI no longer exposes or uses lock state.
    setWidgetValue(node, "dna_locks", JSON.stringify(
        Object.keys(rerolls).length ? { __dna_rerolls: rerolls } : {}
    ));
    setWidgetValue(node, "dna_weights", JSON.stringify(node.__dnaWeights || {}));
    setWidgetValue(node, "dna_rerolls", JSON.stringify(rerolls));

    // Force ComfyUI/LiteGraph to see DNA edits as execution-input changes.
    const revisionWidget = getWidget(node, "dna_revision");
    const previousRevision = Number(revisionWidget?.value ?? 0);
    const nextRevision = Number.isFinite(previousRevision)
        ? (previousRevision >= 2147483647 ? 0 : Math.floor(previousRevision) + 1)
        : 1;
    setWidgetValue(node, "dna_revision", nextRevision);

    node.setDirtyCanvas?.(true, true);
    node.graph?.change?.();
    app.graph?.change?.();
    app.graph?.setDirtyCanvas?.(true, true);
}


function closeDrawer(node) {
    if (node.__dnaEditorGroupId) {
        delete node.__dnaPreviewWeights?.[node.__dnaEditorGroupId];
    }
    if (node.__dnaDrawer) {
        node.__dnaDrawer.remove();
        node.__dnaDrawer = null;
    }
    node.__dnaEditor = null;
    node.__dnaEditorGroupId = null;
}

function toggleDrawer(node) {
    if (node.__dnaDrawer) {
        closeDrawer(node);
        return;
    }

    const drawer = document.createElement("div");
    drawer.className = "rpg-dna-drawer";
    node.__dnaQuote = randomDnaQuote();
    Object.assign(drawer.style, {
        position: "fixed",
        top: "0",
        right: "0",
        width: "390px",
        height: "100vh",
        zIndex: "100000",
        background: "var(--comfy-menu-bg, #202020)",
        color: "var(--input-text, #ddd)",
        boxShadow: "-8px 0 24px rgba(0,0,0,.45)",
        borderLeft: "1px solid rgba(255,255,255,.12)",
        fontFamily: "Arial, sans-serif",
        display: "flex",
        flexDirection: "column",
    });

    node.__dnaDrawer = drawer;
    document.body.appendChild(drawer);
    renderDrawer(node);
}

function renderDrawer(node) {
    const drawer = node.__dnaDrawer;
    if (!drawer) return;

    const seedWidget = getWidget(node, "dna_seed");
    const rawSeed = Number(seedWidget?.value ?? -1);
    const seed = Number.isFinite(rawSeed) && rawSeed >= 0 ? rawSeed : null;

    const groups = node.__dnaGroups || [];

    drawer.innerHTML = `
        <div style="padding:16px 16px 12px; border-bottom:1px solid rgba(255,255,255,.12);">
            <div style="font-size:19px;font-weight:700;">🧬 DNA LOCKER</div>
            <div style="font-size:12px;opacity:.65;margin-top:4px;">
                Reproducible character DNA &amp; variant control
            </div>
            <div style="font-size:11px;line-height:1.45;margin-top:9px;padding:8px 9px;border-left:2px solid rgba(255,255,255,.22);background:rgba(255,255,255,.035);border-radius:0 4px 4px 0;font-style:italic;opacity:.78;">
                ${escapeHtml(node.__dnaQuote || randomDnaQuote())}
            </div>
        </div>

        <div style="padding:12px 16px;border-bottom:1px solid rgba(255,255,255,.12);">
            <div style="font-size:11px;text-transform:uppercase;opacity:.65;margin-bottom:6px;">Master Seed</div>
            <div style="display:flex;gap:6px;">
                <input id="rpg-dna-seed" type="number" min="0" max="4294967295"
                    value="${seed !== null ? seed : ""}"
                    placeholder="Random seed will be assigned on first Run"
                    style="flex:1;min-width:0;background:#111;color:#eee;border:1px solid #555;border-radius:4px;padding:7px;">
                <button id="rpg-dna-random" title="Generate a new seed">🎲</button>
                <button id="rpg-dna-apply" title="Apply seed">✓</button>
            </div>
            <div style="font-size:11px;opacity:.55;margin-top:6px;">
                Master seed anchors the DNA sequence. Re-roll changes one trait; Sculpt gives you direct control.
            </div>
        </div>

        <div id="rpg-dna-groups" style="flex:1;overflow:auto;padding:10px 12px;">
            ${renderGroups(node, groups)}
        </div>

        <div style="padding:10px 16px;border-top:1px solid rgba(255,255,255,.12);font-size:11px;opacity:.55;">
            🎲 re-rolls a trait &nbsp; • &nbsp; 🧬 opens the DNA sculptor
        </div>
    `;

    drawer.querySelector("#rpg-dna-random")?.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const value = randomSeed();
        drawer.querySelector("#rpg-dna-seed").value = value;
        setWidgetValue(node, "dna_seed", value);
        node.__dnaWeights = {};
        node.__dnaPreviewWeights = {};
        refreshAllRandomPreviews(node, value);
        saveState(node);
        renderDrawer(node);
    });

    drawer.querySelector("#rpg-dna-apply")?.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const value = Number(drawer.querySelector("#rpg-dna-seed").value);
        if (!Number.isFinite(value)) return;
        const seed = Math.max(0, Math.min(4294967295, Math.floor(value)));
        setWidgetValue(node, "dna_seed", seed);
        node.__dnaWeights = {};
        node.__dnaPreviewWeights = {};
        refreshAllRandomPreviews(node, seed);
        saveState(node);
        renderDrawer(node);
    });

    bindGroupActions(node, drawer);
}

function refreshGroupCards(node) {
    const groupsEl = node.__dnaDrawer?.querySelector("#rpg-dna-groups");
    if (!groupsEl) return;
    groupsEl.innerHTML = renderGroups(node, node.__dnaGroups || []);
    bindGroupActions(node, groupsEl);
}

function bindGroupActions(node, root) {
    root.querySelectorAll("[data-dna-sculpt]").forEach(button => {
        button.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            const group = (node.__dnaGroups || []).find(g => g.id === button.dataset.dnaSculpt);
            if (group) openSculptor(node, group);
        });
    });

    root.querySelectorAll("[data-dna-reroll]").forEach(button => {
        button.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            const id = button.dataset.dnaReroll;
            const group = (node.__dnaGroups || []).find(g => g.id === id);
            if (!group) return;

            const current = node.__dnaSelections[id] ?? group.selected;
            delete node.__dnaWeights[id];
            delete node.__dnaPreviewWeights?.[id];

            node.__dnaRerolls[id] = rerollStateFor(node, id, current);
            node.__dnaSelections[id] = node.__dnaRerolls[id].preview;
            group.selected = node.__dnaSelections[id];

            saveState(node);
            renderDrawer(node);
        });
    });
}

function renderGroups(node, groups) {
    if (!groups.length) {
        return `
            <div style="padding:22px 8px;text-align:center;opacity:.65;">
                <div style="font-size:30px;">🧬</div>
                <div style="margin-top:8px;">No random DNA loci were found.</div>
                <div style="font-size:11px;margin-top:5px;">
                    Fixed options such as Orc or Half-Orc simply have no DNA controls.
                </div>
            </div>
        `;
    }

    const byField = {};
    for (const group of groups) {
        (byField[group.field] ||= []).push(group);
    }

    return Object.entries(byField).map(([field, fieldGroups]) => `
        <div style="margin-bottom:14px;">
            <div style="font-weight:700;font-size:13px;padding:5px 4px;opacity:.9;">${escapeHtml(field)}</div>
            ${fieldGroups.map(group => {
                const committedWeights = node.__dnaWeights[group.id];
                const previewWeights = node.__dnaPreviewWeights?.[group.id];
                const activeWeights = previewWeights || committedWeights;
                const sculpted = !!activeWeights;
                const rerollState = node.__dnaRerolls[group.id];
                const rerollPreview = rerollState && typeof rerollState === "object"
                    ? rerollState.preview
                    : null;
                const mode = sculpted ? "sculpted" : "random";
                const liveSelection = node.__dnaSelections[group.id];
                const selected = sculpted
                    ? weightedDescription(group.options, activeWeights)
                    : liveSelection && group.options.includes(liveSelection)
                        ? liveSelection
                        : (rerollPreview && group.options.includes(rerollPreview))
                            ? rerollPreview
                            : group.selected;

                return `
                    <div style="background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.09);border-radius:6px;padding:9px;margin:5px 0;">
                        <div style="display:flex;align-items:center;gap:6px;">
                            <div style="flex:1;font-size:12px;font-weight:600;">${escapeHtml(group.label)}</div>
                            <span style="font-size:10px;opacity:.55;">${mode === "sculpted" ? "🧬 SCULPTED" : "RANDOM"}</span>
                        </div>
                        <div style="font-size:12px;margin:7px 0;color:#fff;">${escapeHtml(selected)}</div>
                        <div style="display:flex;gap:5px;">
                            <button type="button" data-dna-reroll="${escapeHtml(group.id)}" title="Reroll this DNA locus" style="flex:1;">🎲 Re-roll</button>
                            <button type="button" data-dna-sculpt="${escapeHtml(group.id)}" title="Open DNA sculptor" style="flex:1;">🧬 Sculpt</button>
                        </div>
                    </div>
                `;
            }).join("")}
        </div>
    `).join("");
}

function makeAnchorPositions(count, width = 340, height = 250) {
    if (count <= 0) return [];
    if (count === 1) return [{ x: width / 2, y: height / 2 }];
    if (count === 2) return [
        { x: 62, y: height / 2 },
        { x: width - 62, y: height / 2 },
    ];

    const cx = width / 2;
    const cy = height / 2;
    const rx = Math.min(width * 0.40, 138);
    const ry = Math.min(height * 0.39, 88);
    const offset = -Math.PI / 2;
    return Array.from({ length: count }, (_, i) => {
        const angle = offset + (Math.PI * 2 * i / count);
        return {
            x: cx + Math.cos(angle) * rx,
            y: cy + Math.sin(angle) * ry,
        };
    });
}

function pointFromWeights(group, weights, anchors) {
    const normalised = normaliseWeights(weights, group.options.length);
    if (!normalised) return { x: 170, y: 125 };

    let x = 0;
    let y = 0;
    let total = 0;
    normalised.forEach((weight, i) => {
        if (anchors[i]) {
            x += anchors[i].x * weight;
            y += anchors[i].y * weight;
            total += weight;
        }
    });
    return total > 0 ? { x: x / total, y: y / total } : { x: 170, y: 125 };
}

function nearestThreeWeights(point, anchors) {
    if (!anchors.length) return [];
    if (anchors.length === 1) return [1];

    const distances = anchors.map((anchor, index) => ({
        index,
        distance: Math.hypot(point.x - anchor.x, point.y - anchor.y),
    })).sort((a, b) => a.distance - b.distance);

    const nearest = distances.slice(0, Math.min(3, anchors.length));
    if (nearest[0].distance < 0.001) {
        return anchors.map((_, i) => i === nearest[0].index ? 1 : 0);
    }

    // Inverse-distance weighting gives a smooth "DNA gravity" field while
    // deliberately discarding every option outside the nearest three.
    const raw = nearest.map(item => 1 / Math.pow(item.distance, 2));
    const total = raw.reduce((a, b) => a + b, 0);
    const weights = Array(anchors.length).fill(0);
    nearest.forEach((item, i) => {
        weights[item.index] = raw[i] / total;
    });
    return weights;
}

function formatWeight(value) {
    return Number(value).toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
}

function openSculptor(node, group) {
    if (!node.__dnaDrawer) return;

    const existing = node.__dnaEditor;
    if (existing) {
        delete node.__dnaPreviewWeights?.[node.__dnaEditorGroupId];
        existing.remove();
        node.__dnaEditor = null;
        node.__dnaEditorGroupId = null;
        refreshGroupCards(node);
    }

    const editor = document.createElement("div");
    node.__dnaEditor = editor;
    node.__dnaEditorGroupId = group.id;

    Object.assign(editor.style, {
        position: "absolute",
        left: "0",
        right: "0",
        bottom: "0",
        maxHeight: "82vh",
        overflow: "auto",
        background: "var(--comfy-menu-bg, #202020)",
        borderTop: "1px solid rgba(255,255,255,.15)",
        boxShadow: "0 -10px 30px rgba(0,0,0,.5)",
        padding: "14px 16px 18px",
        zIndex: "5",
    });

    const width = 340;
    const height = 250;
    const anchors = makeAnchorPositions(group.options.length, width, height);
    const currentWeights = node.__dnaPreviewWeights?.[group.id] || node.__dnaWeights[group.id];
    const startPoint = currentWeights
        ? pointFromWeights(group, currentWeights, anchors)
        : (anchors[group.options.indexOf(group.selected)] || anchors[0]);

    editor.innerHTML = `
        <style>
            .rpg-dna-space { position:relative; width:100%; max-width:${width}px; height:${height}px; margin:8px auto 10px; }
            .rpg-dna-space svg { width:100%; height:100%; display:block; overflow:visible; }
            .rpg-dna-anchor { fill:rgba(210,210,210,.12); stroke:rgba(255,255,255,.35); stroke-width:1.5; }
            .rpg-dna-anchor.active { fill:rgba(190,235,255,.22); stroke:rgba(210,245,255,.9); }
            .rpg-dna-label { font:11px Arial,sans-serif; fill:rgba(255,255,255,.82); pointer-events:none; }
            .rpg-dna-link { stroke:rgba(180,225,255,.75); stroke-width:1.5; stroke-dasharray:5 4; opacity:0; }
            .rpg-dna-link.active { animation:rpg-dna-link-pulse .75s ease-out; }
            @keyframes rpg-dna-link-pulse { 0% { opacity:0; stroke-width:3; } 18% { opacity:1; } 100% { opacity:.18; stroke-width:1.2; } }
            .rpg-dna-core { fill:rgba(220,245,255,.96); stroke:rgba(255,255,255,.95); stroke-width:2; filter:drop-shadow(0 0 6px rgba(170,225,255,.9)); cursor:grab; }
            .rpg-dna-core.dragging { cursor:grabbing; }
            .rpg-dna-spark { fill:rgba(225,250,255,.95); opacity:0; pointer-events:none; }
            .rpg-dna-hint { text-align:center; font-size:10px; opacity:.5; margin-top:-4px; }
        </style>
        <div style="display:flex;align-items:center;gap:8px;">
            <div style="font-weight:700;flex:1;">🧬 ${escapeHtml(group.label)}</div>
            <button id="rpg-dna-cancel" title="Cancel sculpting" style="min-width:34px;color:#f99;">✕</button>
            <button id="rpg-dna-apply-sculpt" title="Apply sculpted DNA" style="min-width:34px;color:#9f9;font-weight:700;">✓</button>
        </div>
        <div style="font-size:11px;opacity:.6;margin:5px 0 8px;">
            Move the DNA point. It blends the <b>nearest three</b> variants.
            The closer the point is to a variant, the stronger its influence.
            Changes preview live in the Locker. <b>✓</b> applies them; <b>✕</b> cancels them.
        </div>
        <div class="rpg-dna-space">
            <svg id="rpg-dna-svg" viewBox="0 0 ${width} ${height}" aria-label="DNA sculpting space"></svg>
        </div>
        <div class="rpg-dna-hint">✨ Drag the point through the DNA field</div>
        <div id="rpg-dna-options" style="margin-top:10px;"></div>
        <div id="rpg-dna-result" style="margin-top:10px;padding:9px;background:#111;border-radius:4px;font-size:11px;word-break:break-word;"></div>
    `;

    node.__dnaDrawer.appendChild(editor);

    const svg = editor.querySelector("#rpg-dna-svg");
    const optionsEl = editor.querySelector("#rpg-dna-options");
    const result = editor.querySelector("#rpg-dna-result");
    const ns = "http://www.w3.org/2000/svg";

    const links = anchors.map((_, i) => {
        const line = document.createElementNS(ns, "line");
        line.classList.add("rpg-dna-link");
        line.dataset.index = String(i);
        svg.appendChild(line);
        return line;
    });

    anchors.forEach((anchor, i) => {
        const circle = document.createElementNS(ns, "circle");
        circle.classList.add("rpg-dna-anchor");
        circle.setAttribute("cx", anchor.x);
        circle.setAttribute("cy", anchor.y);
        circle.setAttribute("r", 8);
        circle.dataset.index = String(i);
        svg.appendChild(circle);

        const label = document.createElementNS(ns, "text");
        label.classList.add("rpg-dna-label");
        label.setAttribute("x", anchor.x);
        label.setAttribute("y", anchor.y + (anchor.y < height / 2 ? -13 : 23));
        label.setAttribute("text-anchor", "middle");
        label.textContent = group.options[i];
        svg.appendChild(label);
    });

    const sparkLayer = document.createElementNS(ns, "g");
    svg.appendChild(sparkLayer);

    const core = document.createElementNS(ns, "circle");
    core.classList.add("rpg-dna-core");
    core.setAttribute("r", 7);
    svg.appendChild(core);

    let point = {
        x: Math.max(8, Math.min(width - 8, startPoint.x)),
        y: Math.max(8, Math.min(height - 8, startPoint.y)),
    };
    let dragging = false;
    let fadeTimer = null;
    let sparkFrame = null;
    let lastSpark = 0;

    optionsEl.innerHTML = group.options.map((option, i) => `
        <div data-option-row="${i}" style="display:flex;align-items:center;gap:7px;margin:4px 0;">
            <div style="width:110px;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(option)}</div>
            <div style="flex:1;height:7px;background:rgba(255,255,255,.1);border-radius:5px;overflow:hidden;">
                <div data-bar="${i}" style="height:100%;width:0%;background:#aaa;transition:width .08s ease;"></div>
            </div>
            <div data-pct="${i}" style="width:40px;text-align:right;font-size:10px;opacity:.7;">0%</div>
        </div>
    `).join("");

    function setPointFromEvent(event) {
        const rect = svg.getBoundingClientRect();
        const scaleX = width / rect.width;
        const scaleY = height / rect.height;
        point.x = Math.max(8, Math.min(width - 8, (event.clientX - rect.left) * scaleX));
        point.y = Math.max(8, Math.min(height - 8, (event.clientY - rect.top) * scaleY));
    }

    function spawnSparkles() {
        const now = performance.now();
        if (now - lastSpark < 35) return;
        lastSpark = now;
        for (let i = 0; i < 3; i++) {
            const spark = document.createElementNS(ns, "circle");
            spark.classList.add("rpg-dna-spark");
            spark.setAttribute("cx", point.x);
            spark.setAttribute("cy", point.y);
            spark.setAttribute("r", String(1 + Math.random() * 2));
            sparkLayer.appendChild(spark);

            const sx = point.x;
            const sy = point.y;
            const dx = (Math.random() - 0.5) * 22;
            const dy = (Math.random() - 0.5) * 22;
            const born = performance.now();
            const duration = 300 + Math.random() * 260;
            const animate = (t) => {
                const progress = Math.min(1, (t - born) / duration);
                spark.setAttribute("cx", sx + dx * progress);
                spark.setAttribute("cy", sy + dy * progress);
                spark.style.opacity = String(1 - progress);
                if (progress < 1 && spark.isConnected) {
                    requestAnimationFrame(animate);
                } else {
                    spark.remove();
                }
            };
            requestAnimationFrame(animate);
        }
    }

    function updateVisuals(showLinks = dragging) {
        const weightsArray = nearestThreeWeights(point, anchors);
        const weights = {};
        weightsArray.forEach((value, i) => weights[String(i)] = value);
        // Sculpting is a live preview until the user clicks ✓.  Keep it
        // separate from committed DNA so ✕ can genuinely cancel.
        node.__dnaPreviewWeights[group.id] = weights;
        refreshGroupCards(node);

        core.setAttribute("cx", point.x);
        core.setAttribute("cy", point.y);
        core.classList.toggle("dragging", dragging);

        anchors.forEach((anchor, i) => {
            const active = (weightsArray[i] || 0) > 0.0005;
            const circle = svg.querySelector(`.rpg-dna-anchor[data-index="${i}"]`);
            circle?.classList.toggle("active", active);

            const line = links[i];
            line.setAttribute("x1", point.x);
            line.setAttribute("y1", point.y);
            line.setAttribute("x2", anchor.x);
            line.setAttribute("y2", anchor.y);
            line.classList.remove("active");
            if (showLinks && active) {
                // Force the CSS animation to restart on every meaningful drag update.
                void line.getBoundingClientRect();
                line.classList.add("active");
            }
        });

        group.options.forEach((_, i) => {
            const pct = Math.round((weightsArray[i] || 0) * 100);
            editor.querySelector(`[data-bar="${i}"]`).style.width = `${pct}%`;
            editor.querySelector(`[data-pct="${i}"]`).textContent = `${pct}%`;
        });

        const parts = group.options
            .map((option, i) => {
                const w = weightsArray[i] || 0;
                return w > 0.0005 ? `(${option}:${formatWeight(w)})` : null;
            })
            .filter(Boolean);
        result.textContent = parts.length > 1 ? parts.join(" & ") : (parts[0] || group.selected);
    }

    function startLinkFade() {
        clearTimeout(fadeTimer);
        fadeTimer = setTimeout(() => {
            links.forEach(line => {
                line.style.transition = "opacity .65s ease";
                line.style.opacity = "0";
                line.classList.remove("active");
            });
        }, 180);
    }

    function dragMove(event) {
        if (!dragging) return;
        setPointFromEvent(event);
        updateVisuals(true);
        spawnSparkles();
        event.preventDefault();
    }

    core.addEventListener("pointerdown", event => {
        dragging = true;
        core.setPointerCapture?.(event.pointerId);
        setPointFromEvent(event);
        updateVisuals(true);
        spawnSparkles();
        event.preventDefault();
    });

    svg.addEventListener("pointermove", dragMove);
    svg.addEventListener("pointerdown", event => {
        if (event.target === core) return;
        dragging = true;
        svg.setPointerCapture?.(event.pointerId);
        setPointFromEvent(event);
        updateVisuals(true);
        spawnSparkles();
        event.preventDefault();
    });

    const stopDragging = () => {
        if (!dragging) return;
        dragging = false;
        core.classList.remove("dragging");
        startLinkFade();
    };
    svg.addEventListener("pointerup", stopDragging);
    svg.addEventListener("pointercancel", stopDragging);
    svg.addEventListener("pointerleave", event => {
        if (dragging && !svg.hasPointerCapture?.(event.pointerId)) stopDragging();
    });

    editor.querySelector("#rpg-dna-cancel").addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        delete node.__dnaPreviewWeights[group.id];
        editor.remove();
        node.__dnaEditor = null;
        node.__dnaEditorGroupId = null;
        refreshGroupCards(node);
    });

    editor.querySelector("#rpg-dna-apply-sculpt").addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();
        const preview = node.__dnaPreviewWeights?.[group.id];
        if (preview) {
            node.__dnaWeights[group.id] = preview;
        } else {
            delete node.__dnaWeights[group.id];
        }
        delete node.__dnaPreviewWeights[group.id];
        node.__dnaEditorGroupId = null;
        saveState(node);
        editor.remove();
        node.__dnaEditor = null;
        renderDrawer(node);
    });

    updateVisuals(false);
}

