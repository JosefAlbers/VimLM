# Copyright 2025 Josef Albers
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import subprocess
import json
import os
from watchfiles import awatch
import shutil
from datetime import datetime
from itertools import accumulate
import argparse
import tempfile
from pathlib import Path
from string import Template
import re

DEFAULTS = dict(
    LLM_MODEL = None, # "mlx-community/DeepSeek-R1-Distill-Qwen-7B-4bit"
    NUM_TOKEN = 2000,
    USE_LEADER = False,
    KEY_MAP = {},
    DO_RESET = True,
    SHOW_USER = False, 
    SEP_CMD = '!',
    VERSION = '0.0.9',
    DEBUG = False,
)

DATE_FORM = "%Y_%m_%d_%H_%M_%S"
VIMLM_DIR = os.path.expanduser("~/vimlm")
WATCH_DIR = os.path.expanduser("~/vimlm/watch_dir")
CFG_FILE = 'cfg.json'
LOG_FILE = "log.json"
LTM_FILE = "cache.json"
OUT_FILE = "response.md"
IN_FILES = ["context", "yank", "user", "tree"]
CFG_PATH = os.path.join(VIMLM_DIR, CFG_FILE)
LOG_PATH = os.path.join(VIMLM_DIR, LOG_FILE)
LTM_PATH = os.path.join(VIMLM_DIR, LTM_FILE)
OUT_PATH = os.path.join(WATCH_DIR, OUT_FILE) 

def is_old(config):
    v_str = config.get('VERSION', 0)
    for min_v, usr_v in zip(DEFAULTS['VERSION'].split('.'), v_str.split('.')):
        if int(min_v) < int(usr_v):
            return False
        elif int(min_v) > int(usr_v): 
            return True
    return False

if os.path.exists(WATCH_DIR):
    shutil.rmtree(WATCH_DIR)
os.makedirs(WATCH_DIR)

try:
    with open(CFG_PATH, "r") as f:
        config = json.load(f)
    if is_old(config):
        for p in [CFG_PATH, LOG_PATH, LTM_PATH]:
            if os.path.isfile(p):
                os.remove(p)
        raise ValueError(f'Updating config')
except Exception as e:
    print(e)
    config = DEFAULTS
    with open(CFG_PATH, 'w') as f:
        json.dump(DEFAULTS, f, indent=2)

for k, v in DEFAULTS.items():
    globals()[k] = config.get(k, v)

def toout(s, key=None, mode=None):
    key = '' if key is None else ':'+key
    mode = 'w' if mode is None else mode
    with open(OUT_PATH, mode, encoding='utf-8') as f:
        f.write(s)
    tolog(s, key='tovim'+key+':'+mode)

def tolog(log, key='debug'):
    if not DEBUG and key == 'debug':
        return
    try:
        with open(LOG_PATH, "r", encoding="utf-8") as log_f:
            logs = json.load(log_f)
    except:
        logs = []
    logs.append(dict(key=key, log=log, timestamp=datetime.now().strftime(DATE_FORM)))
    with open(LOG_PATH, "w", encoding="utf-8") as log_f:
        json.dump(logs, log_f, indent=2)

def print_log():
    with open(LOG_PATH, 'r') as f:
        logs = json.load(f)
    for log in logs:
        print(f'\033[37m{log["key"]} {log["timestamp"]}\033[0m')
        if 'tovim' in log["key"]:
            print('\033[33m')
        elif 'tollm' in log["key"]:
            print('\033[31m')
        print(log["log"])
        print('\033[0m')

toout('Loading LLM...')
if LLM_MODEL is None:
    from nanollama import Chat
    chat = Chat(model_path='uncn_llama_32_3b_it')
    toout(f'LLM is ready')
else:
    from mlx_lm_utils import Chat
    chat = Chat(model_path=LLM_MODEL)
    toout(f'{model_path.split('/')[-1]} is ready')

def deploy(dest=None, src=None, reformat=True):
    prompt_deploy = 'Reformat the text to ensure each code block is preceded by a filename in **filename.ext** format, with only alphanumeric characters, dots, underscores, or hyphens in the filename. Remove any extraneous characters from filenames.'
    tolog(f'deploy {dest=} {src=} {reformat=}')
    if src:
        chat.reset()
        with open(src, 'r') as f:
            prompt_deploy = f.read().strip() + '\n\n---\n\n' + prompt_deploy
    if reformat:
        toout('Deploying...')
        response = chat(prompt_deploy, max_new=NUM_TOKEN, verbose=False, stream=False)['text']
        toout(response, 'deploy')
        lines = response.splitlines()
    else:
        with open(OUT_PATH, 'r') as f:
            lines = f.readlines()
    dest = get_path(dest)
    os.makedirs(dest, exist_ok=True)
    current_filename = None
    code_block = []
    in_code_block = False
    for line in lines:
        line = line.rstrip()
        if line.startswith("```"):
            if in_code_block and current_filename:
                with open(os.path.join(dest, os.path.basename(current_filename)), "w", encoding="utf-8") as code_file:
                    code_file.write("\n".join(code_block) + "\n")
                code_block = []
            in_code_block = not in_code_block
        elif in_code_block:
            code_block.append(line)
        else:
            match = re.match(r"^\*\*(.+?)\*\*$", line)
            if match:
                current_filename = re.sub(r"[^a-zA-Z0-9_.-]", "", match.group(1))

def is_binary(file_path):
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            chunk.decode('utf-8') 
        return False 
    except UnicodeDecodeError:
        return True
    except Exception as e:
        return f"Error: {e}"

def split_str(doc, max_len=2000, get_len=len):
    chunks, current_chunk, current_len = [], [], 0
    lines = doc.splitlines(keepends=True)
    atomic_chunks, temp = [], []
    for line in lines:
        if line.strip():
            temp.append(line)
        else:
            if temp:
                atomic_chunks.append("".join(temp))
                temp = []
            atomic_chunks.append(line) 
    if temp:
        atomic_chunks.append("".join(temp))
    for chunk in atomic_chunks:
        if current_len + get_len(chunk) > max_len and current_chunk:
            chunks.append("".join(current_chunk))
            current_chunk, current_len = [], 0
        current_chunk.append(chunk)
        current_len += get_len(chunk)
    if current_chunk:
        if current_len < max_len / 2 and len(chunks) > 0:
            chunks[-1] += "".join(current_chunk)
        else:
            chunks.append("".join(current_chunk))
    return chunks

def retrieve(src_path, max_len=2000, get_len=len):
    src_path = get_path(src_path)
    result = {}
    if not os.path.exists(src_path):
        tolog(f"The path {src_path} does not exist.", 'retrieve')
        return result
    if os.path.isfile(src_path):
        try:
            with open(src_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            result = {src_path:dict(timestamp=os.path.getmtime(src_path), list_str=split_str(content, max_len=max_len, get_len=get_len))}
        except Exception as e:
            tolog(f'Failed to retrieve({filename}) due to {e}')
    else:
        for filename in os.listdir(src_path):
            try:
                file_path = os.path.join(src_path, filename)
                if filename.startswith('.') or is_binary(file_path):
                    continue
                if os.path.isfile(file_path):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    result[file_path] = dict(timestamp=os.path.getmtime(file_path), list_str=split_str(content, max_len=max_len, get_len=get_len))
            except Exception as e:
                tolog(f'Failed to retrieve({filename}) due to {e}')
                continue
    return result

def get_path(s):
    if not s:
        s = '.'
    s = s.strip()
    s = os.path.expanduser(s)
    s = os.path.abspath(s)
    return s

def ingest(src, max_len=NUM_TOKEN):
    def load_cache(cache_path=LTM_PATH):
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    def dump_cache(new_data, cache_path=LTM_PATH):
        current_data = load_cache(cache_path)
        for k, v in new_data.items():
            if k not in current_data or v['timestamp'] > current_data[k]['timestamp']:
                current_data[k] = v
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2)
    src = get_path(src)
    tolog(f'ingest {src=}')
    result = ''
    src_base = os.path.basename(src)
    if os.path.isdir(src):
        listdir = [i for i in os.listdir(src) if not i.startswith('.') and '.' in i]
        result = '\n- '.join([f'--- {src_base} ---', *listdir]) + '\n\n'
    elif os.path.isfile(src):
        result = ''
    else:
        tolog(f'Failed to ingest({src})')
        return ''
    dict_doc = retrieve(src, max_len=max_len, get_len=chat.get_ntok)
    toout(f'Ingesting {src}...')
    format_ingest = '{volat}{incoming}\n\n---\n\nPlease provide a succint bullet point summary for above:' 
    format_volat = 'Here is a summary of part 1 of **{k}**:\n\n---\n\n{newsum}\n\n---\n\nHere is the next part:\n\n---\n\n' 
    dict_sum = {}
    cache = load_cache()
    max_new_accum = int(max_len/len(dict_doc)) if len(dict_doc) > 0 else max_len
    for k, v in dict_doc.items():
        list_str = v['list_str']
        v_stamp = v['timestamp']
        if len(list_str) == 0:
            continue
        if len(list_str) == 1 and chat.get_ntok(list_str[0]) <= max_new_accum:
            chat_summary = list_str[0]
        else:
            k_base = os.path.basename(k)
            if v_stamp == cache.get(k, {}).get('timestamp'):
                dict_sum[k] = cache[k]
                continue
            max_new_sum = int(max_len/len(list_str))
            volat = f'**{k}**:\n'
            accum = ''
            for i, s in enumerate(list_str):
                chat.reset()
                toout(f'\n\nIngesting {k_base} {i+1}/{len(list_str)}...\n\n', mode='a')
                tolog(f'{s=}') # DEBUG
                newsum = chat(format_ingest.format(volat=volat, incoming=s.rstrip()), max_new=max_new_sum, verbose=False, stream=OUT_PATH)['text'].rstrip()
                tolog(f'{k} {i+1}/{len(list_str)}: {newsum=}') # DEBUG
                accum += newsum + ' ...\n'
                volat = format_volat.format(k=k, newsum=newsum)
            toout(f'\n\nIngesting {k_base}...\n\n', mode='a')
            tolog(f'{accum=}') # DEBUG
            if chat.get_ntok(accum) <= max_new_accum:
                chat_summary = accum.strip()
            else:
                chat.reset()
                chat_summary = chat(format_ingest.format(volat=f'**{k}**:\n', incoming=accum), max_new=max_new_accum, verbose=False, stream=OUT_PATH)['text'].strip()
        dict_sum[k] = dict(timestamp=v_stamp, summary=chat_summary, ntok=chat.get_ntok(chat_summary))
    dump_cache(dict_sum)
    for k, v in dict_sum.items():
        result += f'--- **{os.path.basename(k)}** ---\n{v["summary"].strip()}\n\n'
    result += '---\n\n'
    toout(result, 'ingest')
    return result

def process_command(data):
    if len(data['user']) == 0:
        response = chat.resume(max_new=NUM_TOKEN, verbose=False, stream=OUT_PATH)
        toout(response['text'], mode='a')
        tolog(response)
        data['user_prompt'] = ''
        return data
    if SEP_CMD in data['user']:
        data['user_prompt'], *cmds = (x.strip() for x in data['user'].split(SEP_CMD))
    else:
        data['user_prompt'] = data['user'].strip()
        cmds = []
    tolog(f'process_command i {cmds=} {data=}')

    do_reset = False if 'followup' in data else DO_RESET 
    for cmd in cmds:
        if cmd.startswith('continue'):
            arg = cmd.removeprefix('continue').strip('(').strip(')').strip().strip('"').strip("'").strip()
            data['max_new'] = NUM_TOKEN if len(arg) == 0 else int(arg)
            response = chat.resume(max_new=data['max_new'], verbose=False, stream=OUT_PATH)
            toout(response['text'], mode='a')
            tolog(response)
            do_reset = False
            break

        if cmd.startswith('reset'):
            do_reset = True
            break
        if cmd.startswith('followup'):
            do_reset = False
            break
    if do_reset:
        chat.reset()

    full_path = data['tree']
    data['dir'] = os.path.dirname(full_path)
    data['file'] = os.path.basename(full_path)
    data['ext'] = os.path.splitext(full_path)[1][1:]
    if chat.stop:
        data['file'] = ''
        data['context'] = ''
    if data['tree'] == OUT_PATH:
        data['dir'] = os.getcwd()
        data['file'] = ''
        data['context'] = ''
        data['ext'] = ''
    if data['file'] == '.tmp':
        data['file'] = ''
        data['ext'] = ''

    if len(cmds) == 1 and len(cmds[0]) == 0:
        data['include'] = ingest(data['dir'])
        return data

    data['include'] = ''
    for cmd in cmds:
        if cmd.startswith('include'):
            arg = cmd.removeprefix('include').strip().strip('(').strip(')').strip().strip('"').strip("'").strip()
            src = data['dir'] if len(arg) == 0 else arg
            if arg == '%':
                continue
            if src.startswith('`') or src.startswith('$('):
                shell_cmd = src.strip('`') if src.startswith('`') else src.strip('$()')
                shell_cmd = shell_cmd.strip()
                try:
                    result = subprocess.run(shell_cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        data['include'] += f'--- **{shell_cmd}** ---\n```\n{result.stdout.strip()}\n```\n---\n\n'
                    else:
                        tolog(f'{shell_cmd} failed {result.stderr.strip()}')
                except Exception as e:
                    tolog(f'Error executing {shell_cmd}: {e}')
            else:
                data['include'] += ingest(src)

    for cmd in cmds:
        if cmd.startswith('deploy'):
            arg = cmd.removeprefix('deploy').strip().strip('(').strip(')').strip().strip('"').strip("'").strip()
            if len(data['user_prompt']) == 0:
                deploy(dest=arg)
                data['user_prompt'] = ''
                return data
            data['user_prompt'] += "\n\nEnsure that each code block is preceded by a filename in **filename.ext** format. The filename should only contain alphanumeric characters, dots, underscores, or hyphens. Ensure that any extraneous characters are removed from the filenames."
            data['deploy_dest'] = arg
    for cmd in cmds:
        if cmd.startswith('write'):
            arg = cmd.removeprefix('write').strip().strip('(').strip(')').strip().strip('"').strip("'").strip()
            if len(arg) == 0:
                arg = 'response'
                pass
            timestamp = datetime.now().strftime(DATE_FORM)
            data['write_dest'] = re.sub(r"[^a-zA-Z0-9_.-]", "", f'{arg}_{timestamp}.md')
    return data
    
async def monitor_directory():
    async for changes in awatch(WATCH_DIR):
        found_files = {os.path.basename(f) for _, f in changes}
        tolog(f'{found_files=}') # DEBUG
        if IN_FILES[-1] in found_files and set(IN_FILES).issubset(set(os.listdir(WATCH_DIR))):
            tolog(f'listdir()={os.listdir(WATCH_DIR)}') # DEBUG
            data = {}
            for file in IN_FILES:
                path = os.path.join(WATCH_DIR, file)
                with open(path, 'r', encoding='utf-8') as f:
                    data[file] = f.read().strip()
                os.remove(os.path.join(WATCH_DIR, file))
            if 'followup' in os.listdir(WATCH_DIR):
                os.remove(os.path.join(WATCH_DIR, 'followup'))
                data['followup'] = True
            if 'quit' in os.listdir(WATCH_DIR):
                os.remove(os.path.join(WATCH_DIR, 'quit'))
                data['quit'] = True
            await process_files(data)

async def process_files(data):
    tolog(f'process_files i {data=}')
    str_template = '{include}'
    data = process_command(data)
    if len(data['user_prompt']) == 0:
        return    
    if len(data['file']) > 0:
        str_template += '**{file}**\n'
    if len(data['context']) > 0 and data['yank'] != data['context']:
        str_template += '```{ext}\n{context}\n```\n\n'
    if len(data['yank']) > 0:
        if '\n' in data['yank']:
            str_template += "```{ext}\n{yank}\n```\n\n"
        else:
            if data['user'] == 0:
                str_template += "{yank}"
            else:
                str_template += "`{yank}` "
    str_template += '{user_prompt}'
    tolog(f'process_files o {data=}') # DEBUG
    tolog(f'process_files {str_template=}') # DEBUG
    prompt = str_template.format(**data)
    tolog(prompt, 'tollm')
    toout('')
    max_new = data['max_new'] if 'max_new' in data else max(10, NUM_TOKEN - chat.get_ntok(prompt))
    response = chat(prompt, max_new=max_new, verbose=False, stream=OUT_PATH)
    if SHOW_USER:
        toout(response['text'])
    else:
        toout(response['text'])
    tolog(response)
    if 'write_dest' in data:
        with open(data['write_dest'], 'w') as f:
            f.write(response['text'])
    if 'deploy_dest' in data:
        deploy(dest=data['deploy_dest'], reformat=False)

KEYL = KEY_MAP.get('l', 'l')
KEYJ = KEY_MAP.get('j', 'j')
KEYP = KEY_MAP.get('p', 'p')
mapl, mapj, mapp = (f'<Leader>{KEYL}', f'<Leader>{KEYJ}', f'<Leader>{KEYP}') if USE_LEADER else (f'<C-{KEYL}>', f'<C-{KEYJ}>', f'<C-{KEYP}>')
VIMLMSCRIPT = Template(r"""
let s:register_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u'] 
let s:watched_dir = expand('$WATCH_DIR')
let s:vimlm_enabled = 1

function! ToggleVimLM()
    if s:vimlm_enabled
        let s:vimlm_enabled = 0
        let response_path = s:watched_dir . '/response.md'
        let bufnum = bufnr(response_path)
        let winid = bufwinnr(bufnum)
        if winid != -1
            execute winid . 'wincmd c'
        endif
        if exists('s:monitor_timer')
            call timer_stop(s:monitor_timer)
            unlet s:monitor_timer
        endif
        echohl WarningMsg | echom "VimLM disabled" | echohl None
    else
        let s:vimlm_enabled = 1
        silent! call Monitor()
        echohl WarningMsg | echom "VimLM enabled" | echohl None  
    endif
endfunction

function! CheckForUpdates(timer)
    if !s:vimlm_enabled
        return
    endif
    let bufnum = bufnr(s:watched_dir . '/response.md')
    let winid = bufwinnr(bufnum)
    if winid == -1
        call timer_stop(s:monitor_timer)
        unlet s:monitor_timer
        call Monitor()
    else
        silent! checktime
    endif
endfunction

function! Monitor()
    if exists('s:monitor_timer')
        call timer_stop(s:monitor_timer)
        unlet s:monitor_timer
    endif
    let response_path = s:watched_dir . '/response.md'
    let bufnum = bufnr(response_path)
    if bufnum != -1
        execute 'bwipeout ' . bufnum
    endif
    let response_path = s:watched_dir . '/response.md'
    rightbelow vsplit | execute 'view ' . response_path
    setlocal autoread
    setlocal readonly
    setlocal nobuflisted
    filetype detect
    syntax on
    wincmd h
    let s:monitor_timer = timer_start(100, 'CheckForUpdates', {'repeat': -1})
endfunction

function! ScrollToTop()
    let bufnum = bufnr(s:watched_dir . '/response.md')
    if bufnum != -1
        let winid = bufwinnr(bufnum)
        if winid > 0
            execute winid . "wincmd w"
            normal! gg
            wincmd p
        endif
    endif
endfunction

function! s:CustomInput(prompt) abort
    call inputsave()
    let input = input(a:prompt)
    call inputrestore()
    if empty(input)
        return v:null
    endif
    return input
endfunction

function! SaveUserInput(prompt)
    let user_input = s:CustomInput(a:prompt)
    if user_input is v:null
        echo "Input aborted"
        return
    endif
    let user_file = s:watched_dir . '/user'
    call writefile([user_input], user_file, 'w')
    let current_file = expand('%:p')
    let tree_file = s:watched_dir . '/tree'
    call writefile([current_file], tree_file, 'w')
    call ScrollToTop()
endfunction

function! VisualPrompt()
    silent! execute "normal! \<ESC>"
    silent execute "'<,'>w! " . s:watched_dir . "/yank"
    silent execute "w! " . s:watched_dir . "/context"
    call SaveUserInput('VimLM: ')
endfunction

function! NormalPrompt()
    silent! execute "normal! V\<ESC>"
    silent execute "'<,'>w! " . s:watched_dir . "/yank"
    silent execute "w! " . s:watched_dir . "/context"
    call SaveUserInput('VimLM: ')
endfunction

function! FollowUpPrompt()
    call writefile([], s:watched_dir . '/yank', 'w')
    call writefile([], s:watched_dir . '/context', 'w')
    call writefile([], s:watched_dir . '/followup', 'w')
    call SaveUserInput('... ')
endfunction

function! ExtractAllCodeBlocks()
    let filepath = s:watched_dir . '/response.md'
    if !filereadable(filepath)
        echoerr "File not found: " . filepath
        return
    endif
    let lines = readfile(filepath)
    let in_code_block = 0
    let code_blocks = []
    let current_block = []
    for line in lines
        if line =~ '^```'
            if in_code_block
                call add(code_blocks, current_block)
                let current_block = []
                let in_code_block = 0
            else
                let in_code_block = 1
            endif
        elseif in_code_block
            call add(current_block, line)
        endif
    endfor
    if in_code_block
        call add(code_blocks, current_block)
    endif
    for idx in range(len(code_blocks))
        if idx >= len(s:register_names)
            break
        endif
        let code_block_text = join(code_blocks[idx], "\n")
        let register_name = s:register_names[idx]
        call setreg(register_name, code_block_text, 'v') 
    endfor
    return len(code_blocks)
endfunction

function! PasteIntoLastVisualSelection(...)
    let num_blocks = ExtractAllCodeBlocks()
    if a:0 > 0
        let register_name = a:1
    else
        echo "Extracted " . num_blocks . " blocks into registers @a-@" . s:register_names[num_blocks - 1] . ". Enter register name: "
        let register_name = nr2char(getchar())
    endif
    if register_name !~ '^[a-z]$'
        echoerr "Invalid register name. Please enter a single lowercase letter (e.g., a, b, c)."
        return
    endif
    let register_content = getreg(register_name)
    if register_content == ''
        echoerr "Register @" . register_name . " is empty."
        return
    endif
    let current_mode = mode()
    if current_mode == 'v' || current_mode == 'V' || current_mode == ''
        execute 'normal! "' . register_name . 'p'
    else
        normal! gv
        execute 'normal! "' . register_name . 'p'
    endif
endfunction

function! VimLM(...) range
    let tree_file = s:watched_dir . '/tree'
    while filereadable(tree_file)
        sleep 100m
    endwhile
    let user_input = join(a:000, ' ')
    if empty(user_input)
        echo "Usage: :VimLM <prompt> [!command1] [!command2] ..."
        return
    endif
    if line("'<") == line("'>")
        silent! execute "normal! V\<ESC>"
    endif
    silent execute "'<,'>w! " . s:watched_dir . "/yank"
    silent execute "w! " . s:watched_dir . "/context"
    let user_file = s:watched_dir . '/user'
    call writefile([user_input], user_file, 'w')
    let current_file = expand('%:p')
    call writefile([current_file], tree_file, 'w')
    call ScrollToTop()
endfunction

command! ToggleVimLM call ToggleVimLM()
command! -range -nargs=+ VimLM call VimLM(<f-args>)
nnoremap $mapp :call PasteIntoLastVisualSelection()<CR>
vnoremap $mapp <Cmd>:call PasteIntoLastVisualSelection()<CR>
vnoremap $mapl <Cmd>:call VisualPrompt()<CR>
nnoremap $mapl :call NormalPrompt()<CR>
nnoremap $mapj :call FollowUpPrompt()<CR>
call Monitor()
""").safe_substitute(dict(WATCH_DIR=WATCH_DIR, mapl=mapl, mapj=mapj, mapp=mapp))

async def main():
    parser = argparse.ArgumentParser(description="VimLM - LLM-powered Vim assistant")
    parser.add_argument('--test', action='store_true')
    parser.add_argument("vim_args", nargs=argparse.REMAINDER, help="Vim arguments")
    args = parser.parse_args()
    if args.test:
        return
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vim', delete=False) as f:
        f.write(VIMLMSCRIPT)
        vim_script = f.name
    vim_command = ["vim", "-c", f"source {vim_script}"]
    if args.vim_args:
        vim_command.extend(args.vim_args)
    else:
        vim_command.append('.tmp')
    try:
        monitor_task = asyncio.create_task(monitor_directory())
        vim_process = await asyncio.create_subprocess_exec(*vim_command)
        await vim_process.wait()
    finally:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        os.remove(vim_script)

def run():
    asyncio.run(main())

if __name__ == '__main__':
    run()
