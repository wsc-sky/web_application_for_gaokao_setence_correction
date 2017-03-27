#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Author: Tim Henderson
#Email: tim.tadh@gmail.com
#For licensing see the LICENSE file in the top level directory.

import collections


class Node(object):
    """
    A simple node object that can be used to construct trees to be used with
    :py:func:`zss.distance`.

    Example: ::

        Node("f")
            .addkid(Node("a")
                .addkid(Node("h"))
                .addkid(Node("c")
                    .addkid(Node("l"))))
            .addkid(Node("e"))
    """
    mycnt = 0
    def __init__(self, label, children=None, level = 0, theta=1):
        self.id = Node.mycnt
        self.label = label
        self.children = children or list()
        self.father = None
        self.level = level
        self.theta = theta
        Node.mycnt += 1

    def myleaves(self):
        leaves = []
        for child in self.children:
            if isinstance(child, Node):
                if len(child.children)>0:
                    leaves.extend(child.myleaves())
                else:
                    leaves.append(child)
        return leaves
    def size(self):
        myq1 = [self]
        nodes1 = []
        while myq1:
            for c in myq1[0].children:
                nodes1.append(c)
                myq1.append(c)
            del myq1[0]
        return len(nodes1)
    @staticmethod
    def get_children(node):
        """
        Default value of ``get_children`` argument of :py:func:`zss.distance`.

        :returns: ``self.children``.
        """
        return node.children

    @staticmethod
    def get_label(node):
        """
        Default value of ``get_label`` argument of :py:func:`zss.distance`.

        :returns: ``self.label``.
        """
        return node.label

    def addkid(self, node, before=False):
        """
        Add the given node as a child of this node.
        """
        if before:  self.children.insert(0, node)
        else:   self.children.append(node)
        return self
    def deletechildren(self, node):
        """
        Add the given node as a child of this node.
        """
        self.children = list()
        return self

    def get(self, label):
        """:returns: Child with the given label."""
        if self.label == label: return self
        for c in self.children:
            if label in c: return c.get(label)

    def iter(self):
        """Iterate over this node and its children in a preorder traversal."""
        queue = collections.deque()
        queue.append(self)
        while len(queue) > 0:
            n = queue.popleft()
            for c in n.children: queue.append(c)
            yield n

    def __contains__(self, b):
        if isinstance(b, str) and self.label == b: return 1
        elif not isinstance(b, str) and self.label == b.label: return 1
        elif (isinstance(b, str) and self.label != b) or self.label != b.label:
            return sum(b in c for c in self.children)
        raise TypeError, "Object %s is not of type str or Node" % repr(b)

    def __eq__(self, b):
        if b is None: return False
        if not isinstance(b, Node):
            raise TypeError, "Must compare against type Node"
        return self.label == b.label

    def __ne__(self, b):
        return not self.__eq__(b)

    def __repr__(self):
        return super(Node, self).__repr__()[:-1] + " %s>" % self.label

    def __str__(self):
        s = "%d:%s" % (len(self.children), self.label)
        s = '\n'.join([s]+[str(c) for c in self.children])
        return s
