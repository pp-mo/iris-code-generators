# (C) British Crown Copyright 2013 - 2014, Met Office
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

from datetime import datetime
import os
import re

import gen_helpers

HEADER = \
    '''
# Auto-generated from SciTools/iris-code-generators:tools/gen_rules.py

import warnings

import numpy as np

from iris.aux_factory import HybridHeightFactory, HybridPressureFactory
from iris.coords import AuxCoord, CellMethod, DimCoord
from iris.fileformats.rules import Factory, Reference, ReferenceTarget
from iris.fileformats.um_cf_map import LBFC_TO_CF, STASH_TO_CF
from iris.unit import Unit
import iris.fileformats.pp
import iris.unit


def convert({field_var_name}):
    factories = []
    references = []
    standard_name = None
    long_name = None
    units = None
    attributes = {{}}
    cell_methods = []
    dim_coords_and_dims = []
    aux_coords_and_dims = []
'''


FOOTER = '''
    return (factories, references, standard_name, long_name, units, attributes,
            cell_methods, dim_coords_and_dims, aux_coords_and_dims)
'''


def _write_rule(module_file, conditions, actions, save_style=False):
    module_file.write('\n')
    if len(conditions) == 1:
        module_file.write('    if {}:\n'.format(conditions[0]))
    else:
        module_file.write('    if \\\n')
        for condition in conditions[:-1]:
            module_file.write('            ({}) and \\\n'.format(condition))
        module_file.write('            ({}):\n'.format(conditions[-1]))
    for action in actions:
        if save_style:
            # save rules actions are plain code
            pass
        else:
            if action.startswith('CoordAndDims(DimCoord'):
                match = re.match(r'CoordAndDims\((.*), ([0-1]+)\)$', action)
                if match:
                    fmt = 'dim_coords_and_dims.append(({}))'
                else:
                    fmt = 'aux_coords_and_dims.append(({}, None))'
                action = fmt.format(action[13:-1])
            elif action.startswith('CoordAndDims(AuxCoord('):
                action = action[13:-1]
                # Rudimentary check to see if a dimension was supplied to
                # the CoordAndDims constructor.
                if action[-1] == ')':
                    # Original was: CoordAndDims(AuxCoord(...))
                    fmt = 'aux_coords_and_dims.append(({}, None))'
                else:
                    # Original was: CoordAndDims(AuxCoord(...), <expr>)
                    fmt = 'aux_coords_and_dims.append(({}))'
                action = fmt.format(action)
            elif action.startswith('CellMethod('):
                if 'cm.coord(' in action:
                    action = action[:-1].replace('cm.coord(', 'coords=')
                action = 'cell_methods.append({})'.format(action)
            elif action.startswith('CMCustomAttribute('):
                match = re.match(
                    r'CMCustomAttribute\(([\'"0-9a-zA-Z_]+), ?(.+)\)$', action)
                name = match.group(1)
                value = match.group(2)
                action = 'attributes[{}] = {}'.format(name, value)
            elif action.startswith('CMAttribute('):
                match = re.match(r'CMAttribute\(([\'"0-9a-zA-Z_]+), (.+)\)$',
                                 action)
                name = eval(match.group(1))
                assert name in ('standard_name', 'long_name', 'units')
                value = match.group(2)
                action = '{} = {}'.format(name, value)
            elif action.startswith('Factory('):
                action = 'factories.append({})'.format(action)
            elif action.startswith('ReferenceTarget('):
                action = 'references.append({})'.format(action)
            else:
                raise RuntimeError('unrecognised action: {}'.format(action))
        module_file.write('        {}\n'.format(action))


def write_rules_module(field_var_name, rules_paths, module_path, save_style=False):
    # Define state constants
    IN_CONDITION = 1
    IN_ACTION = 2
    gen_helpers.prep_module_file(module_path)
    with open(module_path, 'a') as module_file:
        module_file.write(HEADER.format(field_var_name=field_var_name))
        for rules_path in rules_paths:
            rules_path = gen_helpers.absolute_path(rules_path)
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
                            _write_rule(module_file, conditions, actions,
                                        save_style=save_style)
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
                    _write_rule(module_file, conditions, actions,
                                save_style=save_style)
        module_file.write(FOOTER)


if __name__ == '__main__':
    write_rules_module('f', ['../load_rules/pp_rules.txt',
                             '../load_rules/pp_cross_reference_rules.txt'],
                       '../outputs/iris/fileformats/pp_rules.py')
    write_rules_module('grib',
                       ['../load_rules/grib_rules.txt',
                        '../load_rules/grib_cross_reference_rules.txt'],
                       '../outputs/iris/fileformats/grib/load_rules.py')
