def tiptap_to_text(content) -> str:
    """Konversi Tiptap JSON ke plain text."""
    if not content:
        return ""

    def parse_node(node):
        if not node:
            return ""
        node_type = node.get("type", "")
        children = node.get("content", [])

        if node_type == "text":
            return node.get("text", "")
        elif node_type == "paragraph":
            return "".join(parse_node(c) for c in children) + "\n"
        elif node_type == "heading":
            return "".join(parse_node(c) for c in children) + "\n"
        elif node_type in ("bulletList", "orderedList"):
            return "".join(parse_node(c) for c in children)
        elif node_type == "listItem":
            return "• " + "".join(parse_node(c) for c in children)
        elif node_type == "hardBreak":
            return "\n"
        elif node_type == "doc":
            return "".join(parse_node(c) for c in children)
        else:
            return "".join(parse_node(c) for c in children)

    return parse_node(content).strip()