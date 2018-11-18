from graph_runner import GraphRunner
import importlib
import time


class GraphFactory:
    def __init__(self, **kwargs):
        self.g = kwargs.get('Traversal')
        self.logger = kwargs.get('Logger')
        self.entity_module = kwargs.get('EntityModule')

    def create(self, entity_type):
        cls = getattr(importlib.import_module(self.entity_module), entity_type)
        return cls(Traversal=self.g, Logger=self.logger)


class GraphEntity:
    def __init__(self, **kwargs):
        self.g = kwargs.get('Traversal')
        self.id = kwargs.get('Id')
        self.friendly_id = kwargs.get('FriendlyId')
        self.logger = kwargs.get('Logger')
        self.logger.debug('ID={}'.format(self.id))
        self.objects = kwargs.get('Objects', {})
        self.gr = GraphRunner(Traversal=kwargs.get('Traversal'),
                              Entity=self,
                              Logger=self.logger,
                              Objects=self.objects)
        self.rule_order = kwargs.get('RuleOrder', {})
        self.exec_properties = kwargs.get('ExecProperties', [])
        self.exec_logs = {}
        self.events = ['on_start',
                       'on_precheck_wait',
                       'on_before_action',
                       'on_after_action'
                       'on_postcheck_wait',
                       'on_success',
                       'on_failure']
        if 'events' in kwargs:
            self.events = self.events + kwargs.get('events')
        node_properties = kwargs.get('NodeProperties', {})
        for prop in node_properties:
            self.__dict__[prop] = node_properties[prop][0]
        self.properties = kwargs.get('Properties') + ['friendly_id',
                                                      'objects',
                                                      'precode',
                                                      'action']
        self.logger.debug('exec_properties: {}'.format(self.__dict__['exec_properties']))

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
        if self.node_exists_f(friendly_id):
            v = self.g.V().has('friendly_id', friendly_id).next()
            return self.from_node(v.id)

    def from_node(self, id):
        self.logger.debug('Loading node {}'.format(id))
        module_name, class_name = self.get_property('gr_type', id).rsplit(".", 1)
        self.logger.debug('Found node, type={}.{}'.format(module_name, class_name))
        cls = getattr(importlib.import_module(module_name), class_name)
        properties = self.g.V(id).valueMap(False).toList()[0]
        self.logger.debug('ID={}, Properties={}'.format(id, properties))
        entity = cls(Id=id,
                     Traversal=self.g,
                     Objects=self.objects,
                     NodeProperties=properties,
                     Logger=self.logger)
        self.logger.debug('From node={}'.format(entity.id))
        return entity

    def perform_action(self, **kwargs):
        print('running action')
        if 'action' not in self.__dict__:
            return
        data = kwargs.get('Data')
        print('on_action_before')
        self.fire_event('on_action_before')
        if 'precode' in self.__dict__:
            action = '{}\n{}'.format(self.precode, self.action)
        else:
            action = self.action
        val, log = self.gr.exec_code(Code=action,
                                     Entity=self,
                                     Data=data)
        self.with_exec_log('action', val, log)
        self.fire_event('on_action_after')
        return val, log

    def with_exec_log(self, name, val, log):
        if name not in self.exec_logs:
            self.exec_logs[name] = {}
        self.exec_logs[name]['val'] = val
        self.exec_logs[name]['log'] = log
        return self

    def enter_step(self, id):
        node = self.from_node(id)
        node.fire_event('on_start')

    def precheck_wait(self, timeout=30):
        timeout = time.time() + timeout
        if self.event_exists('on_precheck_wait'):
            while True:
                val, log = self.fire_event('on_precheck_wait')
                self.logger.debug('Val = {}'.format(val))
                if str(val) == 'True':
                    return val, log
                if time.time() > timeout:
                    break
                time.sleep(3)
        return True, None

    def event_exists(self, event):
        return 'EVENT_{}'.format(event) in self.__dict__

    def fire_event(self, event):
        if self.event_exists(event):
            val, log = self.gr.exec_code(Code=self.__dict__['EVENT_{}'.format(event)],
                                         Entity=self)
            self.with_exec_log(event, val, log)
            return val, log
        return None, None

    def with_property(self, name, value):
        self.__dict__[name] = value
        return self

    def without_property(self, name):
        del self.__dict__[name]
        return self

    def with_event(self, name, value):
        self.__dict__['EVENT_{}'.format(name)] = value

    def save(self, **kwargs):
        v = self.g.addV().property('gr_type', self.full_self())
        self.logger.debug('Creating node, gr_type={}'.format(self.full_self()))
        self.logger.debug('Expected Properties: {}'.format(self.properties))
        self.logger.debug('Actual Properties: {}'.format(self.properties))
        for prop in self.properties:
            if prop in self.__dict__ and self.__dict__[prop]:
                self.logger.debug('Adding property {}:{}'.format(prop, self.__dict__[prop]))
                v.property(prop, self.__dict__[prop])
        for k in self.__dict__:
            if k.startswith('EVENT_'):
                v.property(k, self.__dict__[k])
        v = v.next()
        self.id = v.id

    def node_exists_f(self, friendly_id):
        by_id_f = len(self.g.V().has('friendly_id', friendly_id).fold().next())
        return by_id_f > 0

    def add_ruled_edge(self, name, to_id, rule='None'):
        name = name.upper()
        print('add ruled edge for ' + name + ' ' + str(self.id))
        print('to_id = {}'.format(to_id))
        if self.node_exists_f(to_id):
            to_id = self.g.V().has('friendly_id', to_id).next().id
        else:
            print('No nodes found with friendly_id "{}"'.format(to_id))
        print('to_id = {}'.format(to_id))
        self.g.V(self.id).addE(name).drop().iterate()
        self.logger.debug('Adding ruled edge {} to {}, rule: {}'.format(to_id, self.id, rule))
        self.g.V(self.id).addE(name).to(self.g.V(to_id)).property('rule', rule).next()
        return self.g.V(self.id)

    def add_edge(self, name, to_id):
        self.g.V(self.id).addE(name).to(self.g.V(self.id)).next()
        self.rules.append(name)
        return self.g.V(self.id)

    def get_ruled_edge(self, name):
        return self.g.V(self.id).outE(name)

    def is_last_node(self):
        return not self.get_all_rules

    def get_all_rules(self):
        print('get all edges for {}'.format(self.id))
        edges = self.g.V(self.id).outE().toList()
        rules = {}
        for edge in edges:
            rule = self.g.V(self.id).outE(edge.label).properties('rule').toList()
            if rule:
                print(edge.label)
                rules[edge.label] = rule[0].value
        return rules

    def wait_for_rule(self, timeout=60):
        done = False
        while not done and not self.is_last_node():
            n = self.next_node_by_rules()
            if n is None:
                return None
            if n:
                return n
            time.sleep(3)

    def next_node_by_rules(self):
        self.logger.debug('Getting node by roles for {}'.format(self.id))
        rules = self.get_all_rules()
        self.logger.debug('Rule Order: {}'.format(self.rule_order))
        self.logger.debug('Rules: {}'.format(rules))
        ret_val = None
        for rule in self.rule_order:
            rule = rule.upper()
            if rule not in rules:
                continue
            rule = rule.upper()
            # if rule exists, but not rule code, then return the node
            if rules[rule] == 'None':
                self.logger.debug('Rule is empty: {}'.format(rule))
                result = True
            else:
                if 'precode' in self.__dict__:
                    code = '{}\n{}'.format(self.precode, rules[rule])
                else:
                    code = rules[rule]
                result, log = self.gr.exec_code(Code=code)
                self.logger.debug('Rule {} result: {}'.format(rule, result))
            if result:
                v = self.g.V(self.id).outE(rule).inV().next()
                self.logger.debug('outv: {}'.format(self.g.V(self.id).outE(rule).inV().next().id))
                node = self.from_node(v.id)
                self.logger.debug('Returning node: {}'.format(node))
                ret_val = node
                break
        return ret_val

    def get_property(self, name, id=None):
        self.logger.debug(self.g.V(id).valueMap(False).toList())
        return self.g.V(id).valueMap(False).toList()[0][name][0]
