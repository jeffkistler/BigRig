"""
Base class for abstract syntax tree nodes.
"""
from itertools import izip

class NodeType(type):
    """
    A metaclass for nodes that handles field and attribute inheritance.
    """
    def __new__(cls, name, bases, attrs):
        newslots = []
        assert len(bases) == 1, 'multiple inheritance not allowed'
        for attr in 'fields', 'attributes':
            names = attrs.get(attr, ())
            storage = []
            storage.extend(getattr(bases[0], attr, ()))
            storage.extend(names)
            attrs[attr] = tuple(storage)
            newslots.extend(names)
        attrs['__slots__'] = newslots
        attrs.setdefault('abstract', False)
        return type.__new__(cls, name, bases, attrs)


class Node(object):
    """
    Fields are nodes, lists, or simple values.
    Attributes are for metadata such as source position.
    Constructor takes fields as positional arguments and attributes as
    keyword arguments.
    """
    __metaclass__ = NodeType
    fields = ()
    attributes = ('locator',)
    abstract = True
    
    def __init__(self, *fields, **attributes):
        if self.abstract:
            raise ValueError('abstract nodes are not instantiable')
        if fields:
            num_fields = len(self.fields)
            num_args = len(fields)
            if num_args != num_fields:
                classname = self.__class__.__name__
                if not self.fields:
                    raise TypeError('%r takes 0 arguments' %
                                    classname)
                raise TypeError('%r takes 0 or %d argument%s, got %d' % (
                        classname,
                        num_fields, num_fields != 1 and 's' or '',
                        num_fields
                ))
            for name, arg, in izip(self.fields, fields):
                setattr(self, name, arg)
        for attr in self.attributes:
            setattr(self, attr, attributes.pop(attr, None))
        if attributes:
            raise TypeError('unknown attribute %r' % iter(attributes).next())

    def iter_fields(self):
        """
        Yields the name and value of each of this node's fields.
        """
        for name in self.fields:
            yield name, getattr(self, name)

    def iter_children(self):
        """
        Iterate over all subtrees of this node.
        """
        for field, item in self.iter_fields():
            if isinstance(item, list):
                for n in item:
                    if isinstance(n, Node):
                        yield n
            elif isinstance(item, Node):
                yield item

def copy_node_attrs(source, target):
    """
    Copy the attributes from the source node to the target node.
    """
    if hasattr(source, 'attributes') and hasattr(target, 'attributes'):
        for attribute in source.attributes:
            setattr(target, attribute, getattr(source, attribute, None))
    return target
