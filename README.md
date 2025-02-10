# VimLM - Local LLM-Powered Coding Assistant for Vim

![vimlm](https://github.com/user-attachments/assets/67a97048-48df-40c1-9109-53c759e85d96)

An LLM-powered coding companion for Vim, inspired by GitHub Copilot/Cursor. Integrates contextual code understanding, summarization, and AI assistance directly into your Vim workflow.

## Features

- **Model Agnostic** - Use any MLX-compatible model via config file
- **Vim-Native UX** - Ctrl-l/Ctrl-r keybindings and split-window responses
- **Deep Context** - Understands code context from:
    - Current file
    - Visual selections
    - Referenced files
    - Project directory structure
- **Conversational Coding** - Iterative refinement with follow-up queries
- **Air-Gapped Security** - 100% offline - no APIs, no tracking, no data leaks

## Requirements

- Apple M-series chip (M1/M2/M3/M4)
- Python 3.12.8

## Installation

```zsh
pip install vimlm
```

## Quick Start

1. Launch with default model (DeepSeek-R1-Distill-Qwen-7B-4bit):

```zsh
vimlm your_file.js
```

2. **From Normal Mode**:
    - `Ctrl-l`: Send current line + file context
    - Example prompt: "Regex for removing html tags in item.content"

3. **From Visual Mode**:
    - Select code → `Ctrl-l`: Send selection + file context
    - Example prompt: "Convert this to async/await syntax"

4. **Add Context**: Use `!@#$` to include additional files/folders:
    - `!@#$` (no path): Current folder
    - `!@#$ ~/scrap/jph00/hypermedia-applications.summ.md`: Specific folder
    - `!@#$ ~/wtm/utils.py`: Specific file
    - Example prompt: "AJAX-ify this app !@#$ ~/scrap/jph00/hypermedia-applications.summ.md"

5. **Follow-Up**: After initial response:
    - `Ctrl-r`: Continue thread
    - Example follow-up: "In Manifest V3"

## Advanced Configuration

### Custom Model Setup

1. **Browse models**: [MLX Community Models on Hugging Face](https://huggingface.co/mlx-community)

2. **Edit config file**:

```json
{
 "LLM_MODEL": "/path/to/your/mlx_model"
}
```

3. **Save to**:

```
~/vimlm/cfg.json
```

4. **Restart VimLM**

## Key Bindings

| Binding    | Mode          | Action                                 |
|------------|---------------|----------------------------------------|
| `Ctrl-l`   | Normal/Visual | Send current file + selection to LLM   |
| `Ctrl-r`   | Normal        | Continue conversation                  |
| `Esc`      | Prompt        | Cancel input                           |


