from gremlin_python import statics
from gremlin_python.structure.graph import Graph
from gremlin_python.process.graph_traversal import __
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from graph_entity import GraphEntity
from entities import EventEntity, PersonEntity

if_code = """
if this_entity.ignore_if:
    exec_val = g.V('chloe')
else:
    exec_val = "N/A"
"""
graph = Graph()

g = graph.traversal().withRemote(DriverRemoteConnection('ws://endpoint:8182/gremlin','g'))

# We're going to add an entity to the graph
first_event = EventEntity(Traversal=g)
print('Adding node')

# add_node() returns a traversal
first_event.add_node().next()

# we're going to update the ignore_if with a simple boolean piece of code
# exec_val is always required as the return value
first_event.update_code(Property='ignore_if', Code='exec_val=1==1')

# print the id and the node type
print('Node id = {}'.format(first_event.id))
print('Node type: {}'.format(first_event.full_self()))

# this is where it gets cool . . . the ignore_if property was dynamically added to the python object
# and when you access the property, it executes the code
print('ignore_if property: {}'.format(first_event.ignore_if))

# let's start with the base GraphEntity object and go get what we just created
ge = GraphEntity(Traversal=g)
print('Getting node')
node = ge.from_node(first_event.id)
print('Node id = {}'.format(node.id))
print('Node type: {}'.format(node.full_self()))
print('ignore_if property: {}'.format(node.ignore_if))

# let's create a person entity
pe = PersonEntity(Traversal=g)
print('Adding person')
pe.add_node().next()
pe.update_code(Property='is_present', Code='exec_val=True')

# let's create a second event
second_event = EventEntity(Traversal=g)
print('Adding another event')
second_event.add_node().next()

# let's add some logic to a property
next_node_code = """
from graph_entity import GraphEntity
ge = GraphEntity(Traversal=g)
if ge.from_node('{}').is_present:
    exec_val = g.V('{}')
else:
    exec_val = "N/A"
""".format(pe.id, second_event.id)

# because is_present is true, we get our next node
first_event.update_code(Property='next_node', Code=next_node_code)
print(first_event.next_node)

# change is_present to false, and the next_node is N/A
pe.update_code(Property='is_present', Code='exec_val=False')
print(first_event.next_node)
