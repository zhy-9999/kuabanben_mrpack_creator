#!/usr/bin/env python3
import json
import re
import requests
import random
import tomli_w
import datetime
from pathlib import Path
import time
_last_start = 0.0

_cache = dict()
def set_constant(index_path = "modrinth.index.json", mods_path = "mods.toml"):
    global INDEX,MODS
    INDEX = Path(__file__).parent / index_path
    MODS = Path(__file__).parent / mods_path

set_constant()
def log(level,data):
    print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {level} | {data}')
def fetch_slug(project_id):
    if project_id is None:
        return None
    if project_id in _cache:
        return _cache[project_id]

    global _last_start
    wait = _last_start - time.monotonic() + 0.2
    if wait > 0:
        time.sleep(wait)
    _last_start = time.monotonic()
    response = requests.get(
        f"https://api.modrinth.com/v3/project/{project_id}",
        headers = {"User-Agent": f"{ 10**10 + random.randint(0,10**10-1) }@qq.com"},
        timeout = 60,
    ) # Modrinth 要求带联系方式的 UA
    data = json.loads(response.text)
    _cache[project_id] = data["slug"]
    return data["slug"]

def project_id_from_url(url):
    m = re.search(r"http(s)://cdn.modrinth.com/data/[^/]+/version", url)
    if m is None:
        return None
    return m.group().split('/')[-2]

def convert(index):
    errs = 0
    deps = index["dependencies"]
    # "dependencies": {
    #     "minecraft": "26.1.2",
    #     "fabric-loader": "0.19.5"
    # }
    loaders = tuple(k for k in deps if k != "minecraft")
    if len(loaders) == 1:
        loader = loaders[0].replace("-loader", "").lower()
        log('INFO   ',f'加载器：{loader}')
    else:
        return (-1,f"应有且仅有一个加载器: {loaders}")

    buckets = {"mods/": set(), "resourcepacks/": set(), "shaderpacks/": set()}
# "files": [
#     {
#         "path": "mods/appleskin.jar",
#         "downloads": [
#             "https://cdn.modrinth.com/data/EsAfCjCV/versions/zLlqqiTA/appleskin-fabric-mc26.1.2-3.0.10.jar"
#         ],
    log('INFO   ',f'计划获取 {len(index["files"])} 个模组')
    for entry in index["files"]:
        path = entry["path"]
        prefix = [p for p in buckets if path.startswith(p)]
        if len(prefix) != 1:
            log('ERROR  ',f"未知前缀: {path}")
            errs += 1
        else:
            slug = {fetch_slug(project_id) for project_id in {project_id_from_url(url) for url in entry["downloads"]}}
            slug.discard(None)

            if len(slug) == 1:
                log('INFO   ',f"成功获取 {path} 的 slug: {tuple(slug)[0]}")
                buckets[prefix[0]] |= slug
            else:
                log('WARN   ',f"{path} 应有且仅有一个 slug: {tuple(slug)}")
                errs += 1
    if errs:
        log('WARN   ',f"共 {len(index["files"])} 个模组，失败 {errs} 个，成功 {len(index["files"])-errs} 个")
    else:
        log('SUCCESS',f"共 {len(index["files"])} 个模组，全部获取成功")
    return (errs,{
        "minecraft": {
            "mod_loader": loader,
            "mods": list(buckets["mods/"]),
            "resourcepacks": list(buckets["resourcepacks/"]),
            "shaderpacks": list(buckets["shaderpacks/"]),
        }
    })
def main(newINDEX = "modrinth.index.json", newMODS = "mods.toml"):
    try:
        set_constant(index_path = newINDEX, mods_path = newMODS)
        with open(INDEX, encoding="utf-8") as indexfile:
            index = json.load(indexfile)
        print('开始从 Modrinth API 获取模组 slug')
        cfg = convert(index)
        if cfg[0] >= 0:
            with open(MODS, "wb") as modfile:
                tomli_w.dump(cfg[1], modfile) # type: ignore
            if cfg[0] == 0:
                return (0,MODS)
            return (1,f'{cfg[0]} 个文件错误')
        else:
            return (2,str(cfg[1]))
    except BaseException as e:
        return (3,str(e))
if __name__ == '__main__':
    print(main())