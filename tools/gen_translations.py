# (C) British Crown Copyright 2013, Met Office
#
# This file is part of iris-code-generators.
#
# iris-code-generators is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# iris-code-generators is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with iris-code-generators.  If not, see <http://www.gnu.org/licenses/>.
"""
Processing of metOcean content to provide Iris encodings of
metOcean mapping translations.

"""

from datetime import datetime
import os.path

from metocean.fuseki import FusekiServer

from translator import CFFieldcodeMapping, FieldcodeCFMapping, StashCFMapping


HEADER = """# (C) British Crown Copyright {}, Met Office
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
#
# DO NOT EDIT: AUTO-GENERATED

from collections import namedtuple


CFName = namedtuple('CFName', 'standard_name long_name units')

""".format(datetime.utcnow().year)

FILE_UM_CF = '../outputs/iris/fileformats/um_cf_map.py'


def build_um_cf_map(fuseki, filename):
    # Create the base directory.
    if not os.path.exists(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))

    # Create the file to contain UM/CF translations.
    with open(filename, 'w') as fhandle:
        fhandle.write(HEADER)

        # Encode the relevant UM to CF translations.
        mappings = fuseki.retrieve_mappings('um', 'cf')
        for mapping in FieldcodeCFMapping(mappings):
            fhandle.write(mapping)
        for mapping in StashCFMapping(mappings):
            fhandle.write(mapping)

        # Encode the relevant CF to UM translations.
        mappings = fuseki.retrieve_mappings('cf', 'um')
        for mapping in CFFieldcodeMapping(mappings):
            fhandle.write(mapping)


if __name__ == '__main__':
    with FusekiServer() as fuseki:
        build_um_cf_map(fuseki, FILE_UM_CF)
