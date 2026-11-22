#!/usr/bin/env python3
import json
import re
import shutil
import requests
import random
import tomli_w
import datetime
from pathlib import Path
from idk import *
import time
_last_start = 0.0

_cache = dict()
TEMP_PATH = Path(__file__).parent / 'temps' / "generalize"
TEMP_INDEX_PATH = TEMP_PATH / "modrinth.index.json"
TEMP_MODS_PATH = TEMP_PATH / "mods.toml"

def fetch_slug(project_id: str | None) -> str | None:
    if project_id is None:
        return None
    try:
        return _cache[project_id]
    except KeyError:
        pass

    global _last_start
    wait = _last_start - time.monotonic() + 0.2
    try:
        if wait > 0:
            time.sleep(wait)
        _last_start = time.monotonic()
        response = requests.get(
            f"https://api.modrinth.com/v3/project/{project_id}",
            headers = {"User-Agent": f"{ 10**10 + random.randint(0,10**10-1) }@qq.com"},
            timeout = 60,
        ) # Modrinth 要求带联系方式的 UA
        data = json.loads(response.text)
        _cache[project_id] = str( data["slug"] )
    except Exception:
        pass
    try:
        return _cache[project_id]
    except KeyError:
        pass

    return None

def project_id_from_url(url: str | None) -> str | None:
    if url is None:
        return None
    m = re.search(r"http(s)://cdn.modrinth.com/data/[^/]+/version", url)
    if m is None:
        return None
    try:
        return m.group().split('/')[-2]
    except Exception:
        pass
    return None

def convert(index)-> dict:
    deps = index["dependencies"]
    # "dependencies": {
    #     "minecraft": "26.1.2",
    #     "fabric-loader": "0.19.5"
    # }
    loaders = {k for k in deps if k != "minecraft"}
    if len(loaders) == 1:
        loader = tuple(loaders)[0].replace("-loader", "").lower()
        log('INFO',f'加载器: {loader}')
    else:
        raise RuntimeError(f"应有且仅有一个加载器: {loaders}")

    buckets = {"mods/": set(), "resourcepacks/": set(), "shaderpacks/": set()}
# "files": [
#     {
#         "path": "mods/appleskin.jar",
#         "downloads": [
#             "https://cdn.modrinth.com/data/EsAfCjCV/versions/zLlqqiTA/appleskin-fabric-mc26.1.2-3.0.10.jar"
#         ],
    errs = set()
    log('INFO',f'计划获取 {len(index["files"])} 个模组')
    for entry in index["files"]:
        try:
            path = entry["path"]
        except Exception as e:
            log('ERROR',f"处理未知模组时未知错误: {e}")
            errs.add(f'unknown mod {datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")}')
        try:
            prefix = [p for p in buckets if path.startswith(p)]
            if len(prefix) != 1:
                log('ERROR',f"未知前缀: {path}")
                errs.add(path)
            else:
                slug = {fetch_slug(project_id) for project_id in {project_id_from_url(url) for url in entry["downloads"]}}
                slug.discard(None)

                if len(slug) == 1:
                    log('INFO',f"成功获取 {path} 的 slug: {tuple(slug)[0]}")
                    buckets[prefix[0]] |= slug
                else:
                    log('ERROR',f"{path} 应有且仅有一个 slug: {tuple(slug)}")
                    errs.add(path)
        except Exception as e:
            log('ERROR',f"处理 {path} 时未知错误: {e}")
            errs.add(path)

    if errs:
        log('WARNING',f"共 {len(index["files"])} 个模组，失败 { len(errs) } 个，成功 { len(index["files"]) - len(errs) } 个")
        log('WARNING',"以下是失败模组列表，请手动检查: ")
        for i in errs:
            log('INFO',i)
    else:
        log('SUCCESS',f"共 {len(index["files"])} 个模组，全部获取成功")
    return {
        "minecraft": {
            "mod_loader": loader,
            "mods": list(buckets["mods/"]),
            "resourcepacks": list(buckets["resourcepacks/"]),
            "shaderpacks": list(buckets["shaderpacks/"]),
        }
    }

def main(input_path: Path | None = None, generalized_path: Path | None = None, name: str = datetime.datetime.now().strftime("%Y-%m-%d_%H.%M.%S")) -> Path:
    mrpack = choose_file(input_path, Path(__file__).parent / 'inputs')

    unzip(mrpack,TEMP_PATH)
    with open(TEMP_INDEX_PATH, encoding="utf-8") as indexfile:
        index = json.load(indexfile)

    log('INFO', '开始从 Modrinth API 获取模组 slug')
    cfg = convert(index)

    TEMP_MODS_PATH.unlink(missing_ok=True)
    with open(TEMP_MODS_PATH, "wb") as modfile:
        tomli_w.dump(cfg, modfile)
    TEMP_INDEX_PATH.unlink(missing_ok=True)

    if generalized_path is None:
        output_folder = Path(__file__).parent / "generalized" / name
    else:
        output_folder = generalized_path

    if output_folder.exists():
        shutil.rmtree(output_folder)
    output_folder.mkdir(parents=True,exist_ok=True)
    shutil.copytree(TEMP_PATH, output_folder, dirs_exist_ok=True)
    log('SUCCESS', f'输出文件夹: {output_folder}')
    return output_folder

if __name__ == '__main__':
    a = None
    try:
        a = main()
    except Exception as e:
        print(str(e))
    except KeyboardInterrupt:
        print()
        print()
    print(a)