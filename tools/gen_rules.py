# (C) British Crown Copyright 2013, Met Office
#
# This file is part of Iris-code-generators.
#
# Iris-code-generators is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# Iris-code-generators is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Iris-code-generators.  If not, see <http://www.gnu.org/licenses/>.

import os
import os.path
import re


HEADER = \
'''# (C) British Crown Copyright 2013, Met Office
#
# This file is part of Iris.
#
# Iris is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Iris is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Iris.  If not, see <http://www.gnu.org/licenses/>.

# DO NOT EDIT DIRECTLY
# Auto-generated from SciTools/iris-code-generators:tools/gen_rules.py

import warnings

import numpy as np

from iris.aux_factory import HybridHeightFactory
from iris.coords import AuxCoord, CellMethod, DimCoord
from iris.fileformats.mosig_cf_map import MOSIG_STASH_TO_CF
from iris.fileformats.rules import Factory, Reference, ReferenceTarget
from iris.fileformats.um_cf_map import LBFC_TO_CF, STASH_TO_CF
from iris.unit import Unit
import iris.fileformats.pp
import iris.unit


def convert(cube, {field_var_name}):
    cm = cube
    factories = []
    references = []
'''


FOOTER = '''
    return factories, references
'''

def _write_rule(module_file, conditions, actions):
    module_file.write('\n')
    if len(conditions) == 1:
        module_file.write('    if {}:\n'.format(conditions[0]))
    else:
        module_file.write('    if \\\n')
        for condition in conditions[:-1]:
            module_file.write('            ({}) and \\\n'.format(condition))
        module_file.write('            ({}):\n'.format(conditions[-1]))
    for action in actions:
        if action.startswith('CoordAndDims(DimCoord'):
            match = re.match(r'CoordAndDims\((.*), ([0-1]+)\)$', action)
            if match:
                action = 'cube.add_dim_coord({})'.format(action[13:-1])
            else:
                action = 'cube.add_aux_coord({})'.format(action[13:-1])
        elif action.startswith('CoordAndDims(AuxCoord('):
            action = 'cube.add_aux_coord({})'.format(action[13:-1])
        elif action.startswith('CellMethod('):
            action = 'cube.add_cell_method({})'.format(action)
        elif action.startswith('CMCustomAttribute('):
            match = re.match(
                r'CMCustomAttribute\(([\'"0-9a-zA-Z_]+), ?(.+)\)$', action)
            name = match.group(1)
            value = match.group(2)
            action = 'cube.attributes[{}] = {}'.format(name, value)
        elif action.startswith('CMAttribute('):
            match = re.match(r'CMAttribute\(([\'"0-9a-zA-Z_]+), (.+)\)$',
                             action)
            name = eval(match.group(1))
            value = match.group(2)
            # Temporary code to deal with invalid standard names from
            # the translation table(s).
            if name == 'standard_name':
                action = 'cube.rename({})'.format(value)
            # Temporary code to deal with invalid units in the
            # translation table(s).
            elif name == 'units':
                action = '''units = {}
        try:
            setattr(cube, 'units', units)
        except ValueError:
            msg = 'Ignoring PP invalid units {{!r}}'.format(units)
            warnings.warn(msg)
            cube.attributes['invalid_units'] = units
            cube.units = iris.unit._UNKNOWN_UNIT_STRING'''.format(value)
            else:
                action = 'cube.{} = {}'.format(name, value)
        elif action.startswith('Factory('):
            action = 'factories.append({})'.format(action)
        elif action.startswith('ReferenceTarget('):
            action = 'references.append({})'.format(action)
        else:
            raise RuntimeError('unrecognised action: {}'.format(action))
        module_file.write('        {}\n'.format(action))


def _absolute_path(path):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), path))


def write_rules_module(field_var_name, rules_paths, module_path):
    # Define state constants
    IN_CONDITION = 1
    IN_ACTION = 2

    module_path = _absolute_path(module_path)
    module_dir = os.path.dirname(module_path)
    if not os.path.isdir(module_dir):
        os.makedirs(module_dir)
    with open(module_path, 'w') as module_file:
        module_file.write(HEADER.format(field_var_name=field_var_name))
        for rules_path in rules_paths:
            rules_path = _absolute_path(rules_path)
            print 'rules_path:', rules_path
            with open(rules_path, 'r') as rules_file:
                conditions = []
                actions = []
                state = None
                for line_no, line in enumerate(rules_file):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line == "IF":
                        if conditions and actions:
                            _write_rule(module_file, conditions, actions)
                        conditions = []
                        actions = []
                        state = IN_CONDITION
                    elif line == "THEN":
                        state = IN_ACTION
                    elif state == IN_CONDITION:
                        conditions.append(line)
                    elif state == IN_ACTION:
                        actions.append(line)
                    else:
                        msg = 'Rule file not read correctly at line no. {}\n{}'
                        raise RuntimeError(msg.format(line_no, line))
                if conditions and actions:
                    _write_rule(module_file, conditions, actions)
        module_file.write(FOOTER)


if __name__ == '__main__':
    write_rules_module('f', ['../load_rules/pp_rules.txt',
                             '../load_rules/pp_cross_reference_rules.txt'],
                       '../outputs/iris/fileformats/pp_rules.py')
    write_rules_module('grib',
                       ['../load_rules/grib_rules.txt',
                        '../load_rules/grib_cross_reference_rules.txt'],
                       '../outputs/iris/fileformats/grib/load_rules.py')
