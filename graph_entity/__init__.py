from graph_runner import GraphRunner

class GraphEntity:
    def __init__(self, **kwargs):
        self.g = kwargs.get('Traversal')
        self.gr = GraphRunner(Traversal=kwargs.get('Traversal'), Entity=self)
        self.entity_id = kwargs.get('Id')
        self.exec_properties = kwargs.get('ExecProperties')
        self.type = kwargs.get('Type', 'vertex')

    def __getattribute__(self, name):
        if name in['property', 'g', 'update_code', 'entity_id', 'gr', 'type', 'exec_properties']:
            return super().__getattribute__(name)
        if name in self.exec_properties:
            return self.gr.exec(Id=self.entity_id, Property=name)

    def update_code(self, **kwargs):
        id = kwargs.get('Id')
        code = kwargs.get('Code')
        property = kwargs.get('Property')
        if self.gr.property_exists(Id=id, Property=property)[1]:
            self.g.V(id).properties(property).drop().iterate()
        self.g.V(id).property(property, code).next()

    def node(self, node):
        self.active_node = node
