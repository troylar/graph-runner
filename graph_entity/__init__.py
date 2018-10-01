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
        self.rule_order = kwargs.get('RuleOrder', {})
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

    def add_ruled_edge(self, name, to_id, rule):
        self.g.V(self.id).addE(name).drop().iterate()
        self.g.V(self.id).addE(name).to(self.g.V(self.id)).property('rule', rule).next()
        return self.g.V(self.id)

    def add_edge(self, name, to_id):
        self.g.V(self.id).addE(name).to(self.g.V(self.id)).next()
        self.rules.append(name)
        return self.g.V(self.id)

    def get_ruled_edge(self, name):
        return self.g.V(self.id).outE(name)

    def get_all_rules(self):
        edges = self.g.V(self.id).outE().toList()
        rules = {}
        for edge in edges:
            rule = self.g.V(self.id).outE(edge.label).properties('rule').toList()
            if rule:
                rules[edge.label] = rule[0].value
        return rules

    def next_node_by_rules(self):
        rules = self.get_all_rules()
        for rule in self.rule_order:
            rule = rule.upper()
            print(rules[rule])
            result = self.gr.exec_code(Code=rules[rule])
            if result:
                return self.g.V(self.id).outE(rule)


    def get_property(self, name, id=None):
        if id is None:
            id = self.id
        if self.gr.property_exists(Id=id, Property=name)[1]:
            return self.g.V(id).valueMap(False).toList()[0][name][0]
