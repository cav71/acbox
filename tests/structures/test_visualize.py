from __future__ import annotations

import dataclasses as dc

from acbox.structures import nodes, visualize


@dc.dataclass
class Node(nodes.BaseNode):
    value: str
    children: list[Node] = dc.field(default_factory=list)


def test_render():
    root = Node("A")
    root.children = [Node("B")]
    root.children[0].children = [Node("C")]
    root.children[0].children[0].children = [Node("D"), Node("E")]

    assert (
        """
digraph {
    // definitions
        "0"
        "1"
        "2"
        "3"
        "4"
    // connections
           0 -> 1
           1 -> 2
           2 -> 3
           2 -> 4
}
""".strip()
        == "\n".join(x for x in visualize.tree2dot(root).split("\n") if x.strip())
    )

    assert (
        """
digraph {
    // definitions
        "0" [ label="A" ];
        "1" [ label="B" ];
        "2" [ label="C" ];
        "3" [ label="D" ];
        "4" [ label="E" ];
    // connections
           0 -> 1
           1 -> 2
           2 -> 3
           2 -> 4
}
""".strip()
        == "\n".join(x for x in visualize.tree2dot(root, attribute="value").split("\n") if x.strip())
    )
