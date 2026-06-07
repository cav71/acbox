from typing import Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class BaseNode(Protocol[T]):
    children: list[T]
