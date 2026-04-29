from typing import Annotated
from urllib.parse import urlparse

from pydantic import AfterValidator, BaseModel, ConfigDict, PlainSerializer


class Interface(BaseModel):
    model_config = ConfigDict(frozen=True)
    scheme: str
    host: str
    port: int


def _parse_interface(value: str) -> Interface:
    parsed = urlparse(value)
    if not parsed.scheme:
        raise ValueError(f"missing scheme in interface URL: {value!r}")
    if not parsed.hostname:
        raise ValueError(f"missing host in interface URL: {value!r}")
    if parsed.port is None:
        raise ValueError(f"missing port in interface URL: {value!r}")
    return Interface(scheme=parsed.scheme, host=parsed.hostname, port=parsed.port)


def _serialize_interface(value: Interface) -> str:
    return f"{value.scheme}://{value.host}:{value.port}"


InterfaceType = Annotated[
    str,
    AfterValidator(_parse_interface),
    PlainSerializer(_serialize_interface, return_type=str),
]
