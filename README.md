# ComfyUI-RPG-Characters

A custom node for [ComfyUI](https://github.com/comfyanonymous/ComfyUI) that generates stylized prompts for RPG characters. This node outputs both **standard prompt formats** and enhanced **Ollama-style descriptive prompts** ideal for **extreme close-up portraits**.

✅ Compatible with **Stable Diffusion**, **SDXL**, **Flux**, and any model that uses structured prompts.

The generator supports both classic **AD&D / Fantasy** and **Sci-Fi / Cyberpunk** character creation, with expanded classes, clothing styles, scenes, and art styles. Sci-Fi characters can be created **without augmentations**, allowing fully augment-free characters as well as cybernetic ones.

---

## ✨ Features

- 🎨 Choose from a variety of art styles:
  - Anime Style
  - Dark Fantasy
  - Realistic
  - Fantasy Illustration
  - Digital Painting
  - Sci-Fi / Cyberpunk

- 🧠 Generates:
  - Standard Positive & Negative Prompts (for SD, SDXL, Flux)
  - Ollama-style Descriptive Prompt (text-to-text guidance)
  - Ollama-style Negative Prompt Instruction

- 📸 Designed for **1024x1024 extreme close-up portraits**
- 📄 Fully structured to support character features:
  - Race, Ethnicity, Gender, Age, Class
  - Hair & Beard Styles and Colours
  - Clothing Style, Emotion, and Scene
  - Fantasy and Sci-Fi / Cyberpunk classes and clothing
  - General / Neutral, Fantasy, and Sci-Fi / Cyberpunk scenes

- 🧬 **DNA Locker (V2.4)**
  — Deterministic character DNA with per-locus re-rolls, Master Seed control, and a 2D DNA Sculptor for blending the nearest three variants. Preview changes live, apply or cancel sculpting, and reproduce character variations from the same seed.

---

## 🆕 V2.4 Workflow Highlights — DNA Locker

The **AD&D Character Portrait Generator V2.4** introduces the **🧬 DNA Locker**, a deterministic character-variation system that lets you experiment with a character's visual traits without losing combinations you like.

### 🧬 DNA Locker

The DNA Locker gives each generated character a reproducible set of DNA loci — such as skin tone, eye colour, hair colour, and other supported visual traits.

- 🎲 **Re-roll individual traits** — keep rolling a specific locus until you find a combination you like.
- 🎲 **Re-roll the Master Seed** — generate a completely new DNA combination across all visible loci.
- 🧬 **DNA Sculptor** — blend the nearest three variants in 2D DNA space for finer control than simple random selection.
- 👁️ **Live feedback** — DNA changes are reflected immediately in the Locker while experimenting.
- ✓ **Apply / ✕ Cancel** — sculpt changes can be previewed live and either committed or discarded.
- 🔢 **Reproducible** — the Master Seed allows the same DNA combination to be recreated.

The DNA Locker is designed to sit alongside the normal character-selection workflow: roll the dice, find a combination you like, sculpt it if you want more control, then run the workflow.

> ⚠️ **DNA is deterministic. Genetics are not.**  
> Diffusion models can occasionally interpret traits creatively, so the final image won't always perfectly match the DNA Locker. **DNA is fragile. Handle with care.** 🧬😏

**Your character. Your DNA. Your dice.**

### 🖼️ V2.4 Example Workflow

The repository includes a complete **AD&D Character Portrait Generator V2.4 - Basic** example showing the DNA Locker in use.

**DNA Locker Highlight:**  
![AD&D Character Portrait Generator V2.4 - DNA Locker](Examples/AD&D_Character_Portrait_Generator_V2_4_Basic.png)

**Workflow File:**  
[`AD&D Character Portrait Generator V2.4 - Basic.json`](Examples/AD%26D%20Character%20Portrait%20Generator%20V2.4%20-%20Basic.json)

---

## 🆕 V2.3 Workflow Highlights

The **AD&D Character Portrait Generator V2.3** workflow builds on the RPG character prompt system with several workflow improvements:

- 🧩 Updated upscale stages to use the newer **ComfyUI Subgraph** system
- 🎨 Added an **Anime Prep** stage to improve results when using likeness images with Anime-style generation
- 🧙 Expanded **AD&D / Fantasy** character classes
- 🤖 Added **Sci-Fi / Cyberpunk** character classes
- 👕 Expanded Fantasy and Sci-Fi / Cyberpunk clothing styles
- 🌍 Expanded scene selection with:
  - General / Neutral environments
  - AD&D / Fantasy environments and interiors
  - Sci-Fi / Cyberpunk environments and interiors
- 🍺 Added fantasy tavern and inn environments, including **Pub/Tavern Interior**
- 🧪 Added scientist, laboratory, corporate and research environments
- 🧬 Sci-Fi characters are **not required to have augmentations** — augment-free characters are fully supported

The workflow remains designed for straightforward character creation while allowing the individual character, clothing, scene, and visual style to be mixed and matched.

---

## 📦 Install via ComfyUI Manager (Recommended 🎉)

The node is now officially listed in **ComfyUI Manager**!

To install:

1. Launch **ComfyUI** and open **Manager** (via sidebar or `custom_nodes` menu).
2. Go to the **Install Custom Nodes** tab.
3. Search for: `RPG-Characters`
4. Click **Install**
5. Restart ComfyUI — you're ready to go!

---

## 🧱 Node Outputs

| Output Name                  | Description |
|-------------------------------|-------------|
| `positive_prompt`            | Standard positive tag string |
| `negative_prompt`            | Standard negative tag string |
| `Ollama_Positive_Textbox_1` | Detailed descriptive prompt for LLMs or advanced generators |
| `Ollama_Negative_Textbox_1` | Instructional template to guide LLMs on what to exclude |
| `Ollama_Positive_Textbox_2` | Extra prompt input for LLMs or advanced generators that have a second Text Input|

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

### 🔁 Prompt Switcher Example

**Prompt Switch Node Example:**  
![Switch Example](Examples/RPG_Nodes_Normal_and_Ollama_With_Switch.png)  
**Workflow File:**  
[`RPG_Nodes_Normal_and_Ollama_With_Switch.json`](Examples/RPG_Nodes_Normal_and_Ollama_With_Switch.json)

---

### 🧩 Full Node Collection

A visual reference of the full node layout.  
![Full Node Collection](Examples/Nodes_Collection.png)

---

## 🛠️ Manual Installation (if needed)

Clone this repo into your ComfyUI `custom_nodes` folder:

```bash
git clone https://github.com/lord-lethris/ComfyUI-RPG-Characters.git
```

Restart ComfyUI after installation.

---

## 🧠 Usage

1. Add the **RPG Art Style Selector** and RPG character nodes from the "RPG" category.  
2. Select the character traits, clothing style, scene, and art style you want.  
3. Mix Fantasy, Sci-Fi / Cyberpunk, and General / Neutral options as required.  
4. If using V2.4, use the **🧬 DNA Locker** to re-roll individual traits or the Master Seed, then optionally sculpt the DNA for finer control.  
5. Connect outputs as needed:  
   - `positive_prompt` / `negative_prompt` → your SD/SDXL/Flux prompt node  
   - `Ollama_Positive_Textbox_1` / `Ollama_Negative_Textbox_1` → LLM or prompt analysis/feedback tools  

---

## ⚠️ Optional Ollama Support Requirements

To use the **Ollama-driven prompt generation** features in this node, you need to:

- Install the [**Ollama server**](https://ollama.com/) on your desired host.
  - Download for [macOS](https://ollama.com/download/mac) or [Windows](https://ollama.com/download/windows)
- Install the [**ComfyUI-Ollama node**](https://github.com/stavsap/comfyui-ollama) by Stav Sapir

> Without these installed and running, the Ollama prompt outputs in this node will not function.

---

Credit for the [ComfyUI-Ollama node](https://github.com/stavsap/comfyui-ollama) goes to Stav Sapir ([stavsap](https://github.com/stavsap)).

---

## 🔮 Future Plans

- Dynamic LLM integration for auto-generating character prompts
- Additional art styles (e.g., pixel art, steampunk, noir)
- Further expansion of character classes, clothing styles, and environments
- Additional workflow improvements and generation presets

---

## 🐾 Made by Lord Lethris

Featuring Belle the cat, who disapproves of bad prompts. 🐱
