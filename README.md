
# VimLM - AI-Powered Coding Assistant for Vim

![VimLM Demo](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/captioned_vimlm.gif)

VimLM brings the power of AI directly into your Vim workflow. Maintain focus with keyboard-driven interactions while leveraging AI for code generation, refactoring, and documentation.

Get started quickly with the [tutorial](tutorial.md).

## Features
- **Native Vim Integration** - Split-window responses & intuitive keybindings
- **Offline First** - 100% local execution with MLX-compatible models
- **Contextual Awareness** - Integrates seamlessly with your codebase and external resources
- **Conversational Workflow** - Iterate on responses with follow-up queries
- **Project Scaffolding** - Generate and deploy code blocks to directories
- **Extensible** - Create custom LLM workflows with command chains

## Requirements
- Apple Silicon (M-series)
- Python 3.12.8
- Vim 9.1

## Quick Start
```bash
pip install vimlm
vimlm
```

## Basic Usage

| Key Binding | Mode          | Action                                 |
|-------------|---------------|----------------------------------------|
| `Ctrl-l`    | Normal/Visual | Prompt LLM                             |
| `Ctrl-j`    | Normal        | Continue conversation                  |
| `Ctrl-p`    | Normal/Visual | Import generated code                  |
| `Esc`       | Prompt        | Cancel input                           |

### 1. **Contextual Prompting**
`Ctrl-l` to prompt LLM with context:
- Normal mode: Current file + line
- Visual mode: Current file + selected block

*Example Prompt*: `Create a Chrome extension`

### 2. **Conversational Refinement**
`Ctrl-j` to continue current thread.

*Example Prompt*: `Use manifest V3 instead`

### 3. **Code Substitution**
`Ctrl-p` to insert generated code block
- In Normal mode: Into last visual selection
- In Visual mode: Into current visual selection 

*Example Workflow*:  
1. Select a block of code in Visual mode  
2. Prompt with `Ctrl-l`: `Use regex to remove html tags from item.content`  
3. Press `Ctrl-p` to replace selection with generated code  

## Inline Directives
```text
:VimLM [PROMPT] [!command1] [!command2]...
```

`!` prefix to embed inline directives in prompts:

| Directive        | Description                              |
|------------------|------------------------------------------|
| `!include PATH`  | Add file/directory/shell output to context |
| `!deploy DEST`   | Save code blocks to directory            |
| `!continue N`    | Continue stopped response                |
| `!followup`      | Continue conversation           |

### 1. **Context Layering**
```text
!include [PATH]  # Add files/folders to context
```
- **`!include`** (no path): Current folder  
- **`!include ~/projects/utils.py`**: Specific file  
- **`!include ~/docs/api-specs/`**: Entire folder  
- **`!include $(...)`**: Shell command output

*Example*: `Summarize recent changes !include $(git log --oneline -n 50)`

### 2. **Code Deployment**
```text
!deploy [DEST_DIR]  # Extract code blocks to directory
```
- **`!deploy`** (no path): Current directory  
- **`!deploy ./src`**: Specific directory  

*Example:* `Create REST API endpoint !deploy ./api`

### 3. **Extending Response**
```text
!continue [MAX_TOKENS]  # Continue stopped response
```
- **`!continue`**: Default 2000 tokens  
- **`!continue 3000`**: Custom token limit  

*Example:* `tl;dr !include large-file.txt !continue 5000`

## Command-Line Mode
```vim
:VimLM prompt [!command1] [!command2]...
```

Simplify complex tasks by chaining multiple commands together into a single, reusable Vim command.

*Examples*:
```vim
" Debug CI failures using error logs
:VimLM Fix Dockerfile !include .gitlab-ci.yml !include $(tail -n 20 ci.log)

" Generate unit tests for selected functions and save to test/
:VimLM Write pytest tests for this !include ./src !deploy ./test

" Add docstrings to all Python functions in file
:VimLM Add Google-style docstrings !include % !continue 4000
```

## Configuration

### 1. **Model Settings**
Edit `~/vimlm/cfg.json`:
```json
{
  "LLM_MODEL": "mlx-community/DeepSeek-R1-Distill-Qwen-7B-4bit",
  "NUM_TOKEN": 32768
}
```

### 2. **Key Customization**
```json
{
  "USE_LEADER": true,
  "KEY_MAP": {
    "l": "]",
    "j": "[",
    "p": "p" 
  }
}
```

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.
