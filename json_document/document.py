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

import copy
import decimal
import os

import simplejson

from json_schema_validator.errors import SchemaError, ValidationError
from json_schema_validator.schema  import Schema
from json_schema_validator.validator import Validator

from json_document.errors import DocumentError, DocumentSyntaxError, DocumentSchemaError, OrphanedFragmentError


class DefaultValue(object):
    """
    Special default value marker.

    This value is used by DocumentFragment to represent default values, that
    is, values that should be looked up in the DocumentFragment schema's
    default value.
    """


DefaultValue = DefaultValue()


class DocumentFragment(object):
    """
    Class representing a fragment of a document.

    Fragment may point to a single item (such as None, bool, int, float,
    string) or to a container (such as list or dict). You can access the value
    pointed to with the 'value' property.
    """

    def __init__(self, document, parent, value, item=None, schema=None):
        self._document = document
        self._parent = parent
        self._value = value
        self._item = item
        self._schema = schema
        self._fragment_cache = {}

    @property
    def schema(self):
        if self._schema is not None:
            return Schema(self._schema)

    @property
    def is_default(self):
        """
        Check if this fragment points to a default value.

        Note: A fragment that points to a value equal to the value of the
        default is NOT considered default. Only fragments that were not
        assigned a value previously are considered default.
        """
        return self._value is DefaultValue

    def revert_to_default(self):
        """
        Revert the value that this fragment points to to the default value.
        """
        self._ensure_not_orphaned()
        if not self.default_value_exists:
            raise TypeError("Default value does not exist")
        if self._value is not DefaultValue:
            # Orphan all existing fragments in our fragment cache
            for fragment in self._fragment_cache.itervalues():
                fragment._orphan()
            # Purge the fragment cache from this fragment
            self._fragment_cache = {}
            # Set the new value
            self._set_value(DefaultValue)
            # Mark the document as dirty
            self._document._is_dirty = True

    @property
    def default_value(self):
        """
        Get the default value.

        Note: This method will raise SchemaError if the default is not defined
        in the schema
        """
        return self.schema.default

    @property
    def default_value_exists(self):
        try:
            self.default_value
            return True
        except SchemaError:
            return False

    def validate(self):
        """
        Validate the fragment value against the schema
        """
        if self._schema is not None:
            Validator.validate(self.schema, self.value)

    @property
    def value(self):
        """
        Get the value of this fragment.

        This method transparently gets default values from the schema.
        """
        if self.is_default:
            return self.default_value
        else:
            return self._value

    @value.setter
    def value(self, new_value):
        """
        Set the value of this fragment.

        Setting a value instantiates default values in this or any parent
        fragment. That is, if the value of this fragment or any of the parent
        fragments is default (fragment.is_default returns true), then the
        default value is copied and used as the effective value instead.

        When fragment.is_default is True setting any value (including the value
        of fragment.default_value) will overwrite the value so that
        fragment.is_default will return False. If you want to "set the default
        value" use fragment.revert_to_default() explicitly.

        Setting a value that is different from the current value marks the
        whole document as dirty.
        """
        self._ensure_not_orphaned()
        if self._value != new_value:
            # Ensure there are no defaults around
            self._ensure_not_default()
            # Orphan all existing fragments in our fragment cache
            for fragment in self._fragment_cache.itervalues():
                fragment._orphan()
            # Purge the fragment cache from this fragment
            self._fragment_cache = {}
            # Set the new value
            self._set_value(new_value)
            # Mark the document as dirty
            self._document._is_dirty = True

    def _set_value(self, new_value):
        """
        Low-level set value.

        Stuff it assumes is done elsewhere:
            * Does NOT check for default values
            * Does NOT check for orphans
            * Does NOT invalidate fragment cache
        
        Stuff that is done here:
            * Updates parent object container value (if has parent)
            * Updates _value
        """
        # Set the new value
        if self._parent is not None and self._item is not None:
            # We should be our parent's cache
            assert self is self._parent._fragment_cache[self._item]
            # Update our parent's container value
            if new_value is DefaultValue:
                del self._parent._value[self._item]
            else:
                self._parent._value[self._item] = new_value
        # Set the new value directly
        self._value = new_value

    def _ensure_not_default(self):
        """
        This method transparently "un-defaults" this fragment and any parent
        fragments. The DefaultValue marker will be replaced by a deep copy of
        the default value from the schema.
        """
        if self._value is DefaultValue:
            if self._parent is not None:
                self._parent._ensure_not_default()
            self._set_value(copy.deepcopy(self.schema.default))

    def _ensure_not_orphaned(self):
        """
        Ensure that a this document fragment is not orphaned.
        """
        if self.is_orphaned:
            raise OrphanedFragmentError(self)

    def _orphan(self):
        """
        Orphan this document fragment by disassociating it from the parent and
        the document and copying the value so that it is fully independent from
        the parent.

        Note: This does method _not_ remove the fragment from the parent's
        fragment cache.
        """
        self._parent = None
        self._document = None
        self._value = copy.deepcopy(self._value)

    @property
    def is_orphaned(self):
        """
        Check if a fragment is orphaned.

        Orphaned fragments can occur in this scenario:

        x    >>> doc = Document()
        x    >>> doc["foo"] = "value"
        x    >>> foo = doc["foo"]
        x    >>> doc.value = {}
        x    >>> foo.is_orphaned
        x    True

        That is, when the parent fragment value is overwritten.
        """
        return (self._document is None
                and self._parent is None
                and self._item is not None)

    @property
    def document(self):
        """
        Return the document object (the topmost parent document fragment)
        """
        return self._document

    @property
    def parent(self):
        """
        Return the parent fragment.

        The document root (typically Document instance) has no parent. If the
        parent exist then 'fragment.parent[fragment.item]' points back to the
        same value as 'fragment' but wrapped in a different instance of
        DocumentFragment.
        """
        return self._parent

    @property
    def item(self):
        """
        Get the key that was used to access this fragment from the parent
        fragment. Typically this is the dictionary key name or list index.
        """
        return self._item

    def _get_schema_for_item(self, item):
        if self.schema is None:
            return
        item_schema = None
        value = self.value
        if isinstance(value, dict):
            # For objects/dictionaries
            # Try accessing schema for specific property first.
            try:
                item_schema = self.schema.properties[item]
            except KeyError:
                # If that fails try to use additionalProperties, unless it is False
                if self.schema.additionalProperties is not False:
                    item_schema = self.schema.additionalProperties
                # If that fails then we have no schema, sorry
                # TODO: Maybe support patternProperties later
        elif isinstance(value, list):
            # For arrays with array schemas (one schema item per array item)
            # try to access the schema for a particular item first
            if isinstance(self.schema.items, list):
                try:
                    item_schema = self.schema.items[item]
                except IndexError:
                    # If that fails fall back to additionalItems (not
                    # implemented in linaro_json yet)
                    if self.schema.additionalItems is not False:
                        item_schema = self.schema.additionalItems
            elif isinstance(self.schema.items, dict):
                # For arrays with single scheme for each array item just use
                # the schema directly.
                item_schema = self.schema.items
        return item_schema

    def _add_sub_fragment_to_cache(self, item, allow_create, create_value):
        """
        Add a new fragment instance to the this fragment's cache.
        """
        self._ensure_not_orphaned()
        if not isinstance(self.value, (dict, list)):
            raise TypeError(
                "DocumentFragment must point to a dictionary or list")
        item_schema = self._get_schema_for_item(item)
        try:
            # Since we are using self.value instead of self._value we are
            # using defaults transparently.
            item_value = self.value[item]
        except (KeyError, IndexError) as ex:
            if item_schema is not None and "default" in item_schema:
                item_value = DefaultValue
            elif allow_create is True:
                self._ensure_not_default()
                self._value[item] = create_value
                #  We need to mark the object as dirty manually
                self._document._is_dirty = True
                item_value = create_value
            else:
                raise ex
        if item_schema is not None and "__fragment_cls" in item_schema:
            fragment_cls = item_schema["__fragment_cls"]
        else:
            fragment_cls = DocumentFragment
        self._fragment_cache[item] = fragment_cls(
            self._document, self, item_value, item, item_schema)

    def _get_sub_fragment(self, item, allow_create=False, create_value=None):
        """
        Get a DocumentFragment for the specified item.

        This method is used to implement __getitem__ and __setitem__.

        If the item is missing in this fragment and allow_create is True then
        an appropriate object is constructed.
        """
        if item not in self._fragment_cache:
            self._add_sub_fragment_to_cache(item, allow_create, create_value)
        return self._fragment_cache[item]

    def __getitem__(self, item):
        """
        Get a sub-fragment for the specified item

        This method will return a DocumentFragment (or DocumentFragment
        subclass) instance associated with the specified item.
        """
        return self._get_sub_fragment(item)

    def __setitem__(self, item, new_value):
        """
        Set the value of a sub-fragment.

        Note: unlike __getitem__ this method operates directly on the value.
        It is equivalent to fragment[item].value = new_value but it works
        correctly for missing items.

        See value= for details on how assignment works.
        """
        fragment = self._get_sub_fragment(item, allow_create=True,
                                          create_value=new_value)
        fragment.value = new_value

    def __contains__(self, item):
        """
        Return True if the specified item is in this fragment.

        Works as expected for fragments pointing at lists, dictionaries and
        strings. Raises TypeError for fragments pointing at any other value
        type.
        """
        return item in self.value

    def __len__(self):
        """
        Return the length of this fragment's value.

        Works as expected for fragments pointing at lists, dictionaries and
        strings. Raises TypeError for fragments pointing at any other value
        type.
        """
        return len(self.value)

    def _iter_list(self):
        for item in range(len(self.value)):
            yield self[item]

    def _iter_dict(self):
        for item in self.value.iterkeys():
            yield self[item]

    def __iter__(self):
        """
        Iterate over the elements of this fragments value.

        Works as expected for fragments pointing at lists and dictionaries.
        Raises TypeError for fragments pointing at any other value type.
        """
        if isinstance(self.value, dict):
            return self._iter_dict()
        elif isinstance(self.value, list):
            return self._iter_list()
        else:
            raise TypeError("%r is not iterable" % self)

    get = __getitem__

    set = __setitem__


class DocumentBridge(object):
    """
    Helper with decorator methods for accessing document fragments
    """

    @staticmethod
    def fragment(func):
        """
        Bridge to a document fragment.

        The name of the fragment is identical to to the name of the decorated
        function. The function is never called, it is only used to obtain the
        docstring.

        This is equivalent to:

            @property
            def foo(self):
                return self['foo']
        """
        def _get(self):
            return self[func.__name__]
        return property(_get, None, None, func.__doc__)

    @staticmethod
    def readonly(func):
        """
        Read-only bridge to the value of a document fragment.

        The name of the fragment is identical to to the name of the decorated
        function.  The function is never called, it is only used to obtain the
        docstring.

        This is equivalent to:

            @property
            def foo(self):
                return self['foo'].value
        """
        def _get(self):
            return self[func.__name__].value
        return property(_get, None, None, func.__doc__)

    @staticmethod
    def readwrite(func):
        """
        Read-write bridge to the value of a document fragment.

        The name of the fragment is identical to to the name of the decorated
        function.  The function is never called, it is only used to obtain the
        docstring.

        This is equivalent to:

            @property
            def foo(self):
                return self['foo'].value

            @foo.setter
            def foo(self, new_value):
                return self['foo'] = new_value
        """
        def _get(self):
            return self[func.__name__].value

        def _set(self, new_value):
            # XXX: See what __setitem__ does to understand why we don't assign
            # to .value
            self[func.__name__] = new_value
        return property(_get, _set, None, func.__doc__)


class Document(DocumentFragment):
    """
    Class representing a smart JSON document
    """
    document_schema = {"type": "object"}

    def __init__(self, pathname=None, schema=None):
        if pathname is not None and not pathname.endswith(".json"):
            raise DocumentError(self, "JSON file must have .json extension")
        self._is_dirty = False
        self._pathname = pathname
        super(Document, self).__init__(
            document=self,
            parent=None,
            value={},
            item=None,
            schema=schema or self.document_schema)

    @property
    def is_dirty(self):
        """
        Returns True when the document has been modified and needs to be saved
        """
        return self._is_dirty

    @property
    def pathname(self):
        return self._pathname

    def _validate(self):
        try:
            super(Document, self).validate()
        except ValidationError as ex:
            raise DocumentSchemaError(self, ex)

    def _save(self):
        if self._pathname is None:
            raise ValueError("No pathname specified")
        # TODO: handle and wrap JSONEncodeError here
        with open(self._pathname, 'wt') as stream:
            DocumentIO.dump(stream, self._value)

    def _load(self):
        if self._pathname is None:
            raise ValueError("No pathname specified")
        try:
            with open(self._pathname, 'rt') as stream:
                self._value = DocumentIO.load(stream)
        except simplejson.JSONDecodeError as ex:
            raise DocumentSyntaxError(self, ex)

    def save_as(self, pathname):
        if pathname is not None:
            self._pathname = pathname
        self.save()

    def save(self):
        if self._is_dirty:
            self._validate()
            self._save()
            self._is_dirty = False

    def load(self, ignore_missing=False):
        if os.path.exists(self._pathname) or not ignore_missing:
            self._load()
            self._is_dirty = False
            self._validate()
