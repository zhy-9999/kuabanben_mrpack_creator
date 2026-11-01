#!/usr/bin/env python3
import subprocess
import sys
import zipfile
import shutil
from pathlib import Path
import tomllib
import tomli_w

def set_constant(mods_path = "mods.toml"):
    global MODS
    MODS = Path(__file__).parent / mods_path

set_constant()
TEMP = Path(__file__).parent / ".modfetch_runtime.toml"
DIST_DIR = Path(__file__).parent / "downloads" / "dist"
OVR_SRC = Path("./overrides")
OVR_TMP = Path("./ovrtemp")
CFG = {
    'metadata': {
        'name': 'kuabanben_shengdian', 
        'version': '26.11.01'
    }, 
    'output': {
        'download_dir': './downloads', 
        'format': ['mrpack'], 
        'mrpack_modes': ['reference']
    }
}

def ask_version():
    while True:
        v = input("请输入目标 Minecraft 版本：").strip()
        if v:
            return v
        print("版本不能为空。")


def build_temp_config(version: str):
    with open(MODS, "rb") as modfile:
        mod = tomllib.load(modfile)
    temp = CFG | mod
    temp["minecraft"]["version"] = [version]
    with open(TEMP, "wb") as tempfile:
        tomli_w.dump(temp, tempfile)
    return TEMP


def run_modfetch(config_path: Path):
    before = set(DIST_DIR.glob("*"))
    cmd = [sys.executable, "-m", "modfetch", "build", "-c", str(config_path)]
    print(f"开始调用 ModFetch：{' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        returncode = result.returncode
    except Exception as e:
        returncode = str(e)
    after = set(DIST_DIR.glob("*"))
    new_files = after - before
    if new_files:
        return (result.returncode,tuple(new_files)[0])
    return (-2,returncode)

def override(input_path: Path, output_name: str = "output.mrpack"):
    try:
        output_path = Path(__file__).parent / output_name
        if OVR_TMP.exists():
            shutil.rmtree(OVR_TMP)
        OVR_TMP.mkdir(parents=True,exist_ok=True)

        with zipfile.ZipFile(input_path) as zf:
            zf.extractall(OVR_TMP)

        shutil.copytree(OVR_SRC, OVR_TMP / "overrides", dirs_exist_ok=True)

        output_path.unlink(missing_ok=True)
        tmp_zip = input_path.with_suffix(".zip.tmp")
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in OVR_TMP.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(OVR_TMP))
        tmp_zip.replace(output_path)

    except BaseException as e:
        return (-3,str(e))
    return (0,output_path)

def main(cfg_name: str = "mods.toml", output_name: str = "output.mrpack"):
    try:
        set_constant(mods_path = cfg_name)
        if not MODS.exists():
            return (-1,str(MODS))
        
        version = ask_version()

        TEMP.unlink(missing_ok=True)
        temp_cfg = build_temp_config(version)
        if DIST_DIR.exists():
            shutil.rmtree(DIST_DIR)
        DIST_DIR.mkdir(parents=True,exist_ok=True)
        fetched = run_modfetch(temp_cfg)

        if fetched[0] >= 0:
            success = (fetched[0], override(input_path = fetched[1], output_name = output_name)[1]) # type: ignore
        else:
            success = fetched
        return success
    except BaseException as e:
        return (-4,str(e))
if __name__ == '__main__':
    print(main())