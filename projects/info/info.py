# /// script
# dependencies = [
# "rich",
# "click",
# "cloup",
# "acbox",
# ]
# ///
# TODO replace with: import acbox.toolbox.info
import dataclasses as dc
import platform
import shutil
import sys
from pathlib import Path

from acbox.toolbox import info as acbox_info
from acbox.ureporting import Record, S, check, load_external_checks, print_report

# def get_installed_using_pip(workdir: Path) -> dict[str, str]:
#     output = runc(["pipenv", "run", "pip", "list", "--format", "json"], overrides={
#         "PIP_NO_CACHE_DIR": "yes",
#         "PIPENV_VENV_IN_PROJECT": "1",
#     }, cwd=workdir)
#
#     result = {}
#     for item in json.loads(output.strip()):
#         key = item["name"].strip().lower()
#         result[stripkey(key)] = item["version"]
#     return result
#
#
# def get_installed_using_pipenv(workdir: Path) -> dict[str, str]:
#     output = runc(["pipenv", "requirements"], cwd=workdir).strip()
#     packages = {}
#     for line in output.split("\n"):
#         # eg. lines like '-i url'
#         if "-i " in line:
#             continue
#
#         values = line
#         if ";" in line:
#             values = line.partition(";")[0]
#         values = values.split("==")  # in requirements only ==
#
#         # eg.
#         if line.count("@") == 2:
#             values = line.split("@")[::2]
#         elif match := (re.compile(r"(https|http|file)://(?P<url>[^ ;]+)").search(line)):
#             # https://some.url/path/csv2ofx-some-weird--0.30.1-py2.py3-none-any.whl ; python_version >= '3.9'
#             items = match.group("url").rpartition("/")[2].split("-")[:-3]
#             values = "-".join(items[:-1]), items[-1]
#
#         name, version = values
#         packages[stripkey(name)] = version
#
#     return packages
# def check_installed_python_packages() -> Record:
#     found_in_pip = get_installed_using_pip(WORKDIR)
#     found_in_pipenv = get_installed_using_pipenv(WORKDIR)
#     skip = {
#         "pip": ("25.0.1", "N/A"),
#         "instructor": ("1.7.9", "2b602c53679c5d6bce2048828df92a68359627dd"),
#     }
#     delta = diffdict(found_in_pip, found_in_pipenv, skip)
#     if delta:
#         msg = "\n".join(f"- {', '.join(d)}" for d in delta)
#         return Record("difference between packages installed with pipenv and detected by pip", S.FAILED, msg)
#     else:
#         return Record("no difference between packages installed with pipenv and detected by pip", S.OK)
#


@check
def check_missing_so_files(root: Path):
    @dc.dataclass
    class LSO:
        missing: list[str] = dc.field(default_factory=list)
        deps: dict[str, Path] = dc.field(default_factory=dict)

    if (system := platform.uname().system) != "Linux":
        # value expected for 'system' is 'Linux' but found 'Darwin'
        return Record(S.NOSTATUS, "so-files", "unsupported", f"value expected for 'system' is 'Linux' but found '{system}'")

    if not (ldd := shutil.which("ldd")):  # noqa: F841
        return Record(S.FAILED, "so-files", "missing", "cannot find 'ldd' executable")

    return Record(S.NOSTATUS, "so-files", "INCOMPLETE", "MUST FINISH")


#     result = {}
#     for path in root.rglob("*"):
#         if not (path.name.endswith(".so") or os.access(path, os.X_OK)):
#             continue
#         if (txt := runc(["ldd", path], quiet=True)) is None:
#             continue
#         result[path] = lso = LSO()
#
#         for line in runc(["ldd", path]).split("\n"):
#             if "=>" not in line:
#                 continue
#             name, target = [p.strip() for p in line.split("=>")]
#             if target == "not found":
#                 target = None
#                 lso.missing.append(name)
#             else:
#                 target = target.partition(" ")[0]
#                 lso.deps[name] = Path(target)
#
#     if any(lso.missing for lso in result.values()):
#         lines = []
#         for path, lso in result.items():
#             if not lso.missing:
#                 continue
#             lines.append(f"{path} missing: {', '.join(lso.missing)}")
#         return Record("missing .so files", "\n".join(lines))
#
#     # TODO check for libpython rpaths!
#     return Record(".so files ok", S.OK)


def main() -> int:
    report = []
    report.extend(acbox_info.check_sys("sys"))
    report.extend(acbox_info.check_plaform("platform"))
    report.extend(acbox_info.check_environ("environ.env"))
    report.extend(acbox_info.check_executables("environ.exe"))
    report.extend(acbox_info.check_envfile("envfile"))
    report.extend(check_missing_so_files(Path.cwd()))
    report.extend(load_external_checks(sys.argv[1:]))
    return print_report(report)


if __name__ == "__main__":
    sys.exit(main())
