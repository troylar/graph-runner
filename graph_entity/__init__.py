from graph_runner import GraphRunner
import importlib
import inflection


class GraphEntity:
    def __init__(self, **kwargs):
        self.g = kwargs.get('Traversal')
        self.gr = GraphRunner(Traversal=kwargs.get('Traversal'), Entity=self)
        self.id = kwargs.get('Id')
        self.friendly_id = kwargs.get('FriendlyId')
        self.logger = kwargs.get('Logger')
        self.rule_order = kwargs.get('RuleOrder', {})
        self.exec_properties = kwargs.get('ExecProperties')
        node_properties = kwargs.get('NodeProperties', {})
        for prop in node_properties:
            self.__dict__[prop] = node_properties[prop][0]
        self.properties = kwargs.get('Properties') + ['friendly_id']

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

    def from_node_f(self, friendly_id):
        self.logger.debug('Loading node {}'.format(id))
        v = self.g.V().has('friendly_id', friendly_id)
        if v.has_next():
            return self.from_node(v.id)

    def from_node(self, id):
        self.logger.debug('Loading node {}'.format(id))
        if self.gr.property_exists(Id=id, Property='gr_type')[1]:
            module_name, class_name = self.get_property('gr_type', id).rsplit(".", 1)
            self.logger.debug('Found node, type={}.{}'.format(module_name, class_name))
            cls = getattr(importlib.import_module(module_name), class_name)
            properties = self.g.V(id).valueMap(False).toList()[0]
            self.logger.debug('Properties={}'.format(properties))
            return cls(Id=id,
                       Traversal=self.g,
                       NodeProperties=properties,
                       Logger=self.logger)

    def add_node(self, **kwargs):
        properties = kwargs.get('Properties')
        v = self.g.addV().property('gr_type', self.full_self())
        self.logger.debug('Creating node')
        self.logger.debug('Expected Properties: {}'.format(self.properties))
        self.logger.debug('Actual Properties: {}'.format(properties))
        for prop in self.properties:
            prop_u = inflection.underscore(prop)
            properties_u = {inflection.underscore(k): v for k, v in properties.items()}
            self.logger.debug('Checking {}'.format(prop_u))
            if prop_u in properties_u:
                self.logger.debug('Adding property {}:{}'.format(prop_u, properties_u[prop_u]))
                v.property(prop_u, properties_u[prop_u])
        return v

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
