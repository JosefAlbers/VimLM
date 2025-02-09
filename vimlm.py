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
from nanollama32 import Chat
import shutil
import time
from itertools import accumulate
import argparse
import tempfile
from pathlib import Path
from string import Template

DEBUG = True
NUM_TOKEN = 2000
SEP_CMD = '!@#$'
VIMLM_DIR = os.path.expanduser("~/vimlm")
WATCH_DIR = os.path.expanduser("~/vimlm/watch_dir")
CFG_FILE = "cfg.json"
LOG_FILE = "log.json"
LTM_FILE = "cache.json"
OUT_FILE = "response.md"
IN_FILES = ["context", "yank", "user", "tree"]
CFG_PATH = os.path.join(VIMLM_DIR, CFG_FILE)
LOG_PATH = os.path.join(VIMLM_DIR, LOG_FILE)
LTM_PATH = os.path.join(VIMLM_DIR, LTM_FILE)
OUT_PATH = os.path.join(WATCH_DIR, OUT_FILE) 

if os.path.exists(WATCH_DIR):
    shutil.rmtree(WATCH_DIR)
os.makedirs(WATCH_DIR)

try:
    with open(CFG_PATH, "r") as f:
        cfg = cfg.load(f)
    DEBUG = config.get("DEBUG", DEBUG)
    NUM_TOKEN = config.get("NUM_TOKEN", NUM_TOKEN)
    SEP_CMD = config.get("SEP_CMD", SEP_CMD)
except:
    with open(CFG_PATH, 'w') as f:
        json.dump(dict(DEBUG=DEBUG, NUM_TOKEN=NUM_TOKEN, SEP_CMD=SEP_CMD), f, indent=2)

def toout(s, key='tovim'):
    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write(s)
    tolog(s, key)

def tolog(log, key='debug'):
    if not DEBUG and key == 'debug':
        return
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r", encoding="utf-8") as log_f:
            logs = json.load(log_f)
    else:
        logs = []
    logs.append(dict(key=key, log=log, timestamp=time.ctime()))
    with open(LOG_PATH, "w", encoding="utf-8") as log_f:
        json.dump(logs, log_f, indent=2)

toout('Loading LLM...')
chat = Chat(variant='uncn_llama_32_3b_it')
toout('LLM is ready')

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
    src_path = os.path.expanduser(src_path)
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
            tolog(f'Skipped {filename} due to {e}', 'retrieve')
        return result
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
            tolog(f'Skipped {filename} due to {e}', 'retrieve')
            continue
    return result

def get_ntok(s):
    return len(chat.tokenizer.encode(s)[0])

def ingest(src):
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
    toout('Ingesting...')
    format_ingest = '{volat}{incoming}\n\n---\n\nPlease provide a succint bullet point summary for above:'
    format_volat = 'Here is a summary of part 1 of **{k}**:\n\n---\n\n{newsum}\n\n---\n\nHere is the next part:\n\n---\n\n'
    dict_doc = retrieve(src, get_len=get_ntok)
    dict_sum = {}
    cache = load_cache()
    for k, v in dict_doc.items():
        v_stamp = v['timestamp']
        if v_stamp == cache.get(k, {}).get('timestamp'):
            dict_sum[k] = cache[k]
            continue
        list_str = v['list_str']
        if len(list_str) == 0:
            continue
        if len(list_str) > 1:
            max_new_sum = int(NUM_TOKEN / len(list_str) / 2)
            volat = f'**{k}**:\n'
            accum = ''
            for s in list_str:
                chat.reset()
                newsum = chat(format_ingest.format(volat=volat, incoming=s.strip()), max_new=max_new_sum, verbose=False, stream=None)[0][:-10].strip()
                accum += newsum + ' ...\n'
                volat = format_volat.format(k=k, newsum=newsum)
        else:
            accum = list_str[0]
        chat.reset()
        toout('')
        chat_summary = chat(format_ingest.format(volat=f'**{k}**:\n', incoming=accum), max_new=int(NUM_TOKEN/4), verbose=False, stream=OUT_PATH)[0][:-10].strip()
        dict_sum[k] = dict(timestamp=v_stamp, summary=chat_summary)
    dump_cache(dict_sum)
    result = ''
    for (k,v) in dict_sum.items():
        result += f'--- Summary of **{k}** ---\n{v["summary"]}\n\n'
    result += '---\n\n'
    return result

def process_command(data, str_template):
    try:
        if len(data['user_command'].strip()) > 0:
            src = data['user_command']
        else:
            src = data['dir']
        return ingest(src) + str_template
    except Exception as e:
        tolog(f'Failed to ingest due to {e}', 'process_command')
        return str_template
   
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
                str_template = '{user}'
            await process_files(data)

async def process_files(data):
    tolog(f'{data=}')
    if 'followup' in data:
        str_template = "{user}"
    else:
        full_path = data['tree']
        data['dir'] = os.path.dirname(full_path)
        data['file'] = os.path.basename(full_path)
        data['ext'] = os.path.splitext(full_path)[1][1:]
        str_template = ''
        if len(data['file']) > 0 and data['file'] != '.tmp':
            str_template += '**{file}**\n'
        if len(data['context']) > 0:
            str_template += '```{ext}\n{context}\n```\n\n'
        if len(data['yank']) > 0:
            if '\n' in data['yank']:
                str_template += "```{ext}\n{yank}\n```\n\n"
            else:
                str_template += "`{yank}` "
        str_template += '{user_prompt}'
        if SEP_CMD in data['user']:
            data['user_prompt'], data['user_command'] = (x.strip() for x in data['user'].split(SEP_CMD))
            str_template = process_command(data, str_template)
        else:
            data['user_prompt'] = data['user']
        chat.reset()
    tolog(f'{str_template=}') # DEBUG
    prompt = str_template.format(**data)
    tolog(prompt, 'tollm')
    toout('')
    response = chat(prompt, max_new=NUM_TOKEN - get_ntok(prompt), verbose=False, stream=OUT_PATH)
    toout(response[0][:-10].strip())
    tolog(response[-1], 'tps')

VIMLMSCRIPT = Template(r"""
let s:watched_dir = expand('$WATCH_DIR')

function! Monitor()
    write
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

function! CheckForUpdates(timer)
    let bufnum = bufnr(s:watched_dir . '/response.md')
    if bufnum == -1
        call timer_stop(s:monitor_timer)
        return
    endif
    silent! checktime
endfunction

function! s:CustomInput(prompt) abort
    let input = ''
    let clean_prompt = a:prompt
    let aborted = v:false
    echohl Question
    echon clean_prompt
    echohl None
    while 1
        let c = getchar()
        if type(c) == v:t_number
            if c == 13 " Enter
                break
            elseif c == 27 " Esc
                let aborted = v:true
                break
            elseif c == 8 || c == 127 " Backspace
                if len(input) > 0
                    let input = input[:-2]
                    echon "\r" . clean_prompt . input . ' '
                    execute "normal! \<BS>"
                endif
            else
                let char = nr2char(c)
                let input .= char
                echon char
            endif
        endif
    endwhile
    let input_length = aborted ? 0 : len(input)
    let clear_length = len(clean_prompt) + input_length
    echon "\r" . repeat(' ', clear_length) . "\r"
    return aborted ? v:null : input
endfunction

function! SaveUserInput()
    let user_input = s:CustomInput('Ask LLM: ')
    if user_input is v:null
        echo "Input aborted"
        return
    endif
    let user_file = s:watched_dir . '/user'
    call writefile([user_input], user_file, 'w')
    let current_file = expand('%:p')
    let tree_file = s:watched_dir . '/tree'
    call writefile([current_file], tree_file, 'w')
endfunction

function! SaveUserInput()
    let user_input = s:CustomInput('Ask LLM: ')
    if user_input is v:null
        echo "Input aborted"
        return
    endif
    let user_file = s:watched_dir . '/user'
    call writefile([user_input], user_file, 'w')
    let current_file = expand('%:p')
    let tree_file = s:watched_dir . '/tree'
    call writefile([current_file], tree_file, 'w')
endfunction

function! FollowUpInput()
    call writefile([], s:watched_dir . '/yank', 'w')
    call writefile([], s:watched_dir . '/context', 'w')
    call writefile([], s:watched_dir . '/followup', 'w')
    call SaveUserInput()
endfunction

vnoremap <C-l> :w! $WATCH_DIR/yank<CR>:w! $WATCH_DIR/context<CR>:call SaveUserInput()<CR>
nnoremap <C-l> V:w! $WATCH_DIR/yank<CR>:w! $WATCH_DIR/context<CR>:call SaveUserInput()<CR>
nnoremap <C-r> :call FollowUpInput()<CR>

call Monitor()
""").safe_substitute(dict(WATCH_DIR=WATCH_DIR))

async def main():
    parser = argparse.ArgumentParser(description="VimLM - LLM-powered Vim assistant")
    parser.add_argument("vim_args", nargs=argparse.REMAINDER, help="Vim arguments")
    args = parser.parse_args()
    with tempfile.NamedTemporaryFile(mode='w', suffix='.vim', delete=False) as f:
        f.write(VIMLMSCRIPT)
        vim_script = f.name
    vim_command = ["vim", "-c", f"source {vim_script}"]
    if args.vim_args:
        vim_command.extend(args.vim_args)
    else:
        vim_command.append('.tmp')
    monitor_task = asyncio.create_task(monitor_directory())
    vim_process = await asyncio.create_subprocess_exec(*vim_command)
    await vim_process.wait()
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass

def run():
    asyncio.run(main())

if __name__ == '__main__':
    run()
