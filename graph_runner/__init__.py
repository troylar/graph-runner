from jinja2 import Environment, BaseLoader
import sys
from io import StringIO
import contextlib
import traceback


@contextlib.contextmanager
def stdoutIO(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO()
        sys.stdout = stdout
        yield stdout
        sys.stdout = old


class GraphRunner:
    def __init__(self, **kwargs):
        self.g = kwargs.get('Traversal')
        self.entity = kwargs.get('Entity')
        self.logger = kwargs.get('Logger')
        self.objects = kwargs.get('Objects')

    def property_exists(self, **kwargs):
        node_id = kwargs.get('Id')
        property = kwargs.get('Property')
        prop = self.g.V(node_id).properties().toList()
        prop = self.g.V(node_id).properties(property).toList()
        return len(prop), len(prop) > 0

    def exec_code(self, **kwargs):
        self.logger.debug('exec code')
        data = kwargs.get('Data')
        code = kwargs.get('Code')
        entity = kwargs.get('Entity')
        o = self.objects
        g = self.g
        logger = self.logger
        this_entity = self.entity
        if data:
            code_t = Environment(loader=BaseLoader()).from_string(code)
            code_r = code_t.render(data)
        else:
            code_r = code
        # TODO: Add a code sanitizer
        self.logger.debug('Executing code: {}'.format(code_r))
        with stdoutIO() as s:
            try:
                exec(code_r)
                val = None
                if 'exec_val' in locals():
                    val = locals()['exec_val']
                return val, s.getvalue().strip()
            except Exception as e:
                _traceback = traceback.format_exc()
                self.logger.error(_traceback)
                return None, e

    def exec(self, **kwargs):
        node_id = kwargs.get('Id')
        property = kwargs.get('Property')
        data = kwargs.get('Data')
        count_p, exists = self.property_exists(Id=node_id, Property=property)
        if not exists:
            raise ValueError('{} does not exist in this node'.format(property))
        code = self.g.V(node_id).valueMap(False).toList()[0][property][0]
        return self.exec_code(Code=code, Data=data)
