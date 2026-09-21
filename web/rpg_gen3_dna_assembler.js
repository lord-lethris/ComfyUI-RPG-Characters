import { app } from "../../../scripts/app.js";

const EXTENSION_NAME = "lethris.rpg_character_gen3.dna_assembler";
const NODE_NAME = "RPGCharacterDNAAssembler";
const CHANGE_PREFIX = "change_";
const INPUT_TYPE = 1;

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
    if (last?.link != null) {
        node.addInput(`${CHANGE_PREFIX}${inputs.length + 1}`, "RPG_DNA_SECTION", {
            forceInput: true,
            label: `Change ${inputs.length + 1}`,
            tooltip: "Connect a DNA section to override that section. Connect this slot to add another change.",
        });
    }
}

function compactDisconnectedChangeInputs(node) {
    const inputs = changeInputs(node);
    if (inputs.length <= 1) {
        ensureChangeInput(node);
        return;
    }

    // Remove empty slots that sit before a later connected slot. This keeps
    // the visible Change numbers contiguous while preserving the later links.
    for (let i = inputs.length - 2; i >= 0; i--) {
        if (inputs[i].link == null) {
            const actualIndex = node.inputs.indexOf(inputs[i]);
            if (actualIndex >= 0) node.removeInput(actualIndex);
        }
    }

    ensureChangeInput(node);
}

app.registerExtension({
    name: EXTENSION_NAME,

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_NAME) return;

        const originalCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            originalCreated?.apply(this, arguments);

            ensureChangeInput(this);

            // Dynamic inputs are created by the frontend and therefore need
            // their own graph-change notification when added to an existing
            // node so the workflow can be saved with the current socket set.
            this.setDirtyCanvas?.(true, true);
        };

        const originalConnectionsChange = nodeType.prototype.onConnectionsChange;
        nodeType.prototype.onConnectionsChange = function (type, index, connected, linkInfo) {
            const result = originalConnectionsChange?.apply(this, arguments);

            if (type === INPUT_TYPE) {
                const input = this.inputs?.[index];
                if (input && isChangeInput(input)) {
                    if (connected) {
                        ensureChangeInput(this);
                    } else {
                        compactDisconnectedChangeInputs(this);
                    }
                    this.graph?.change?.();
                    app.graph?.change?.();
                    this.setDirtyCanvas?.(true, true);
                }
            }

            return result;
        };
    },
});
