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
Exceptions
==========

.. autoexception:: DocumentError

.. autoexception:: DocumentSyntaxError

.. autoexception:: DocumentSchemaError

.. autoexception:: OrphanedFragmentError 

"""

import os

import simplejson

from json_schema_validator.errors import ValidationError


class DocumentError(Exception):
    """
    Base class for all Document exceptions.
    """

    def __init__(self, document, msg):
        self.document = document
        self.msg = msg

    def __str__(self):
        return "{0}: {1}".format(
            os.path.normpath(self.document.pathname), self.msg)


class DocumentSyntaxError(DocumentError):
    """
    Syntax error in document
    """

    def __init__(self, document, error):
        if not isinstance(error, simplejson.JSONDecodeError):
            raise TypeError("error must be a JSONDecodeError subclass")
        self.document = document
        self.error = error

    def __str__(self):
        return "{0}: {1}".format(
            os.path.normpath(self.document.pathname), self.error)


class DocumentSchemaError(DocumentError):
    """
    Schema error in document
    """

    def __init__(self, document, error):
        if not isinstance(error, ValidationError):
            raise TypeError("error must be a ValidationError subclass")
        self.document = document
        self.error = error

    def __str__(self):
        return "{0}: {1}".format(
            os.path.normpath(self.document.pathname), self.error)


class OrphanedFragmentError(Exception):
    """
    Exception raised when an orphaned document fragment is being modified.

    A fragment becomes orphaned if a saved reference no longer belongs to any
    document tree. This can happen when one reverts a document fragment to
    default value while still holding references do elements of that fragment.
    """

    def __init__(self, fragment):
        self.fragment = fragment

    def __str__(self):
        return "Attempt to modify orphaned document fragment"

    def __repr__(self):
        return "{0}({1!r})".format(self.__class__.__name__, self.fragment)
