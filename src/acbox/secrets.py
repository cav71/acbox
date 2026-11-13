import base64
import dataclasses as dc
import hashlib
from pathlib import Path

from cryptography.fernet import Fernet


@dc.dataclass
class Key:
    key: bytes
    digest: str
    path: Path | None = None

    def header(self) -> str:
        return f"> {self.digest} {self.path}"

    def match(self, header: bytes) -> bool | None:
        if not (self.key and header.startswith(b"> ")):
            return None
        return header.startswith(f"> {self.digest}".encode("utf-8"))


def read_key(path: Path) -> Key | None:
    lines: list[str] | None = None
    for line in path.read_text().split("\n"):
        if line == "-----BEGIN OPENSSH PRIVATE KEY-----" and lines is None:
            lines = []
            continue
        if lines is not None:
            if line == "-----END OPENSSH PRIVATE KEY-----":
                result = "".join(line for line in lines if line.strip())
                if len(result) < 32 * 3:
                    raise RuntimeError("short key in path", path)
                with path.open("rb") as fp:
                    key = base64.urlsafe_b64encode(hashlib.sha256(result.encode("utf-8")).digest())
                    digest = hashlib.file_digest(fp, "sha256").hexdigest()
                    return Key(key, digest, path)
            lines.append(line)
    return None


def lookup(path: Path | None = None) -> Key | None:
    path = path or Path("~/.ssh").expanduser().resolve()
    if path.is_file():
        return read_key(path)

    for source in path.glob("*.pub"):
        if not (keypath := source.with_suffix("")).exists():
            continue
        if key := read_key(keypath):
            return key


def encrypt(data: str, key: Key, path: Path | None = None) -> bytes:
    cypher = Fernet(key.key)
    result = key.header().encode("utf-8")
    result += b"\n"
    result += cypher.encrypt(data.encode("utf-8"))
    if path:
        path.write_bytes(result)
    return result


def decrypt(content: bytes, key: Key | None) -> str:
    if not key:
        return content.decode("utf-8")
    header, _, data = content.partition(b"\n")
    if header and (match := key.match(header)) is False:
        raise RuntimeError("no encrypted or matching header")
    if match is None:
        return (b"\n".join([header, data])).decode("uft-8")
    cypher = Fernet(key.key)
    return cypher.decrypt(data).decode("utf-8")


class SecretPath(Path):
    def __init__(self, *args, **kwargs):
        self.key = lookup(kwargs.pop("key", None))
        super().__init__(*args, **kwargs)

    def read_text(self, *args, **kwargs) -> str:
        return decrypt(super().read_bytes(*args, **kwargs), self.key)
