from pathlib import Path
from typing import Callable
import shutil
import zipfile
import datetime

ZIP_TEMP = Path(__file__).parent / 'temps' / "zip"
def log(level: str,data) -> None:
    print(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | {level.upper()+' '*(8-len(level))} | {data}')

def unzip(zip: Path, path: Path | None = None) -> Path:
    if ZIP_TEMP.exists():
        shutil.rmtree(ZIP_TEMP)
    ZIP_TEMP.mkdir(parents=True,exist_ok=True)

    with zipfile.ZipFile(zip) as zf:
        zf.extractall(ZIP_TEMP)

    if path is None:
        return ZIP_TEMP

    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True,exist_ok=True)
    shutil.copytree(ZIP_TEMP, path, dirs_exist_ok=True)

    return path

def makezip(path: Path, zip: Path | None = None) -> Path:
    if ZIP_TEMP.exists():
        shutil.rmtree(ZIP_TEMP)
    ZIP_TEMP.mkdir(parents=True,exist_ok=True)

    tmp_zip = ZIP_TEMP / "zip.tmp"
    with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in path.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(path))
    if zip is None:
        return tmp_zip

    zip.parent.mkdir(parents=True,exist_ok=True)
    zip.unlink(missing_ok=True)
    tmp_zip.replace(zip)
    return zip

def choose_file(path: Path | None = None, default: Path | None = None) -> Path:
    if (path is None):
        if default is None:
            raise OSError
        default.mkdir(parents=True, exist_ok=True)
        files = tuple(sorted(default.iterdir()))
        for i in range(len(files)):
            log('INFO',f'{i}: {files[i]}')
        file = files[int(input(f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | INPUT    | 请输入所选文件序号: '))]
    else:
        file = path
    if not file.exists():
        raise OSError
    log('INFO', f'{'选择' if path is None else '输入'}{'文件夹' if file.is_dir() else '文件'}: {file}')
    return file

def easy_run(*funcs: Callable, first_input = None, default = None):
    a = first_input
    for func in funcs:
        log('INFO',f'开始运行 {func.__name__}')
        try:
            a = func(a)
        except KeyboardInterrupt:
            print()
            a = default
    return a

if __name__ == '__main__':
    raise RuntimeError