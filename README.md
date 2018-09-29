# Graph Runner
## Overview
`graph-runner` provides a way to add actual Python code to Graph DB nodes, which can be used to create real-time dynamically property values. Rather than only storing fixed values, you have the option to create rich property values that can be calculated on-the-fly with other vertex property values.

## Quick Start
To install `graph-runner`:

    pip install graph-runner

Here's a sample code that assumes you have `node1` and `node2` nodes:

```python
from gremlin_python.process.strategies import *
from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
from graph_entity import GraphEntity
    
if_code = """
if this_entity.ignore_if:
    exec_val = g.V('node2')
else:
    exec_val = "N/A"
 """
graph = Graph()

class Entity(GraphEntity):
     def __init__(self, *args, **kwargs):
		 # you must explicitly define the code properties
         kwargs['ExecProperties']=['ignore_if', 'action', 'next_node']
         super().__init__(*args, **kwargs)

g = graph.traversal().withRemote(DriverRemoteConnection('ws://endpoint:8182/gremlin','g'))

gn = Entity(Traversal=g, Id='node1')

# set the `ignore_if` property to an evaluation of `True`
gn.update_code(Id='node1', Property='ignore_if', Code='exec_val=1==1')
print('should_ignore={}'.format(gn.ignore_if))

# set the `ignore_if` property to an evaluation of `False`
gn.update_code(Id='calvin', Property='ignore_if', Code='exec_val=1>1')
print('should_ignore={}'.format(gn.ignore_if))

# set the `next_node` property to return a traversal
gn.update_code(Id='calvin', Property='next_node', Code='exec_val=g.V(\'chloe\')')
print('next_node={}'.format(gn.next_node))

# set the `next_node` property based on the `ignore_if`
gn.update_code(Id='calvin', Property='next_node', Code=if_code)
print('next_node={}'.format(gn.next_node))
```