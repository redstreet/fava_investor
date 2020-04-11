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

    def pretty_print(self, indent=0):
        # print("{}{} {} {}".format('-'*indent, self.name, self.balance, self.balance_children))
        print("{}{} {:4.2f} {:4.2f}".format('-'*indent, self.name, self.percentage, self.percentage_children))
        for c in self.children:
            c.pretty_print(indent+1)

    @classmethod
    def compute_child_balances(cls, node, total):
        node.balance_children = node.balance + sum(cls.compute_child_balances(c, total) for c in node.children)
        node.percentage = (node.balance / total) * 100
        node.percentage_children = (node.balance_children / total) * 100
        return node.balance_children
