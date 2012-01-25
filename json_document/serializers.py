# Copyright (C) 2010, 2011 Linaro Limited
#
# Author: Zygmunt Krynicki <zygmunt.krynicki@linaro.org>
#
# This file is part of json-document
#
# json-document is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version 3
# as published by the Free Software Foundation
#
# json-document is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with json-document.  If not, see <http://www.gnu.org/licenses/>.

"""
json_document.serializers
-------------------------
Document serializer classes
"""

import decimal

import simplejson


JSONDecodeError = simplejson.decoder.JSONDecodeError


class JSON(object):
    """
    JSON class encapsulates loading and saving JSON files using simplejson
    module. It handles 'raw' json without any of the additions specified in the
    :class:`~json_document.document.Document` class.
    """

    # Other classes can set this to True to serialize the real object-oriented
    # version of the object.
    needs_real_object = False

    @classmethod
    def _get_dict_impl(cls, retain_order):
        if retain_order:
            object_pairs_hook = simplejson.OrderedDict
        else:
            object_pairs_hook = None
        return object_pairs_hook

    @classmethod
    def _get_indent_and_separators(cls, human_readable):
        if human_readable:
            indent = ' ' * 2
            separators = (', ', ': ')
        else:
            indent = None
            separators = (',', ':')
        return indent, separators

    @classmethod
    def load(cls, stream, retain_order=True):
        """
        Load a JSON document from the specified stream

        :Discussion:
            The document is read from the stream and parsed as JSON text.

        :Return value:
            The document loaded from the stream. If retain_order is True then
            the resulting objects are composed of ordered dictionaries. This
            mode is slightly slower and consumes more memory but allows one to
            save the document exactly as it was before (apart from whitespace
            differences).

        :Exceptions:
            JSONDecodeError
                When the text does not represent a correct JSON document.
        """
        object_pairs_hook = cls._get_dict_impl(retain_order)
        return simplejson.load(
            stream, parse_float=decimal.Decimal,
            object_pairs_hook=object_pairs_hook)

    @classmethod
    def loads(cls, text, retain_order=True):
        """
        Same as load() but reads data from a string
        """
        object_pairs_hook = cls._get_dict_impl(retain_order)
        return simplejson.loads(
            text, parse_float=decimal.Decimal,
            object_pairs_hook=object_pairs_hook)

    @classmethod
    def dump(cls, stream, doc, human_readable=True, sort_keys=False):
        """
        Dump JSON to a stream-like object

        :Discussion:
            If human_readable is True the serialized stream is meant to be
            read by humans, it will have newlines, proper indentation and
            spaces after commas and colons. This option is enabled by default.

            If sort_keys is True then resulting JSON object will have sorted
            keys in all objects. This is useful for predictable format but is
            not recommended if you want to load-modify-save an existing
            document without altering it's general structure. This option is
            not enabled by default.

        :Return value:
            None
        """
        indent, separators = cls._get_indent_and_separators(human_readable)
        simplejson.dump(
            doc, stream, use_decimal=True, indent=indent,
            separators=separators, sort_keys=sort_keys)

    @classmethod
    def dumps(cls, doc, human_readable=True, sort_keys=False):
        """
        Dump JSON to a string

        :Discussion:
            If human_readable is True the serialized value is meant to be read
            by humans, it will have newlines, proper indentation and spaces
            after commas and colons. This option is enabled by default.

            If sort_keys is True then resulting JSON object will have sorted
            keys in all objects. This is useful for predictable format but is
            not recommended if you want to load-modify-save an existing
            document without altering it's general structure. This option is
            not enabled by default.

        :Return value:
            JSON document as string
        """
        indent, separators = cls._get_indent_and_separators(human_readable)
        return simplejson.dumps(
            doc, use_decimal=True, indent=indent,
            separators=separators, sort_keys=sort_keys)


__all__ = ['JSON', 'JSONDecodeError']
