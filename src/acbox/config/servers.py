from pathlib import Path
from sys import argv
from typing import Any, Literal

from ruamel.yaml import YAML

from acbox.config.types import InterfaceType  # noqa: I001
from pydantic import BaseModel, ConfigDict, PrivateAttr


class ConfigError(Exception):
    pass


class Server(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda x: {
            "server_type": "type",
        }.get(x, x),
        frozen=True,
    )
    name: str
    server_type: Literal["sqlite"] | Literal["imap"]


class Sqlite(Server):
    url: str | None = None


class Imap(Server):
    username: str
    password: str
    interface: InterfaceType


class Config(BaseModel):
    servers: dict[str, Server]
    _raw: Any = PrivateAttr(default=None)
    _yaml: Any = PrivateAttr(default=None)


def server_from_dict(data: dict[str, Any]) -> Imap | Sqlite:
    mapper = {klass.__name__.lower(): klass for klass in {Imap, Sqlite}}
    return mapper[data["type"]](**data)


def load(path: Path | str, kind: str | None = None) -> Config:
    yaml = YAML(typ="rt")
    data = yaml.load(Path(path))
    seen = set()
    servers: dict[str, Server] = {}
    for sdata in data["servers"]:
        if (name := sdata["name"]) in seen:
            raise ConfigError(f"duplicate server {name=}")
        seen.add(name)
        servers[name] = server_from_dict(sdata)
    config = Config(servers=servers)
    config._raw = data
    config._yaml = yaml
    return config


def save(config: Config, path: Path | str) -> None:
    if config._raw is not None:
        # Update the raw ruamel structure in-place to preserve comments
        raw_by_name = {sdata["name"]: sdata for sdata in config._raw["servers"]}
        for server in config.servers.values():
            dumped = server.model_dump(by_alias=True)
            if server.name in raw_by_name:
                sdata = raw_by_name[server.name]
                for key, value in dumped.items():
                    sdata[key] = value
            else:
                config._raw["servers"].append(dumped)
        # Remove entries that no longer exist
        config._raw["servers"] = [sdata for sdata in config._raw["servers"] if sdata["name"] in config.servers]
        yaml = config._yaml
        yaml.dump(config._raw, Path(path))
    else:
        yaml = YAML(typ="rt")
        servers = [server.model_dump(by_alias=True) for server in config.servers.values()]
        yaml.dump({"servers": servers}, Path(path))


if __name__ == "__main__":
    for name, server in load(Path(argv[1])).servers.items():
        print(f"{name=}, [{server.__class__.__name__}]")  # noqa: T201
        print(f"  {server.server_type=}")  # noqa: T201
