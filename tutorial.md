# VimLM: Bringing AI Assistance to Vim

At their core, LLMs generate chunks of text - code snippets, explanations, refactorings - that developers need to evaluate and integrate into their projects. 

Vim, with its efficient text manipulation and navigation capabilities, provides the perfect environment to harness the power of LLMs. Its modal design transforms editing into a fluid, keyboard-driven dialogue: yank fragments into registers for later use, leap between files with marks, or rewrite blocks with precision—all while maintaining unbroken focus. 

VimLM aims to seamlessly integrate LLMs into this workflow.

## Getting Started

### Installation
Install VimLM with a simple pip command:
```
$ pip install vimlm
```

### Launch
Start VimLM from your terminal:
```
$ vimlm
```

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0000.png)

You'll see a split interface with your editing pane on the left and the LLM response window on the right. The right window is where the AI assistant's outputs will appear.

## Basic Workflow

### Prompt the AI
To ask the LLM a question, press `Ctrl-l`

The command-line area will show "VimLM:" ready for your input. Type your request and press Enter.

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0010.png)

For example, ask for help creating a Chrome extension:
```
Create a Chrome Extension for copying selected content from webpages
```

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0020.png)

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0030.png)

The response is streamed asynchronously to the split window, freeing you to continue editing in the other window.

**TIP**: To focus only on the generated content, use `Ctrl-w w w o` to close the empty window and maximize the response window:

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0033.png)

### Follow-up Questions
When you need to refine or adjust the AI's response, press `Ctrl-j` to make a follow-up request. The previous context is maintained.

For example, if you notice the generated code uses an outdated manifest version:
```
Use manifest V3 instead
```

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0040.png)

### Deploy Generated Code
To extract code blocks from the response and save them as separate files, use the `!deploy` command in a follow-up prompt (`Ctrl-j`):

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0050.png)

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0060.png)

### Apply Suggestions to Your Code
Open the file you want to edit: `:e popup.js` (or `vimlm popup.js` in terminal)

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0070.png)

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0071.png)

Make a selection and press `Ctrl-l` and ask a specific question about the selected code:
```
VimLM: how to get rid of html tags from item.content
```

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0100.png)

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0110.png)

When you see a solution you like, press `Ctrl-p` to apply the suggested code fix directly to your selection.

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0120.png)

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0130.png)

**TIP**: `gg=G` auto-indents the entire file:

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0140.png)

**TIP**: If the suggested code change doesn't match your original selection, press `gv` to return to your previous selection, then use `o` to switch between the start and end points to adjust as needed.

### Adding Context
VimLM defaults to layered context - your active selection and the entire current file are automatically included alongside prompts. But as Vim's creator Bram Moolenaar noted, *"a file seldom comes alone"*([source](https://www.moolenaar.net/habits.html)). You can use `!include` to add more context to the query:
```
AJAX-ify this app !include ~/scrap/hypermedia-applications.summ.md
```

It can be used to automate tedious parts of development, such as reviewing changes for a commit message:
```
Git commit message for the code changes !include $(git diff popup.js)
```

![](https://raw.githubusercontent.com/JosefAlbers/VimLM/main/assets/0150.png)

Or to generate changelogs after a version update:
```
Summarize the changes !include $(git log --oneline -n 50)
```

You can also pipe and filter to focus on specific patterns, just as you would in a terminal:
```
Diagnose server errors !include $(grep -r "500 Internal Error" ./fuzz | head -n 5)
```

### Ex Commands
For frequently used LLM workflows, VimLM provides the `:VimLM` command, allowing you to create and store reusable prompting patterns. A few examples:
```
" Debug CI failures using error logs
:VimLM Fix Dockerfile !include .gitlab-ci.yml !include $(tail -n 20 ci.log)

" Generate unit tests for selected functions and save to test/
:VimLM Write pytest tests for this !include ./src !deploy ./test

" Add docstrings to all Python functions in file
:VimLM Add Google-style docstrings !include % !continue 4000
```

### Changing the LLM Model
By default, VimLM uses an uncensored Llama 3.2 3B model with token limit of 2000. You can switch to any MLX-compatible model:
```json
{
  "LLM_MODEL": "mlx-community/DeepSeek-R1-Distill-Qwen-7B-4bit",
  "NUM_TOKEN": 32768
}
```

Save to `~/vimlm/cfg.json` and restart VimLM.

## Conclusion

Vim's efficiency and LLM capabilities are a perfect match. VimLM bridges this gap, giving you AI assistance without leaving your favorite editor. Whether you're writing code, fixing bugs, or exploring new frameworks, VimLM helps you stay in flow while leveraging AI power.
