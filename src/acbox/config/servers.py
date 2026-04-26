from pathlib import Path
from sys import argv
from typing import Any, Literal

from ruamel.yaml import YAML

from pydantic import BaseModel, ConfigDict


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
    url: str | None = None
    username: str
    password: str
    interface: str  # Interface #Annotated[str, AfterValidator(Interface)]


class Config(BaseModel):
    servers: dict[str, Server]


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
    return Config(servers=servers)


if __name__ == "__main__":
    for name, server in load(Path(argv[1])).servers.items():
        print(f"{name=}, [{server.__class__.__name__}]")  # noqa: T201
        print(f"  {server.server_type=}")  # noqa: T201
