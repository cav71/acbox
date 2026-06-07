import collections
from typing import TypeVar

from .nodes import BaseNode

U = TypeVar("U")


def tree2dot(root: BaseNode, attribute: str | None = None) -> str:
    from jinja2 import Template

    node2ids: dict[str, tuple[int, BaseNode]] = {}
    q = collections.deque([root])
    while q:
        cur = q.popleft()
        key = hex(id(cur))
        if key not in node2ids:
            node2ids[hex(id(cur))] = (len(node2ids), cur)
        for c in reversed(cur.children):
            if c:
                q.appendleft(c)

    return Template("""
digraph {
    // definitions
    {% for k, v in node2ids.items() %}
        {% if attribute %}
        "{{v[0]}}" [ label="{{getattr(v[1], attribute)}}" ];
        {% else %}"{{v[0]}}"
        {% endif %}
    {%- endfor %}

    // connections
    {% for k, v in node2ids.items() %}
        {%- for c in v[1].children %}
           {% if node2ids[hex(id(c))] %}
           {{node2ids[k][0]}} -> {{node2ids[hex(id(c))][0]}}
           {% endif %}
        {%- endfor %}
    {%- endfor %}

}
""").render(node2ids=node2ids, hex=hex, id=id, getattr=getattr, attribute=attribute)
