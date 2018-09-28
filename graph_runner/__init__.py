class GraphRunner:
    def __init__(self, **kwargs):
        self.g = kwargs.get('Traversal')
        self.entity = kwargs.get('Entity')

    def property_exists(self, **kwargs):
        node_id = kwargs.get('Id')
        property = kwargs.get('Property')
        prop = self.g.V(node_id).properties(property).toList()
        return len(prop), len(prop) > 0


    def exec(self, **kwargs):
        node_id = kwargs.get('Id')
        property = kwargs.get('Property')
        count_p, exists = self.property_exists(Id=node_id, Property=property)
        if not exists:
            raise ValueError('{} does not exist in this node'.format(property))
        g = self.g
        this_entity = self.entity
        code = self.g.V(node_id).valueMap(False).toList()[0][property][0]
        exec(code)
        return locals()['exec_val']
