from graph_entity import GraphEntity

class EventEntity(GraphEntity):
    def __init__(self, *args, **kwargs):
        kwargs['ExecProperties']=['ignore_if', 'action', 'next_node']
        super().__init__(*args, **kwargs)

class PersonEntity(GraphEntity):
    def __init__(self, *args, **kwargs):
        kwargs['ExecProperties']=['is_present']
        super().__init__(*args, **kwargs)
