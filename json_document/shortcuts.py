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

from json_document.document import DocumentPersistence
from json_document.storage import FileStorage
from json_document.serializers import JSON


def persistence(document, path, ignore_missing=True, serializer=None):
    """
    Get a DocumentPersistance instance setup for looking at the specified path
    with the specified document instance and the JSON serializer (by default)
    """
    if serializer is None:
        serializer = JSON
    return DocumentPersistence(
        document, FileStorage(path, ignore_missing), serializer)
