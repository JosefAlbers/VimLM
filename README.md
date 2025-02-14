
# VimLM - Local LLM-Powered Coding Assistant for Vim

![vimlm](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/captioned_vimlm.gif)

LLM-powered coding companion for Vim, inspired by GitHub Copilot/Cursor. Integrates contextual code understanding, summarization, and AI assistance directly into your Vim workflow.

## Features

- **Model Agnostic** - Use any MLX-compatible model via a configuration file
- **Vim-Native UX** - Intuitive keybindings and split-window responses
- **Deep Context** - Understands code context from:
    - Current file
    - Visual selections
    - Referenced files
    - Project directory structure
- **Conversational Coding** - Iterative refinement with follow-up queries
- **Air-Gapped Security** - 100% offline - no APIs, no tracking, no data leaks

## Requirements

- Apple M-series chip
- Python 3.12.8

## Quick Start

Install:

```zsh
pip install vimlm
```

Launch:

```zsh
vimlm
```

or

```zsh
vimlm path/to/your_file
```

This launches Vim with the LLM in a split window, ready to assist you.

## Basic Usage

1. **From Normal Mode**:
    - `Ctrl-l`: Adds current line + file to context
    - Example prompt: "Regex for removing html tags from item.content"

2. **From Visual Mode**:
    - Select code → `Ctrl-l`: Adds selected block + current file to context
    - Example prompt: "Convert this to async/await syntax"

3. **Inline Commands**:

!include: Adds specified outside files/folders to context:
    - `!include` (no path): Current folder
    - `!include ~/scrap/jph00/hypermedia-applications.summ.md`: Specific folder
    - `!include ~/wtm/utils.py`: Specific file
    - Example prompt: "AJAX-ify this app @ ~/scrap/jph00/hypermedia-applications.summ.md"

!deploy: Extract code blocks to files in user specified dir (current dir if none specified).

!continue: Lets the LLM resume the generation from where it had halted due to length limits.

!followup: Continue the thread (equivalent to `Ctrl-j`

4. **Follow-Up**: After initial response:
    - `Ctrl-j`: Continue thread
    - Example follow-up: "In Manifest V3"

4. **Code Extraction: Press `Ctrl-p` to choose a code block from the response and insert them into:
    - The last selected visual block (in Normal mode)
    - The current selection (in Visual mode)
    - Example workflow:
        1. Select a block of code in Visual mode.
        2. Prompt the LLM with `Ctrl-l` (e.g., "Convert this to async/await syntax").
        3. Once the response is generated, press `Ctrl-p` to replace the selected block with the extracted code.

### Key Bindings

| Binding    | Mode          | Action                                 |
|------------|---------------|----------------------------------------|
| `Ctrl-l`   | Normal/Visual | Send current file + selection to LLM   |
| `Ctrl-j`   | Normal        | Continue conversation                  |
| `Ctrl-p`   | Normal/Visual | Replace the selection with generated code |
| `Esc`      | Prompt        | Cancel input                           |

## Advanced Configuration

VimLM uses a JSON config file with the following configurable parameters:

```json
{
  "DEBUG": true,
  "LLM_MODEL": null,
  "NUM_TOKEN": 2000,
  "SEP_CMD": "!",
  "USE_LEADER": false
}
```

### Custom Model Setup

1. **Browse models**: [MLX Community Models on Hugging Face](https://huggingface.co/mlx-community)

2. **Edit config file**:

```json
{
  "LLM_MODEL": "mlx-community/DeepSeek-R1-Distill-Qwen-7B-4bit"
}
```
3. **Save to**:

```
~/vimlm/config.json
```

4. **Restart VimLM**


### Custom Keybinding

If you prefer using `<Leader>` in place of `<Ctrl>` for the ViMLM key bindings:

```json
{
  "USER_LEADER": true
}
```


