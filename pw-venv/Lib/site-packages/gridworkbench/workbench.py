# GridWorkbench: A Python structure for power system data
#
# Adam Birchfield, Texas A&M University
# 
# Log:
# 9/29/2021 Initial version, rearranged from prior draft so that most object fields
#   are only listed in one place, the PW_Fields table. Now to add a field you just
#   need to add it in that list.
# 11/2/2021 Renamed this file to core and added fuel type object
# 1/22/22 Split out all device types
# 8/18/22 Engine rename and throwing exceptions for non-existent items
#
from typing import OrderedDict
from .utils.exceptions import GridObjDNE

class GridWorkbench:

    # PowerWorld IO Functions
    from .io.default_pw_instructions import make_default_pw_instructions
    from .io.pwb_analysis import setup_pwb_fields
    from .io.pwb_analysis import open_pwb
    from .io.pwb_analysis import close_pwb
    from .io.pwb_analysis import pwb_read_all
    from .io.pwb_analysis import pwb_write_all
    from .io.pwb_analysis import pwb_write_data
    from .io.pwaux import import_aux
    from .io.pwaux import export_aux

    # Other IO Functions
    from .io.pwb_dyn import pwb_read_dyn
    from .io.json_tool import json_save
    from .io.json_tool import json_open
    from .io.grid_engine import setup_engine

    def __init__(self, fname=None):
        self.clear()
        self.setup_pwb_fields()
        self.make_default_pw_instructions()
        if isinstance(fname, str) and len(fname) >= 4 and \
                fname[-4:].lower() == '.pwb':
            self.open_pwb(fname)
            self.pwb_read_all(hush=True)
        elif isinstance(fname, str) and len(fname) >= 4 and \
                fname[-4:].lower() == '.aux':
            self.import_aux(fname, hush=True)
        elif isinstance(fname, str) and len(fname) >= 5 and \
                fname[-5:].lower() == '.json':
            self.json_open(fname)
        elif fname is not None:
            raise NameError(f'Do not understand {fname} to open')

    def clear(self):
        self._region_map = OrderedDict()
        self._area_map = OrderedDict()
        self._sub_map = OrderedDict()
        self._bus_map = OrderedDict()
        self._node_map = OrderedDict()
        self.esa = None

    def region(self, number):
        if number in self._region_map:
            return self._region_map[number]
        else:
            raise GridObjDNE(f"Region {number} does not exist")

    def area(self, number):
        if number in self._area_map:
            return self._area_map[number]
        else:
            raise GridObjDNE(f"Area {number} does not exist")

    def sub(self, number):
        if number in self._sub_map:
            return self._sub_map[number]
        else:
            raise GridObjDNE(f"Substation {number} does not exist")

    def bus(self, number):
        if number in self._bus_map:
            return self._bus_map[number]
        else:
            raise GridObjDNE(f"Bus {number} does not exist")

    def node(self, number):
        if number in self._node_map:
            return self._node_map[number]
        else:
            raise GridObjDNE(f"Node {number} does not exist")

    def gen(self, node_number, id):
        return self.node(node_number).gen(id)

    def load(self, node_number, id):
        return self.node(node_number).load(id)

    def shunt(self, node_number, id):
        return self.node(node_number).shunt(id)
            
    def branch(self, from_node_number, to_node_number, id):
        return self.node(from_node_number).branch_from(to_node_number, id)
    
    @property
    def regions(self):
        return tuple(region for region in self._region_map.values())

    @property
    def areas(self):
        return tuple(area for area in self._area_map.values())

    @property
    def subs(self):
        return tuple(sub for sub in self._sub_map.values())

    @property
    def buses(self):
        return tuple(bus for bus in self._bus_map.values())

    @property
    def nodes(self):
        return tuple(bus for bus in self._node_map.values())

    @property
    def gens(self):
        return tuple(gen for node in self.nodes for gen in node.gens)

    @property
    def branches(self):
        return tuple(branch for node in self.nodes for branch in node.branches_from)

    @property
    def loads(self):
        return tuple(load for node in self.nodes for load in node.loads)

    @property
    def shunts(self):
        return tuple(shunt for node in self.nodes for shunt in node.shunts)
