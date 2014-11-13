"""
This module contains classes for walking abstract syntax trees and transforming
them.
"""
from .node import Node

class NodeVisitor(object):
    """
    Walks the abstract syntax tree, calling the visitor function for every
    subtree found.
    """
    def __init__(self):
        self._visitor_cache = {}

    def get_visitor(self, node):
        node_class = node.__class__
        visitor = self._visitor_cache.get(node_class)
        if visitor is None:
            method = 'visit_%s' % node_class.__name__
            visitor = getattr(self, method, self.generic_visit)
            self._visitor_cache[node_class] = visitor
        return visitor

    def visit(self, node):
        visitor = self.get_visitor(node)
        return visitor(node)

    def generic_visit(self, node):
        if isinstance(node, Node):
            self.visit_node(node)

    def visit_node(self, node):
        for child in node.iter_children():
            self.visit(child)

    def visit_list(self, node):
        for element in node:
            self.visit(element)


class NodeTransformer(NodeVisitor):
    """
    Walks the abstract syntax tree and allows modification of nodes.

    This will walk the AST and use the return value of the visitors to replace
    or remove the old nodes. If the return value of the visitor method is
    ``None``, the node will be removed from its location, otherwise it will
    be replaced with the return value. If the return value is the original
    node, no replacement takes place.
    """
    def generic_visit(self, node):
        if isinstance(node, Node):
            return self.visit_node(node)
        return node

    def visit_node(self, node):
        for field, old_value in node.iter_fields():
            new_value = self.visit(old_value)
            setattr(node, field, new_value)
        return node

    def visit_list(self, node):
        new_values = []
        for element in node:
            new_value = self.visit(element)
            if new_value is None:
                continue
            elif isinstance(new_value, list):
                new_values.extend(new_value)
            else:
                new_values.append(new_value)
        return new_values
