# ComfyUI-RPG-Characters

A collection of custom nodes for ComfyUI that generate richly detailed RPG character portrait prompts with various art style options. Designed to work seamlessly with SDXL and Ollama for RPG-themed AI character image generation.

---

## Features

- Select from multiple art styles: Anime, Dark Fantasy, Realistic, Fantasy Illustration, Pixar Animation, and more.
- Generate descriptive, detailed portrait prompts including race, ethnicity, gender, class, emotion, and scene.
- Separate node to choose between standard or Ollama-style positive and negative prompts.
- Easily extendable for new styles or prompt customization.

---

## Installation

1. Clone this repository into your ComfyUI `custom_nodes` folder:

    cd path/to/ComfyUI/custom_nodes
    git clone https://github.com/lord-lethris/ComfyUI-RPG-Characters.git

2. Restart ComfyUI to load the new nodes.

---

## Usage

- Use the RPG Art Style Selector node to generate base prompts and positive/negative prompt pairs.
- Use the Prompt Selector node to switch between standard and Ollama prompt versions.
- Connect outputs to your text-to-image or SDXL pipeline as needed.

---

## Example

Select `Anime Style` in the Art Style Selector and connect its outputs to the Prompt Selector to toggle prompt sets based on your preference.

---

## Contributing

Feel free to submit issues or pull requests to add new art styles, improve prompts, or fix bugs. Open to collaboration!

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.
