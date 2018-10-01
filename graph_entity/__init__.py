from graph_runner import GraphRunner
from gremlin_python.process.traversal import T
import importlib
import uuid
from jinja2 import Environment, BaseLoader

class GraphEntity:
    def __init__(self, **kwargs):
        self.g = kwargs.get('Traversal')
        self.gr = GraphRunner(Traversal=kwargs.get('Traversal'), Entity=self)
        self.id = kwargs.get('Id')
        self.exec_properties = kwargs.get('ExecProperties')

    def full_self(self):
        return type(self).__module__ + "." + self.__class__.__qualname__

    def __getattribute__(self, name):
        __dict__ = super(GraphEntity, self).__getattribute__('__dict__')
        if 'exec_properties' in __dict__ and __dict__['exec_properties'] and \
                name in __dict__['exec_properties']:
            def exec_wrapper(*args, **kwargs):
                kwargs['Id'] = self.id
                kwargs['Property'] = name
                value = self.get_property(name)
                if 'exec_val' in value:
                    return self.gr.exec(**kwargs)
                else:
                    return self.get_property(name)
            return exec_wrapper
        return super(GraphEntity, self).__getattribute__(name)

    def __setattr__(self, name, value):
        if hasattr(self, 'exec_properties') and name in self.exec_properties:
            self.set_property(name, value)
        else:
            self.__dict__[name] = value

    def set_property(self, property, value):
        if self.gr.property_exists(Id=self.id, Property=property)[1]:
            self.g.V(self.id).properties(property).drop().iterate()
        self.g.V(self.id).property(property, value).next()

    # TODO: Add a code sanitizer
    def update_code(self, **kwargs):
        id = kwargs.get('Id', self.id)
        code = kwargs.get('Code')
        property = kwargs.get('Property')
        if self.gr.property_exists(Id=id, Property=property)[1]:
            self.g.V(id).properties(property).drop().iterate()
        self.g.V(id).property(property, code).next()

    def from_node(self, id):
        if self.gr.property_exists(Id=id, Property='gr_type')[1]:
            module_name, class_name = self.get_property('gr_type', id).rsplit(".", 1)
            cls = getattr(importlib.import_module(module_name), class_name)
            return cls(Id=id, Traversal=self.g)

    def add_node(self):
        id = str(uuid.uuid4())
        self.id = id
        return self.g.addV().property(T.id, self.id).property('gr_type', self.full_self())

    def get_property(self, name, id=None):
        if id is None:
            id = self.id
        if self.gr.property_exists(Id=id, Property=name)[1]:
            return self.g.V(id).valueMap(False).toList()[0][name][0]
