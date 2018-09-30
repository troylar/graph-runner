from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from graph_entity import GraphEntity
"""
graph = Graph()

g = graph.traversal().withRemote(DriverRemoteConnection(os.environ.get('GRAPH_DB'),'g'))
print(g.V('calvin').properties('id')[0].toList())

#gn = GraphEntity(Traversal=g)
#node = gn.from_node('94b312e7-a3c4-6eb6-2360-e890f6124cfe')
#print(node)
