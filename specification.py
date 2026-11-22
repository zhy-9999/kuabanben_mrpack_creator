#!/usr/bin/env python3
import re
import subprocess
import sys
import shutil
from pathlib import Path
import datetime
import tomllib
import tomli_w
from idk import *

TEMP_PATH = Path(__file__).parent / "temps" / "specification"
RUNTIME_CONFIG = TEMP_PATH / ".modfetch_runtime.toml"
TEMP_MRPACK = TEMP_PATH / "dist"
CFG = {
    'metadata': {
        'name': 'autobuild_mrpack',
        'version': '00.00.00'
    },
    'output': {
        'download_dir': str(TEMP_PATH),
        'format': ['mrpack'],
        'mrpack_modes': ['reference']
    }
}

def build_temp_config(mc_ver: str, mods: Path, ignores: set = set(),*, name: str = 'autobuild_mrpack') -> Path:
    if not mods.exists():
        raise RuntimeError(f'Cannot find {mods}')
    RUNTIME_CONFIG.unlink(missing_ok=True)
    with open(mods, "rb") as modfile:
        mod = tomllib.load(modfile)
    temp = CFG | mod

    ignore_mods = set(temp["minecraft"]["mods"])
    ignore_mods -= ignores
    temp["minecraft"]["mods"] = list(ignore_mods)
    ignore_resourcepacks = set(temp["minecraft"]["resourcepacks"])
    ignore_resourcepacks -= ignores
    temp["minecraft"]["resourcepacks"] = list(ignore_resourcepacks)
    ignore_shaderpacks = set(temp["minecraft"]["shaderpacks"])
    ignore_shaderpacks -= ignores
    temp["minecraft"]["shaderpacks"] = list(ignore_shaderpacks)

    temp["minecraft"]["version"] = [mc_ver]
    temp["metadata"]["name"] = name
    temp["metadata"]["version"] = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")

    with open(RUNTIME_CONFIG, "wb") as tempfile:
        tomli_w.dump(temp, tempfile)
    return RUNTIME_CONFIG

def run_modfetch(config_path: Path = RUNTIME_CONFIG, times = 1) -> Path:
    if not config_path.exists():
        raise RuntimeError(f'Cannot find {config_path}')
    if TEMP_MRPACK.exists():
        shutil.rmtree(TEMP_MRPACK)
    TEMP_MRPACK.mkdir(parents=True,exist_ok=True)

    cmd = [sys.executable, "-m", "modfetch", "build", "-c", str(config_path)]
    log('INFO', f'第 {times} 次尝试调用 ModFetch')
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    new_files = set(TEMP_MRPACK.glob("*"))
    if new_files:
        if result.stdout:
            print(result.stdout.strip())
        else:
            log('SUCCESS', f'mrpack 生成成功: {' '.join(str(p) for p in new_files)}')
            log('SUCCESS', 'ModFetch 任务完成!')
            log('SUCCESS', f'完成! 输出 { len(new_files) } 个文件')
        if result.returncode != 0:
            log('WARNING', f'值得注意的是，ModFetch 返回码为 { result.returncode }')
        if result.stderr:
            for i in result.stderr.strip().split('\n'):
                if i:
                    log('WARNING', i)
        return tuple(new_files)[0]
    else:
        log('FAILURE', 'mrpack 生成失败: 未找到新文件')
        log('FAILURE', f'ModFetch 返回码为 { result.returncode }')
        if result.stderr:
            for i in result.stderr.strip().split('\n'):
                if i :
                    log('INFO', i)
        else:
            log('FAILURE', 'ModFetch 未给出任何错误报告')
        raise RuntimeError(result.stderr)

def retry_fetch(mods: Path, mc_ver: str,*,count: int = 3) -> Path:
    ignores = set()
    fetched = None
    for i in range(count):
        try:
            temp_cfg = build_temp_config(mc_ver,mods,ignores)
            fetched = run_modfetch(temp_cfg,i+1)
        except RuntimeError as e:
            errs = str(e)
            matched = re.findall(r"未找到项目: \s*(\S+)\s*", errs) + re.findall(r"项目\s*(\S+)\s*不兼容", errs)
            ignores.update(matched)
            log('INFO', f"自动忽略错误模组: {' '.join(ignores)}")
        if not fetched is None:
            if ignores:
                log('WARNING',"以下是失败模组列表，请手动检查: ")
                for i in ignores:
                    log('INFO',i)
            return fetched
    log('FAILURE', f'已达到最大重试次数 {count}')
    raise RuntimeError(f'Reach max retry times {count}')

def ask_version(mc_ver: str | None = None) -> str:
    if not (mc_ver is None):
        return str(mc_ver)
    while True:
        v = input(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | INPUT    | 请输入目标 Minecraft 版本: ').strip()
        if v:
            return str(v)
        log('INFO', f'版本 {v} 无效，请重新输入。')

def main(generalized_path: Path | None = None, mc_ver: str | None = None, forcheck_path: Path | None = None, name: str = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")):

    generalized = choose_file(generalized_path, Path(__file__).parent / "generalized", wait = True)
    mods = generalized / "mods.toml"
    overrides = generalized / "overrides"

    TEMP_PATH.mkdir(parents=True, exist_ok=True)
    output_mrpack = retry_fetch(mods,ask_version(mc_ver))

    if forcheck_path is None:
        output_folder = Path(__file__).parent / "forcheck" / name
    else:
        output_folder = forcheck_path

    unzip(output_mrpack, output_folder)
    shutil.copytree(overrides, output_folder / "overrides", dirs_exist_ok=True)
    log('SUCCESS', f'输出文件夹: {output_folder}')
    return output_folder

def final(forcheck_path: Path | None = None, output_path: Path | None = None, name: str = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")):

    checked = choose_file(forcheck_path, Path(__file__).parent / "forcheck", wait = True)

    if output_path is None:
        output_mrpack = Path(__file__).parent / "output" / f"{name}.mrpack"
    else:
        output_mrpack = output_path

    makezip(checked, output_mrpack)
    log('SUCCESS', f'输出文件: {output_mrpack}')
    return output_mrpack

if __name__ == '__main__':
    easy_run(main,final)