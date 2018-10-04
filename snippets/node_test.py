from gremlin_python.structure.graph import Graph
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from graph_entity import GraphEntity
from entities import EventEntity, PersonEntity
import os

graph = Graph()

g = graph.traversal().withRemote(DriverRemoteConnection(os.environ.get('CONN_STR'), 'g'))

# We're going to add an entity to the graph
first_event = EventEntity(Traversal=g)
print('Adding node')

# add_node() returns a traversal, so we have to next()
first_event.add_node().next()

# Now we're going to add a dynamic property called 'ignore_if' with a simple boolean piece of code
# NOTE: exec_val is always required as the return value
first_event.ignore_if = 'exec_val=1==1'

# print the id
print('Node id = {}'.format(first_event.id))

# print the node type, which maps to the EventEntity class and is saved as a property in the graph
print('Node type: {}'.format(first_event.full_self()))

# this is where it gets cool . . . the ignore_if property method was dynamically added to the python object
# and when you access the property, it executes the code and returns the value
print('ignore_if property: {}'.format(first_event.ignore_if()))

# now let's create a GraphEntity object and from scratch, load the node we just created
ge = GraphEntity(Traversal=g)
print('Getting node')
node = ge.from_node(first_event.id)
print('Node id = {}'.format(node.id))
print('Node type: {}'.format(node.full_self()))
print('ignore_if property: {}'.format(node.ignore_if()))

# let's create a person entity with an 'is_present' property
pe = PersonEntity(Traversal=g)
print('Adding person')
pe.add_node().next()
pe.is_present = 'True'

# let's create a second event
second_event = EventEntity(Traversal=g)
print('Adding another event')
second_event.add_node().next()

# let's add some more complex logic to a property
# this property is saying that if the person is present, move to the next event
next_node_code = """
from graph_entity import GraphEntity
ge = GraphEntity(Traversal=g)

if ge.from_node('{}').is_present()=='True':
    exec_val = g.V('{}')
else:
    exec_val = "N/A"
""".format(pe.id, second_event.id)

# because is_present is true, we get our next node
first_event.next_node = next_node_code
print(first_event.next_node())

# change is_present to false, and the next_node is N/A
pe.is_present = 'False'
print(first_event.next_node())

# we can also use jinja2 templating, which allows us to pass in dynamic values at run-time
# in this case, it's the same code, but we we're alloing the ids to be passed in at run-time
next_node_template = """
from graph_entity import GraphEntity
ge = GraphEntity(Traversal=g)

if ge.from_node('{{ person_node_id }}').is_present()=='True':
    exec_val = g.V('{{ next_node_id }}')
else:
    exec_val = "N/A"
"""

# run the same code, but pass ids at run-time
first_event.next_node = next_node_template
pe.is_present = 'True'
print(first_event.next_node(Data={'person_node_id': pe.id, 'next_node_id': second_event.id}))

pe.is_present = 'False'
print(first_event.next_node(Data={'person_node_id': pe.id, 'next_node_id': second_event.id}))

first_event.add_ruled_edge('IS_NOT_LOADED', second_event.id, 'exec_val = 1==1')
first_event.add_ruled_edge('IS_NOT_READY', second_event.id, 'exec_val = False')
first_event.add_ruled_edge('IS_READY', second_event.id, 'exec_val = True')
#print(first_event.get_ruled_edge('HAS_NEXT'))
print('All rules:\n{}'.format(first_event.get_all_rules()))
print('Next node: {}'.format(first_event.next_node_by_rules()))
first_event.add_ruled_edge('IS_NOT_LOADED', second_event.id, 'exec_val = False')
print('Next node: {}'.format(first_event.next_node_by_rules()))
