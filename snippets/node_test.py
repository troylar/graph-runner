from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from graph_entity import GraphEntity
if_code = """
if this_entity.ignore_if:
    exec_val = g.V('chloe')
else:
    exec_val = "N/A"
"""
graph = Graph()

class EventEntity(GraphEntity):
    def __init__(self, *args, **kwargs):
        kwargs['ExecProperties']=['ignore_if', 'action', 'next_node']
        super().__init__(*args, **kwargs)

g = graph.traversal().withRemote(DriverRemoteConnection('ws://pollexy.cpnsd60aij0a.us-east-1.neptune.amazonaws.com:8182/gremlin','g'))

gn = EventEntity(Traversal=g, Id='calvin')
gn.update_code(Id='calvin', Property='ignore_if', Code='exec_val=1==1')
print('should_ignore={}'.format(gn.ignore_if))
gn.update_code(Id='calvin', Property='ignore_if', Code='exec_val=1>1')
print('should_ignore={}'.format(gn.ignore_if))
gn.update_code(Id='calvin', Property='next_node', Code='exec_val=g.V(\'chloe\')')
print('next_node={}'.format(gn.next_node))
gn.update_code(Id='calvin', Property='next_node', Code=if_code)
print('next_node={}'.format(gn.next_node))

