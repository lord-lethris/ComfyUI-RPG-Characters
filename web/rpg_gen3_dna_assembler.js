import { app } from "../../../scripts/app.js";

const EXTENSION_NAME = "lethris.rpg_character_gen3.dna_assembler";
const NODE_NAME = "RPGCharacterDNAAssembler";
const CHANGE_PREFIX = "change_";
const INPUT_TYPE = 1;
const MAX_CHANGE_INPUTS = 16;

function isChangeInput(input) {
    return typeof input?.name === "string" && input.name.startsWith(CHANGE_PREFIX);
}

function changeInputs(node) {
    return (node.inputs || [])
        .filter(isChangeInput)
        .sort((a, b) => {
            const ai = Number(a.name.slice(CHANGE_PREFIX.length));
            const bi = Number(b.name.slice(CHANGE_PREFIX.length));
            return ai - bi;
        });
}

function ensureChangeInput(node) {
    let inputs = changeInputs(node);

    if (!inputs.length) {
        node.addInput("change_1", "RPG_DNA_SECTION", {
            forceInput: true,
            label: "Change 1",
            tooltip: "Connect a DNA section to override that section. Connect this slot to add another change.",
        });
        inputs = changeInputs(node);
    }

    inputs.forEach((input, index) => {
        input.name = `${CHANGE_PREFIX}${index + 1}`;
        input.label = `Change ${index + 1}`;
        input.type = "RPG_DNA_SECTION";
        input.forceInput = true;
        input.tooltip = "Connect a DNA section to override that section. Connect this slot to add another change.";
    });

    // Keep exactly one empty landing slot at the end.
    inputs = changeInputs(node);
    const last = inputs[inputs.length - 1];
    if (last?.link != null && inputs.length < MAX_CHANGE_INPUTS) {
        node.addInput(`${CHANGE_PREFIX}${inputs.length + 1}`, "RPG_DNA_SECTION", {
            forceInput: true,
            label: `Change ${inputs.length + 1}`,
            tooltip: "Connect a DNA section to override that section. Connect this slot to add another change.",
        });
    }
}

function getVisibleChangeCount(node) {
    const inputs = changeInputs(node);
    if (!inputs.length) return 1;

    let lastConnected = -1;
    for (let i = 0; i < inputs.length; i++) {
        if (inputs[i].link != null) lastConnected = i;
    }

    // Show all connected changes plus exactly one empty landing slot.
    return Math.min(inputs.length, Math.max(1, lastConnected + 2));
}

function isVisibleInput(node, input) {
    if (!isChangeInput(input)) return true;

    const number = Number(input.name.slice(CHANGE_PREFIX.length));
    return number <= getVisibleChangeCount(node);
}

function resizeToVisibleInputs(node) {
    const visibleChangeCount = getVisibleChangeCount(node);
    const totalVisibleInputs = 1 + visibleChangeCount; // character_info + changes
    const rows = Math.max(totalVisibleInputs, node.outputs?.length || 1);

    // This node has no widgets. Match LiteGraph's normal slot-based sizing
    // while sizing from the visible socket count rather than the backend pool.
    const slotStartY = node.constructor?.slot_start_y || 0;
    const desiredHeight = slotStartY + rows * 20 + 6;

    if (node.size?.[1] !== desiredHeight) {
        node.setSize?.([node.size?.[0] || 200, desiredHeight]);
    }
}
app.registerExtension({
    name: EXTENSION_NAME,

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_NAME) return;

        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            originalCreated?.apply(this, arguments);

            ensureChangeInput(this);
            compactDisconnectedChangeInputs(this);

            // Dynamic inputs are created by the frontend and therefore need
            // their own graph-change notification when added to an existing
            // node so the workflow can be saved with the current socket set.
            this.setDirtyCanvas?.(true, true);
        };

        const originalArrange = nodeType.prototype.arrange;
        nodeType.prototype.arrange = function () {
            const result = originalArrange?.apply(this, arguments);
            resizeToVisibleInputs(this);
            return result;
        };

        const originalDrawSlots = nodeType.prototype.drawSlots;
        nodeType.prototype.drawSlots = function (ctx, options) {
            const { fromSlot, colorContext, editorAlpha, lowQuality } = options;

            // Keep the complete input array intact so LiteGraph link indices
            // remain stable. Only skip unused change sockets while rendering.
            for (const [index, slot] of (this._concreteInputs || []).entries()) {
                const input = this.inputs?.[index];
                if (!isVisibleInput(this, input)) continue;

                const isValidTarget = fromSlot && slot.isValidTarget(fromSlot);
                const isMouseOverSlot = this._isMouseOverSlot(slot);

                const isValid = !fromSlot || isValidTarget;
                const highlight = isValid && isMouseOverSlot;

                if (
                    isMouseOverSlot ||
                    isValidTarget ||
                    !slot.isWidgetInputSlot ||
                    this._isMouseOverWidget(this.getWidgetFromSlot(slot)) ||
                    slot.isConnected ||
                    slot.alwaysVisible
                ) {
                    ctx.globalAlpha = isValid ? editorAlpha : 0.4 * editorAlpha;
                    slot.draw(ctx, {
                        colorContext,
                        lowQuality,
                        highlight
                    });
                }
            }

            for (const slot of this._concreteOutputs || []) {
                const isValidTarget = fromSlot && slot.isValidTarget(fromSlot);
                const isMouseOverSlot = this._isMouseOverSlot(slot);

                const isValid = !fromSlot || isValidTarget;
                const highlight = isValid && isMouseOverSlot;

                ctx.globalAlpha = isValid ? editorAlpha : 0.4 * editorAlpha;
                slot.draw(ctx, {
                    colorContext,
                    lowQuality,
                    highlight
                });
            }

            ctx.globalAlpha = editorAlpha;
        };

        const originalGetInputOnPos = nodeType.prototype.getInputOnPos;
        nodeType.prototype.getInputOnPos = function (pos) {
            const result = originalGetInputOnPos?.call(this, pos);
            if (!result || isVisibleInput(this, result)) return result;
            return undefined;
        };

        const originalConnectionsChange = nodeType.prototype.onConnectionsChange;
        const originalConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            const result = originalConfigure?.apply(this, arguments);
            compactDisconnectedChangeInputs(this);
            return result;
        };

        nodeType.prototype.onConnectionsChange = function (type, index, connected, linkInfo) {
            const result = originalConnectionsChange?.apply(this, arguments);

            if (type === INPUT_TYPE) {
                const input = this.inputs?.[index];
                if (input && isChangeInput(input)) {
                    compactDisconnectedChangeInputs(this);
                    this.graph?.change?.();
                    app.graph?.change?.();
                    this.setDirtyCanvas?.(true, true);
                }
            }

            return result;
        };
    },
});
