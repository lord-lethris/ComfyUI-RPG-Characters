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

function setVariantSelection(variant, index) {
    if (!Array.isArray(variant.options) || !variant.options.length) return;
    const weights = {};
    weights[String(index)] = 1;
    variant.weights = weights;
    variant.mode = "selected";
    variant.selected = variant.options[index];
}

function renderExpressionMouth(node, section, locus, host) {
    const control = locus?.controls?.mouth;
    if (!control) return;

    const wrap = document.createElement("div");
    wrap.style.cssText = "margin-top:8px;padding:7px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.08);border-radius:5px";

    const title = document.createElement("div");
    title.style.cssText = "display:flex;align-items:center;gap:6px;margin-bottom:5px";
    title.innerHTML = '<span style="font-size:11px;font-weight:700">👄 Mouth</span><span style="margin-left:auto;font-size:8px;opacity:.5">EXPRESSION CONTROL</span>';
    wrap.appendChild(title);

    const field = document.createElement("div");
    field.style.cssText = [
        "position:relative",
        "height:190px",
        "border:1px solid rgba(255,255,255,.12)",
        "border-radius:5px",
        "background:radial-gradient(circle at 50% 50%,rgba(255,255,255,.04),rgba(0,0,0,.18))",
        "overflow:hidden",
        "touch-action:none",
    ].join(";");

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 300 190");
    svg.style.cssText = "position:absolute;inset:0;width:100%;height:100%;pointer-events:none";
    field.appendChild(svg);

    const upper = document.createElementNS("http://www.w3.org/2000/svg", "path");
    const lower = document.createElementNS("http://www.w3.org/2000/svg", "path");
    const opening = document.createElementNS("http://www.w3.org/2000/svg", "path");
    [upper, lower, opening].forEach(p => {
        p.setAttribute("fill", "none");
        p.setAttribute("stroke", "rgba(240,240,240,.9)");
        p.setAttribute("stroke-width", "3");
        p.setAttribute("stroke-linecap", "round");
        svg.appendChild(p);
    });
    opening.setAttribute("fill", "rgba(255,255,255,.08)");
    opening.setAttribute("stroke", "rgba(255,255,255,.45)");

    const point = document.createElement("div");
    point.style.cssText = "position:absolute;width:14px;height:14px;margin:-7px 0 0 -7px;border-radius:50%;background:#e8f7ff;border:2px solid #fff;box-shadow:0 0 10px rgba(200,235,255,.8);cursor:grab;z-index:5";
    field.appendChild(point);

    const axisX = document.createElement("div");
    axisX.style.cssText = "position:absolute;left:8px;right:8px;top:50%;border-top:1px dashed rgba(255,255,255,.12);pointer-events:none";
    field.appendChild(axisX);
    const axisY = document.createElement("div");
    axisY.style.cssText = "position:absolute;top:8px;bottom:8px;left:50%;border-left:1px dashed rgba(255,255,255,.12);pointer-events:none";
    field.appendChild(axisY);

    const labels = document.createElement("div");
    labels.style.cssText = "position:absolute;inset:0;pointer-events:none;font-size:8px;opacity:.45";
    labels.innerHTML = '<span style="position:absolute;left:6px;top:4px">Frown</span><span style="position:absolute;right:6px;top:4px">Smile</span><span style="position:absolute;left:6px;bottom:4px">Closed</span><span style="position:absolute;right:6px;bottom:4px">Open</span>';
    field.appendChild(labels);

    const values = {
        x: Number(control.x_value ?? 0),
        y: Number(control.y_value ?? 0),
    };

    function render() {
        const px = 50 + values.x * 40;
        const py = 10 + values.y * 80;
        point.style.left = px + "%";
        point.style.top = py + "%";

        const smile = values.x;
        const open = values.y;
        const cx = 150;
        const width = 76;
        const left = cx - width;
        const right = cx + width;
        const corner = 145 - smile * 24;
        const center = 118;
        const openingHeight = 3 + open * 35;
        const upperY = center;
        const lowerY = center + openingHeight;

        upper.setAttribute("d", `M ${left} ${corner} Q ${cx - 30} ${center - 18 - smile * 8} ${cx} ${center + 2} Q ${cx + 30} ${center - 18 + smile * 8} ${right} ${corner}`);
        lower.setAttribute("d", `M ${left} ${corner} Q ${cx - 30} ${lowerY + 10} ${cx} ${lowerY} Q ${cx + 30} ${lowerY + 10} ${right} ${corner}`);
        opening.setAttribute("d", `M ${left} ${corner} Q ${cx} ${center + openingHeight} ${right} ${corner} Q ${cx} ${center - 1} ${left} ${corner} Z`);
    }

    function positionFromEvent(event) {
        const rect = field.getBoundingClientRect();
        return {
            x: Math.max(-1, Math.min(1, ((event.clientX - rect.left) / rect.width - 0.5) * 2)),
            y: Math.max(0, Math.min(1, (event.clientY - rect.top) / rect.height)),
        };
    }

    function move(event) {
        const p = positionFromEvent(event);
        values.x = p.x;
        values.y = p.y;
        control.x_value = Number(p.x.toFixed(3));
        control.y_value = Number(p.y.toFixed(3));
        render();
        readout.textContent = `Smile ${p.x >= 0 ? "+" : ""}${p.x.toFixed(2)}  •  Open ${p.y.toFixed(2)}`;
    }

    let dragging = false;
    field.addEventListener("pointerdown", event => {
        dragging = true;
        field.setPointerCapture?.(event.pointerId);
        move(event);
        event.stopPropagation();
    });
    field.addEventListener("pointermove", event => {
        if (dragging) move(event);
    });
    field.addEventListener("pointerup", () => { dragging = false; });
    field.addEventListener("pointercancel", () => { dragging = false; });

    const readout = document.createElement("div");
    readout.style.cssText = "font-size:9px;opacity:.65;text-align:center;margin-top:5px";

    const reset = document.createElement("button");
    reset.textContent = "Reset Mouth";
    reset.style.cssText = "margin-top:5px;width:100%";
    reset.onclick = event => {
        event.stopPropagation();
        values.x = 0;
        values.y = 0;
        control.x_value = 0;
        control.y_value = 0;
        render();
        readout.textContent = "Smile +0.00  •  Open 0.00";
        applySection(node, section);
    };

    wrap.appendChild(field);
    wrap.appendChild(readout);
    wrap.appendChild(reset);
    host.appendChild(wrap);

    render();
    readout.textContent = `Smile ${values.x >= 0 ? "+" : ""}${values.x.toFixed(2)}  •  Open ${values.y.toFixed(2)}`;
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
        updateWeights(weights);
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

    const controls = document.createElement("div");
    controls.style.cssText = "display:flex;justify-content:flex-end;gap:4px;margin-top:5px";

    const cancel = document.createElement("button");
    cancel.textContent = "✕";
    cancel.title = "Cancel sculpting";
    cancel.style.cssText = "min-width:34px";

    const accept = document.createElement("button");
    accept.textContent = "✓";
    accept.title = "Apply sculpting";
    accept.style.cssText = "min-width:34px";

    controls.appendChild(cancel);
    controls.appendChild(accept);

    const help = document.createElement("div");
    help.textContent = "Drag the point • nearest three variants blend • hover dots for names";
    help.style.cssText = "font-size:9px;opacity:.5;margin-top:4px";

    cancel.onclick = event => {
        event.stopPropagation();
        host.innerHTML = "";
    };

    accept.onclick = event => {
        event.stopPropagation();
        const weights = weightsAt(position.x, position.y);
        const weightMap = {};
        weights.forEach(item => weightMap[String(item.index)] = item.weight);

        locus.weights = weightMap;
        locus.mode = "sculpted";

        const best = weights.slice().sort((a, b) => b.weight - a.weight)[0];
        if (best) {
            locus.selected = locus.options[best.index];
            if (locus.id?.includes(":variant:")) {
                locus.mode = "sculpted";
            } else {
                section.values = section.values || {};
                const key = locus.id?.includes(":") ? locus.id.split(":").slice(1).join(":") : locus.id;
                if (key) section.values[key] = locus.selected;
            }
        }

        applySection(node, section);
        renderEditor(node);
        requestAnimationFrame(() => {
            const size = node.computeSize?.();
            if (size) node.setSize?.([Math.max(node.size[0], size[0]), size[1]]);
        });
    };

    host.appendChild(field);
    host.appendChild(controls);
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
        node.__gen3EditorHeight = 55;
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
        node.__gen3EditorHeight = 95;
        node.setSize?.([Math.max(node.size[0], 320), Math.max(node.size[1], 240)]);
        return;
    }

    const makeActions = (target, card, allowSculpt = false) => {
        const actions = document.createElement("div");
        actions.style.cssText = "display:flex;gap:5px";

        const reroll = document.createElement("button");
        reroll.textContent = "🎲 Re-roll";
        reroll.style.flex = "1";
        reroll.onclick = event => {
            event.stopPropagation();
            const index = pickRerollIndex(target, currentIndex(target));
            if (target.id?.includes(":variant:")) {
                setVariantSelection(target, index);
            } else {
                setLocusSelection(section, target, index);
            }
            applySection(node, section);
            renderEditor(node);
        };
        actions.appendChild(reroll);

        if (allowSculpt) {
            const sculpt = document.createElement("button");
            sculpt.textContent = "🧬 Sculpt";
            sculpt.style.flex = "1";
            sculpt.onclick = event => {
                event.stopPropagation();
                const existing = card.querySelector(".gen3-inline-sculpt");
                if (existing) {
                    existing.remove();
                    refreshEditorHeight(node);
                    return;
                }
                const sculptHost = document.createElement("div");
                sculptHost.className = "gen3-inline-sculpt";
                card.appendChild(sculptHost);
                renderSculptField(node, section, target, sculptHost);
                refreshEditorHeight(node);
            };
            actions.appendChild(sculpt);
        }

        card.appendChild(actions);
    };

    for (const locus of loci) {
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

        const variants = Array.isArray(locus.variant_sets) ? locus.variant_sets : [];

        if (locus.controls?.mouth) {
            const mouthHost = document.createElement("div");
            mouthHost.className = "gen3-expression-mouth";
            renderExpressionMouth(node, section, locus, mouthHost);
            card.appendChild(mouthHost);
        }
        if (variants.length) {
            const note = document.createElement("div");
            note.textContent = "Internal DNA variants";
            note.style.cssText = "font-size:9px;opacity:.5;margin:4px 0 5px";
            card.appendChild(note);

            for (const variant of variants) {
                const variantCard = document.createElement("div");
                variantCard.style.cssText = "padding:7px;margin:5px 0;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);border-radius:5px";

                const variantTitle = document.createElement("div");
                variantTitle.style.cssText = "display:flex;align-items:center;gap:6px";
                variantTitle.innerHTML = `
                    <div style="flex:1;font-size:10px;font-weight:600">${escapeHtml(variant.label || "Variant")}</div>
                    <div style="font-size:8px;opacity:.5">${escapeHtml(variant.mode || "RANDOM").toUpperCase()}</div>`;
                variantCard.appendChild(variantTitle);

                const variantValue = document.createElement("div");
                variantValue.textContent = variant.selected || "Random";
                variantValue.style.cssText = "font-size:10px;margin:3px 0 6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis";
                variantCard.appendChild(variantValue);

                makeActions(variant, variantCard, true);
                card.appendChild(variantCard);
            }
        } else {
            // A top-level categorical choice is re-rollable, but only an
            // internal {A|B|C} DNA variant is meaningfully sculptable.
            makeActions(locus, card, false);
        }

        container.appendChild(card);
    }

    const footer = document.createElement("div");
    footer.style.cssText = "padding:7px 0 2px;font-size:9px;opacity:.45;text-align:center";
    footer.textContent = "Changes are stored in the DNA section and revisioned automatically.";
    container.appendChild(footer);

    refreshEditorHeight(node);
}

function refreshEditorHeight(node) {
    const container = node.__gen3EditorContainer;
    if (!container) return;
    const height = Math.max(50, container.scrollHeight + 4);
    node.__gen3EditorHeight = height;
    container.style.minHeight = height + "px";
    const size = node.computeSize?.();
    if (size) {
        node.setSize?.([Math.max(node.size[0], 320, size[0]), Math.max(node.size[1], size[1], height + 70)]);
    }
    node.setDirtyCanvas?.(true, true);
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

            const editorWidget = node.addDOMWidget("gen3_dna_editor", "custom", container, {
                serialize: false,
                hideOnZoom: false,
                getValue() { return ""; },
                setValue() {},
                getMinHeight() { return node.__gen3EditorHeight || 50; },
                getMaxHeight() { return node.__gen3EditorHeight || 50; },
            });
            editorWidget.computeLayoutSize = () => ({
                minHeight: node.__gen3EditorHeight || 50,
                maxHeight: node.__gen3EditorHeight || 50,
                minWidth: 300,
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
