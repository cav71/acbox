from acbox.structures import nodes


class Node(nodes.BaseNode):
    children: list[int]


def test_node():
    node = Node()
    node.children = [1, 2, 3]
    assert node.children == [1, 2, 3]
