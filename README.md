# VimLM - Vim Language Model Assistant for privacy-conscious developers

![vimlm](https://github.com/user-attachments/assets/4aa39efe-aa6d-4363-8fe1-cf964d7f849c)

VimLM brings AI-powered assistance directly into Vim, keeping your workflow smooth and uninterrupted. Instead of constantly switching between your editor and external tools, VimLM provides real-time, context-aware suggestions, explanations, and code insights—all within Vim.

Unlike proprietary cloud-based AI models, VimLM runs entirely offline, ensuring complete privacy, data security, and control. You’re not just using a tool—you own it. Fine-tune, modify, or extend it as needed, without reliance on big tech platforms.

## Features

- **Real-Time Interaction with local LLMs**: Runs **fully offline** with local models (default: uncensored Llama-3.2-3B).
- **Integration with Vim's Native Workflow**: Simple Vim keybindings for quick access and split-window interface for non-intrusive responses.
- **Context-Awareness Beyond Single Files**: Inline support for external documents and project files for richer, more informed responses.
- **Conversational AI Assistance**: Goes beyond simple code suggestions-explains reasoning, provides alternative solutions, and allows interactive follow-ups. 
- **Versatile Use Cases**: Not just for coding-use it for documentation lookup, general Q&A, or even casual (uncensored) conversations.

## Installation

```zsh
pip install vimlm
```

## Usage

1. Start Vim with VimLM:

```zsh
vimlm
```

or

```zsh
vimlm your_file.js
```

2. **From Normal Mode**:
    - `Ctrl-l`: Send current line + file context
    - Example prompt: "Regex for removing html tags in item.content"

3. **From Visual Mode**:
    - Select text → `Ctrl-l`: Send selection + file context
    - Example prompt: "Convert this to async/await syntax"

4. **Add Context**: Use `!@#$` to include additional files/folders:
    - `!@#$` (no path): Current folder
    - `!@#$ ~/scrap/jph00/hypermedia-applications.summ.md`: Specific folder
    - `!@#$ ~/wtm/utils.py`: Specific file
    - Example prompt: "AJAX-ify this app !@#$ ~/scrap/jph00/hypermedia-applications.summ.md"

5. **Follow-Up**: After initial response:
    - `Ctrl-R`: Continue thread
    - Example follow-up: "In Manifest V3"

## Key Bindings

| Binding    | Mode          | Action                                 |
|------------|---------------|----------------------------------------|
| `Ctrl-L`   | Normal/Visual | Send current file + selection to LLM   |
| `Ctrl-R`   | Normal        | Continue conversation                  |
| `Esc`      | Prompt        | Cancel input                           |


