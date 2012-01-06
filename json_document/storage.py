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
json_document.storage
---------------------

Storage classes (for storing serializer output)
"""

import abc
import errno


class IStorage(object):
    """
    Interface for storage classes
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def write(self, data):
        """
        Write data to the storage
        """

    @abc.abstractmethod
    def read(self):
        """
        Read all data from the storage
        """


class FileStorage(IStorage):
    """
    File-based storage class.

    This class is used in conjunction with
    :class:`~json_document.document.DocumentPersistance` to *bind* a Document
    to a file (via a serializer).
    """

    def __init__(self, pathname, ignore_missing=False):
        self._pathname = pathname
        self._ignore_missing = ignore_missing

    @property
    def pathname(self):
        return self._pathname

    def write(self, data):
        """
        Write the specified data to the file

        The data overwrites anything present in the file earlier. If data is an
        Unicode object it is automatically converted to UTF-8.
        """
        if isinstance(data, unicode):
            data = data.encode('UTF-8')
        elif isinstance(data, str):
            pass
        else:
            raise TypeError("data must be an unicode or byte-string")
        with open(self._pathname, 'wt') as stream:
            stream.write(data)

    def read(self):
        """
        Read all data from the file.

        Data is transparently interpreted as UTF-8 encoded Unicode string.  If
        ignore_missing is True and the file does not exist an empty string is
        returned instead.
        """
        try:
            with open(self._pathname, 'rt') as stream:
                return stream.read().decode('UTF-8')
        except IOError as exc:
            if self._ignore_missing is True and exc.errno == errno.ENOENT:
                return ''
            else:
                raise
