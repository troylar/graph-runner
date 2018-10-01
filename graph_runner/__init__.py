from jinja2 import Environment, BaseLoader


class GraphRunner:
    def __init__(self, **kwargs):
        self.g = kwargs.get('Traversal')
        self.entity = kwargs.get('Entity')

    def property_exists(self, **kwargs):
        node_id = kwargs.get('Id')
        property = kwargs.get('Property')
        prop = self.g.V(node_id).properties().toList()
        prop = self.g.V(node_id).properties(property).toList()
        return len(prop), len(prop) > 0

    def exec(self, **kwargs):
        node_id = kwargs.get('Id')
        property = kwargs.get('Property')
        data = kwargs.get('Data')
        count_p, exists = self.property_exists(Id=node_id, Property=property)
        if not exists:
            raise ValueError('{} does not exist in this node'.format(property))
        g = self.g
        this_entity = self.entity
        code = self.g.V(node_id).valueMap(False).toList()[0][property][0]
        if data:
            code_t = Environment(loader=BaseLoader()).from_string(code)
            code_r = code_t.render(data)
        else:
            code_r = code
        # TODO: Add a code sanitizer
        exec(code_r)
        return locals()['exec_val']
