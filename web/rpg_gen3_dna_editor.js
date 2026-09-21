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

function hashString(value) {
    let hash = 2166136261;
    for (const ch of String(value)) {
        hash ^= ch.charCodeAt(0);
        hash = Math.imul(hash, 16777619);
    }
    return hash >>> 0;
}

function candidateIndices(locus, count = 6) {
    const options = Array.isArray(locus?.options) ? locus.options : [];
    if (!options.length) return [];

    const selectedIndex = Math.max(0, options.indexOf(locus.selected));
    const result = [selectedIndex];
    let state = hashString(locus.id || locus.label || "");

    while (result.length < Math.min(count, options.length)) {
        state = Math.imul(state ^ (state >>> 16), 2246822507) >>> 0;
        const index = state % options.length;
        if (!result.includes(index)) result.push(index);
    }
    return result;
}

function pickRerollIndex(locus, currentIndex) {
    const options = Array.isArray(locus?.options) ? locus.options : [];
    if (options.length < 2) return currentIndex;
    let index = Math.floor(Math.random() * options.length);
    if (index === currentIndex) index = (index + 1) % options.length;
    return index;
}

function activeWeights(locus) {
    const weights = normaliseWeights(locus?.weights, locus?.options?.length || 0);
    return weights || [];
}

function currentIndex(locus) {
    const options = Array.isArray(locus?.options) ? locus.options : [];
    const weights = activeWeights(locus);
    if (weights.length) {
        let best = 0;
        for (let i = 1; i < weights.length; i++) {
            if (weights[i] > weights[best]) best = i;
        }
        if (weights[best] > 0) return best;
    }
    const index = options.indexOf(locus?.selected);
    return index >= 0 ? index : 0;
}

function applySection(node, section) {
    const transport = getWidget(node, "edited_section");
    if (transport) {
        transport.value = JSON.stringify(section);
        transport.callback?.(transport.value);
    }

    node.__gen3SectionData = section;

    const revision = getWidget(node, "revision");
    const previous = Number(revision?.value ?? 0);
    setWidget(node, "revision",
        Number.isFinite(previous) ? (previous >= 2147483647 ? 0 : previous + 1) : 1
    );

    node.setDirtyCanvas?.(true, true);
    node.graph?.change?.();
    app.graph?.change?.();
    app.graph?.setDirtyCanvas?.(true, true);
}

function setLocusSelection(section, locus, index) {
    if (!Array.isArray(locus.options) || !locus.options.length) return;

    const weights = {};
    weights[String(index)] = 1;
    locus.weights = weights;
    locus.mode = "selected";
    locus.selected = locus.options[index];
    section.values = section.values || {};
    const valueKey = locus.id?.includes(":") ? locus.id.split(":").slice(1).join(":") : locus.id;
    if (valueKey) section.values[valueKey] = locus.selected;
    section.traits = Array.isArray(section.traits) ? section.traits : [];
    if (locus.selected && !section.traits.includes(locus.selected)) section.traits.push(locus.selected);
}

function renderSculptField(node, section, locus, host) {
    const candidates = candidateIndices(locus, 6);
    if (!candidates.length) return;

    const field = document.createElement("div");
    field.className = "gen3-sculpt-field";
    field.style.cssText = [
        "position:relative",
        "height:180px",
        "margin-top:8px",
        "border:1px solid rgba(255,255,255,.12)",
        "border-radius:5px",
        "background:rgba(0,0,0,.18)",
        "overflow:hidden",
    ].join(";");

    const point = document.createElement("div");
    point.style.cssText = [
        "position:absolute",
        "width:14px",
        "height:14px",
        "margin:-7px 0 0 -7px",
        "border-radius:50%",
        "background:#e8f7ff",
        "border:2px solid #fff",
        "box-shadow:0 0 10px rgba(200,235,255,.8)",
        "cursor:grab",
        "z-index:5",
    ].join(";");

    const anchors = candidates.map((index, i) => {
        const angle = -Math.PI / 2 + (Math.PI * 2 * i / candidates.length);
        return {
            index,
            x: 50 + Math.cos(angle) * 37,
            y: 50 + Math.sin(angle) * 38,
        };
    });

    for (const anchor of anchors) {
        const dot = document.createElement("div");
        dot.title = locus.options[anchor.index];
        dot.style.cssText = [
            "position:absolute",
            "width:9px",
            "height:9px",
            "margin:-4px 0 0 -4px",
            "border-radius:50%",
            "background:rgba(210,210,210,.2)",
            "border:1px solid rgba(255,255,255,.45)",
            "cursor:pointer",
        ].join(";");
        dot.style.left = anchor.x + "%";
        dot.style.top = anchor.y + "%";

        const label = document.createElement("div");
        label.textContent = locus.options[anchor.index];
        label.style.cssText = [
            "position:absolute",
            "left:50%",
            "transform:translateX(-50%)",
            "white-space:nowrap",
            "max-width:120px",
            "overflow:hidden",
            "text-overflow:ellipsis",
            "font-size:9px",
            "opacity:.8",
            "pointer-events:none",
        ].join(";");
        label.style.top = anchor.y < 50 ? "10px" : "-20px";
        dot.appendChild(label);

        dot.addEventListener("click", event => {
            event.stopPropagation();
            movePoint(anchor.x, anchor.y);
        });
        field.appendChild(dot);
    }

    field.appendChild(point);

    const existing = activeWeights(locus);
    let position = { x: 50, y: 50 };
    if (existing.length) {
        let total = 0;
        let x = 0;
        let y = 0;
        anchors.forEach(anchor => {
            const weight = existing[anchor.index] || 0;
            total += weight;
            x += anchor.x * weight;
            y += anchor.y * weight;
        });
        if (total > 0) position = { x: x / total, y: y / total };
    } else {
        const selected = anchors.find(a => a.index === currentIndex(locus));
        if (selected) position = { x: selected.x, y: selected.y };
    }

    function weightsAt(x, y) {
        const distances = anchors.map(anchor => ({
            ...anchor,
            distance: Math.hypot(x - anchor.x, y - anchor.y),
        })).sort((a, b) => a.distance - b.distance);

        const nearest = distances.slice(0, Math.min(3, distances.length));
        if (nearest[0].distance < 0.001) {
            return nearest.map(a => ({ index: a.index, weight: a.index === nearest[0].index ? 1 : 0 }));
        }

        const raw = nearest.map(a => 1 / Math.pow(a.distance, 2));
        const total = raw.reduce((a, b) => a + b, 0);
        return nearest.map((a, i) => ({ index: a.index, weight: raw[i] / total }));
    }

    function movePoint(x, y) {
        position = { x: Math.max(3, Math.min(97, x)), y: Math.max(3, Math.min(97, y)) };
        point.style.left = position.x + "%";
        point.style.top = position.y + "%";

        const weights = weightsAt(position.x, position.y);
        const weightMap = {};
        weights.forEach(item => weightMap[String(item.index)] = item.weight);
        locus.weights = weightMap;
        locus.mode = "sculpted";

        const best = weights.slice().sort((a, b) => b.weight - a.weight)[0];
        if (best) {
            locus.selected = locus.options[best.index];
            section.values = section.values || {};
            const key = locus.id?.includes(":") ? locus.id.split(":").slice(1).join(":") : locus.id;
            if (key) section.values[key] = locus.selected;
        }

        updateWeights(weights);
        applySection(node, section);
    }

    function updateWeights(weights) {
        const weightMap = new Map(weights.map(item => [item.index, item.weight]));
        weightList.innerHTML = anchors
            .map(anchor => {
                const weight = weightMap.get(anchor.index) || 0;
                return `<div style="display:flex;gap:6px;align-items:center;margin:3px 0">
                    <div style="flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:10px">${escapeHtml(locus.options[anchor.index])}</div>
                    <div style="width:70px;height:5px;background:rgba(255,255,255,.1);border-radius:3px;overflow:hidden">
                        <div style="height:100%;width:${Math.round(weight * 100)}%;background:#aaa"></div>
                    </div>
                    <div style="width:30px;text-align:right;font-size:10px;opacity:.7">${Math.round(weight * 100)}%</div>
                </div>`;
            }).join("");
    }

    const weightList = document.createElement("div");
    weightList.style.marginTop = "6px";

    let dragging = false;
    function pointerPosition(event) {
        const rect = field.getBoundingClientRect();
        return {
            x: ((event.clientX - rect.left) / rect.width) * 100,
            y: ((event.clientY - rect.top) / rect.height) * 100,
        };
    }

    field.addEventListener("pointerdown", event => {
        if (event.target !== point && event.target.parentElement !== point) {
            const p = pointerPosition(event);
            movePoint(p.x, p.y);
        }
        dragging = true;
        field.setPointerCapture?.(event.pointerId);
    });
    field.addEventListener("pointermove", event => {
        if (!dragging) return;
        const p = pointerPosition(event);
        movePoint(p.x, p.y);
    });
    field.addEventListener("pointerup", () => { dragging = false; });
    field.addEventListener("pointercancel", () => { dragging = false; });

    const help = document.createElement("div");
    help.textContent = "Drag the point • nearest three variants blend • hover dots for names";
    help.style.cssText = "font-size:9px;opacity:.5;margin-top:4px";

    host.appendChild(field);
    host.appendChild(weightList);
    host.appendChild(help);

    updateWeights(weightsAt(position.x, position.y));
}

function renderEditor(node) {
    const container = node.__gen3EditorContainer;
    if (!container) return;

    const section = node.__gen3SectionData;
    if (!section || typeof section !== "object") {
        container.innerHTML = `
            <div style="padding:10px;opacity:.6;font-size:11px;text-align:center">
                Run the graph to populate this DNA section.
            </div>`;
        node.setSize?.([Math.max(node.size[0], 320), Math.max(node.size[1], 180)]);
        return;
    }

    const loci = Array.isArray(section.loci) ? section.loci : [];
    const sectionLabel = SECTION_LABELS[section.id] || section.id || "DNA";

    container.innerHTML = `
        <div style="padding:4px 2px 8px;border-bottom:1px solid rgba(255,255,255,.1)">
            <div style="font-weight:700;font-size:13px">🧬 ${escapeHtml(sectionLabel)}</div>
            <div style="font-size:9px;opacity:.5">Structured DNA editor</div>
        </div>
    `;

    if (!loci.length) {
        container.innerHTML += `
            <div style="padding:12px 4px;opacity:.55;font-size:10px">
                No editable loci in this section yet.
            </div>`;
        return;
    }

    for (let i = 0; i < loci.length; i++) {
        const locus = loci[i];
        const card = document.createElement("div");
        card.style.cssText = "padding:8px 0;border-bottom:1px solid rgba(255,255,255,.08)";

        const title = document.createElement("div");
        title.style.cssText = "display:flex;align-items:center;gap:6px";
        title.innerHTML = `
            <div style="flex:1;font-weight:700;font-size:11px">${escapeHtml(locus.label || locus.id)}</div>
            <div style="font-size:8px;opacity:.5">${escapeHtml(locus.mode || "RANDOM").toUpperCase()}</div>`;
        card.appendChild(title);

        const value = document.createElement("div");
        value.textContent = locus.selected || "Random";
        value.style.cssText = "font-size:10px;margin:3px 0 7px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";
        card.appendChild(value);

        const actions = document.createElement("div");
        actions.style.cssText = "display:flex;gap:5px";

        const reroll = document.createElement("button");
        reroll.textContent = "🎲 Re-roll";
        reroll.style.flex = "1";
        reroll.onclick = event => {
            event.stopPropagation();
            const index = pickRerollIndex(locus, currentIndex(locus));
            setLocusSelection(section, locus, index);
            applySection(node, section);
            renderEditor(node);
        };

        const sculpt = document.createElement("button");
        sculpt.textContent = "🧬 Sculpt";
        sculpt.style.flex = "1";
        sculpt.onclick = event => {
            event.stopPropagation();
            const existing = card.querySelector(".gen3-inline-sculpt");
            if (existing) {
                existing.remove();
                return;
            }
            const sculptHost = document.createElement("div");
            sculptHost.className = "gen3-inline-sculpt";
            card.appendChild(sculptHost);
            renderSculptField(node, section, locus, sculptHost);
        };

        actions.appendChild(reroll);
        actions.appendChild(sculpt);
        card.appendChild(actions);
        container.appendChild(card);
    }

    const footer = document.createElement("div");
    footer.style.cssText = "padding:7px 0 2px;font-size:9px;opacity:.45;text-align:center";
    footer.textContent = "Changes are stored in the DNA section and revisioned automatically.";
    container.appendChild(footer);

    node.setSize?.([Math.max(node.size[0], 320), Math.max(node.size[1], 240)]);
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

            const container = document.createElement("div");
            container.style.cssText = [
                "width:100%",
                "box-sizing:border-box",
                "padding:0 4px 6px",
                "color:var(--input-text,#ddd)",
                "font-family:Arial,sans-serif",
                "overflow:visible",
            ].join(";");

            node.addDOMWidget("gen3_dna_editor", "custom", container, {
                serialize: false,
                hideOnZoom: false,
                getValue() { return ""; },
                setValue() {},
            });

            node.__gen3EditorContainer = container;
            renderEditor(node);
        };

        const originalExecuted = nodeType.prototype.onExecuted;
        nodeType.prototype.onExecuted = function (message) {
            originalExecuted?.apply(this, arguments);

            const raw = message?.section ?? message?.ui?.section;
            const section = Array.isArray(raw) ? raw[0] : raw;
            if (section && typeof section === "object") {
                this.__gen3SectionData = section;
                renderEditor(this);
            }
        };
    },
});
