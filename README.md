```markdown
# ComfyUI-RPG-Characters

A custom node for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that generates stylized SDXL prompts for RPG characters. This node can output both **standard prompt formats** and enhanced **Ollama-driven prompts** for extreme close-up portraits with vivid detail.

---

## ✨ Features

- 🎨 Choose from a variety of art styles:
  - Anime Style
  - Dark Fantasy
  - Realistic
  - Fantasy Illustration
  - Digital Painting
  - Pixar Animation

- 🧠 Generates:
  - Standard Positive & Negative Prompts (for ComfyUI/SDXL use)
  - Ollama-specific Descriptive Prompt (text-to-text guidance)
  - Ollama-style Negative Prompt Instruction

- 📸 Designed for **1024x1024 extreme close-up portraits**
- 📄 Fully structured to support character features:
  - Race, Ethnicity, Gender, Age, Class
  - Hair & Beard Styles and Colours
  - Clothing Style, Emotion, and Scene

---

## 🧱 Node Outputs

| Output Name                  | Description |
|-----------------------------|-------------|
| `Ollama_Posative_Textbox_1` | Detailed textual prompt for AI input (e.g., LLMs or advanced generation logic) |
| `positive_prompt`           | Basic positive tag list for SDXL |
| `negative_prompt`           | Basic negative tag list for SDXL |
| `Ollama_Negative_Textbox_1` | Instructional template to help LLMs generate clean negative prompts |

---

## 📂 Example Files

All examples are in the `Examples/` folder of this repository.

### 🧠 Standard Prompt Examples

**Node Setup:**  
![Standard Prompt Nodes](Examples/RPG_Standard.png)

**Workflow File:**  
[`RPG_Nodes_Normal.json`](Examples/RPG_Nodes_Normal.json)

---

### 🧠 Ollama-Driven Prompt Examples

**Node Setup:**  
![Ollama Prompt Nodes](Examples/RPG_Ollama.png)

**Workflow File:**  
[`RPG_Nodes_Ollama.json`](Examples/RPG_Nodes_Ollama.json)

---

### ⚔️ Comparison: Standard vs Ollama

**Side-by-Side Visual:**  
![Standard vs Ollama](Examples/RPG_Standard_Vs_Ollama.png)

**Workflow File:**  
[`RPG_Nodes_Normal_Vs_Ollama.json`](Examples/RPG_Nodes_Normal_Vs_Ollama.json)

---

## 📦 Installation

1. Clone or download this repo into your ComfyUI custom nodes folder:

```bash
git clone https://github.com/lord-lethris/ComfyUI-RPG-Characters.git
```

2. Restart ComfyUI.

---

## 🛠️ Usage

1. Add the **RPG Art Style Selector** node from the "RPG" category.
2. Select an Art Style from the dropdown.
3. Connect outputs as needed:
   - `positive_prompt` / `negative_prompt` → SDXL node
   - `Ollama_Posative_Textbox_1` / `Ollama_Negative_Textbox_1` → LLM integration or text generation

---

## 🔮 Future Plans

- Dynamic LLM integration for character prompt generation.
- Additional art styles (e.g., pixel art, steampunk, noir).
- Drag-and-drop interface for race/class/emotion selection.

---

## 🐾 Made by Lord Lethris

Featuring Belle the cat, who disapproves of bad prompts. 🐱
```
