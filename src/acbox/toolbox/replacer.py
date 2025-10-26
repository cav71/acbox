import shutil
import tempfile
from pathlib import Path


def process(txt: str, defines: dict[str, str]) -> str:
    result = []
    for line in txt.split("\n"):
        newline = line
        for key, value in defines.items():
            newline = newline.replace(f"@{key}@", value)
        result.append(newline)
    return "\n".join(result)


def fix(path: Path, defines: dict[str, str], inplace: bool) -> str:
    with tempfile.NamedTemporaryFile(mode="w+") as fp:
        shutil.copymode(path, fp.name)
        fp.write(process(path.read_text(), defines))
        fp.flush()
        fp.seek(0)
        if inplace:
            shutil.copy(fp.name, path)
        return fp.read()
