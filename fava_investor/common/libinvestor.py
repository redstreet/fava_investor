#!/usr/bin/env python3

class Node(object):
    """Generic tree implementation. Consider replacing this with anytree"""
    def __init__(self, name):
        self.name = name
        self.children = []
        self.parent = None

    def add_child(self, obj):
        self.children.append(obj)
        obj.parent = self

    def find_child(self, name):
        for child in self.children:
            if child.name == name:
                return child
        return None

    def pre_order(self, level=0):
        yield self, level
        for c in self.children:
            yield from c.pre_order(level+1)
