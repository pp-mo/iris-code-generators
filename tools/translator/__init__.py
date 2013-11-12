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
Provides the framework to support the encoding of metOcean mapping
translations.

"""

from abc import ABCMeta, abstractmethod
from collections import namedtuple
import warnings

from metocean.fuseki import FusekiServer


# Restrict the tokens exported from this module.
__all__ = ['Mapping', 'CFFieldcodeMapping', 'FieldcodeCFMapping',
           'StashCFMapping']

CFName = namedtuple('CFName', 'standard_name long_name units')


class Mapping(object):
    """
    Abstract base class to support the encoding of specific metOcean
    mapping translations.

    """
    __metaclass__ = ABCMeta

    def __init__(self, mappings):
        temp = []
        # Filter the mappings for the required type of translations.
        for mapping in mappings:
            source = mapping.source
            target = mapping.target
            if source.scheme == self.source_scheme and \
                    target.scheme == self.target_scheme and \
                    self.valid_mapping(mapping):
                temp.append(mapping)
        self.mappings = sorted(temp, key=self._key)
        if len(self) == 0:
            msg = '{!r} contains no mappings.'
            warnings.warn(msg.format(self.__class__.__name__))

    def __iter__(self):
        """Provide an iterator of the encoded metOcean mappings."""
        lines = ['\n%s = {\n' % self.mapping_name]
        payload = [self.encode(mapping) for mapping in self.mappings]
        lines.extend(payload)
        lines.append('    }\n')
        return iter(lines)

    def __len__(self):
        return len(self.mappings)

    @abstractmethod
    def _key(self, mapping):
        """Abstract method to provide the sort key of the mappings order."""

    @abstractmethod
    def encode(self, mapping):
        """
        Abstract method to return the chosen encoded representation
        of a metOcean mapping translation.

        """

    @abstractmethod
    def valid_mapping(self, mapping):
        """
        Abstract method that determines whether the provided mapping
        is a translation for the required source concept to the
        required target concept.

        """

    def _available(self, prop):
        """Determine whether a fully populated property is available."""
        return prop is not None and prop.complete

    def cf_phenomenon_notation(self, concept):
        """
        Given a CF concept from a mapping, the skos notation for
        the associated CF standard name, long name and units of the
        the phenomenon are returned.

        Args:
        * concept:
            A :class:`metocean.Concept` instance for a CF scheme.

        Returns:
            Tuple containing the CF standard name, long name and units.

        """
        units = concept.units.value.notation
        standard_name = concept.standard_name
        if self._available(standard_name):
            standard_name = standard_name.value.notation
        long_name = concept.long_name
        if self._available(long_name):
            long_name = long_name.value.notation
        return CFName(standard_name, long_name, units)

    def is_cf(self, concept, kind='field'):
        """
        Determines whether the provided concept from a mapping
        represents a simple CF concept of the given kind.

        Args:
        * concept:
            A :class:`metocean.Concept` instance.

        Kwags:
        * kind:
            The type of :class:`metocean.Concept`.
            Defaults to 'field'.

        Return:
            Boolean.

        """
        result = False
        if concept.simple:
            result = self._available(concept.type) and \
                concept.type == kind and \
                self._available(concept.units)
        return result

    def is_fieldcode(self, concept):
        """
        Determines whether the provided concept from a mapping
        represents a simple UM concept for a field-code.

        Args:
        * concept:
            A :class:`metocean.Concept` instance.

        Returns:
            Boolean.

        """
        result = False
        if concept.simple:
            result = self._available(concept.lbfc)
        return result

    def is_stash(self, concept):
        """
        Determines whether the provided concept for a mapping
        represents a simple UM concept for a stash-code.

        Args:
        * concept:
            A :class:`metocean.Concept` instance.

        Returns:
            Boolean.

        """
        result = False
        if concept.simple:
            result = self._available(concept.stash)
        return result


class CFFieldcodeMapping(Mapping):
    """
    Represents a container for CF to UM field-code metOcean mapping
    translations.

    Encoding support is provided to generate the Python dictionary source
    code representation of these mappings from CF standard name, long name,
    and units to UM field-code.

    """
    source_scheme = 'cf'
    target_scheme = 'um'
    mapping_name = 'CF_TO_LBFC'

    def _key(self, mapping):
        """Provides the sort key of the mappings order."""
        return self.cf_phenomenon_notation(mapping.source)

    def encode(self, mapping):
        """
        Return a string of the Python source code required to represent an
        entry in a dictionary mapping CF standard name, long name, and units
        to UM field-code.

        Args:
        * mapping:
            A :class:`metocean.Mapping` instance representing a translation
            from CF to UM field-code.

        Returns:
            String.

        """
        msg = '    ' \
            'CFName({standard_name!r}, {long_name!r}, {units!r}): {lbfc},\n'
        cf = self.cf_phenomenon_notation(mapping.source)
        lbfc = mapping.target.lbfc.value.notation
        return msg.format(lbfc=lbfc, **cf._asdict())

    def valid_mapping(self, mapping):
        """
        Determine whether the provided mapping represents a CF to
        UM field-code translation.

        Args:
        * mapping:
            A :class:`metocean.Mapping` instance.

        Return:
            Boolean.

        """
        return self.is_cf(mapping.source) and self.is_fieldcode(mapping.target)


class FieldcodeCFMapping(Mapping):
    """
    Represents a container for UM field-code to CF metOcean mapping
    translations.

    Encoding support is provided to generate the Python dictionary source
    code representation of these mappings from UM field-code to
    CF standard name, long name, and units.

    """
    source_scheme = 'um'
    target_scheme = 'cf'
    mapping_name = 'LBFC_TO_CF'

    def _key(self, mapping):
        """Provides the sort key of the mappings order."""
        return int(mapping.source.lbfc.value.notation)

    def encode(self, mapping):
        """
        Return a string of the Python source code required to represent an
        entry in a dictionary mapping UM field-code to CF standard name,
        long name, and units.

        Args:
        * mapping:
            A :class:`metocean.Mapping` instance representing a translation
            from UM field-code to CF.

        Returns:
            String.

        """
        msg = '    ' \
            '{lbfc}: CFName({standard_name!r}, {long_name!r}, {units!r}),\n'
        lbfc = mapping.source.lbfc.value.notation
        cf = self.cf_phenomenon_notation(mapping.target)
        return msg.format(lbfc=lbfc, **cf._asdict())

    def valid_mapping(self, mapping):
        """
        Determine whether the provided mapping represents a UM field-code
        to CF translation.

        Args:
        * mapping:
            A :class:`metocean.Mapping` instance.

        Returns:
            Boolean.

        """
        return self.is_fieldcode(mapping.source) and self.is_cf(mapping.target)


class StashCFMapping(Mapping):
    """
    Represents a container for UM stash-code to CF metOcean mapping
    translations.

    Encoding support is provided to generate the Python dictionary source
    code representation of these mappings from UM stash-code to CF
    standard name, long name, and units.

    """
    source_scheme = 'um'
    target_scheme = 'cf'
    mapping_name = 'STASH_TO_CF'

    def _key(self, mapping):
        """Provides the sort key of the mappings order."""
        return mapping.source.stash.value.notation

    def encode(self, mapping):
        """
        Return a string of the Python source code required to represent an
        entry in a dictionary mapping UM stash-code to CF standard name,
        long name, and units.

        Args:
        * mapping:
            A :class:`metocean.Mapping` instance representing a translation
            from UM stash-code to CF.

        Returns:
            String.

        """
        msg = '    ' \
            '{stash!r}: CFName({standard_name!r}, {long_name!r}, {units!r}),\n'
        stash = mapping.source.stash.value.notation
        cf = self.cf_phenomenon_notation(mapping.target)
        return msg.format(stash=stash, **cf._asdict())

    def valid_mapping(self, mapping):
        """
        Determine whether the provided mapping represents a UM stash-code to
        CF translation.

        Args:
        * mapping:
            A :class:`metocean.Mapping` instance.

        Returns:
            Boolean.

        """
        return self.is_stash(mapping.source) and self.is_cf(mapping.target)
