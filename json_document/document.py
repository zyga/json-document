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
json_document.document
----------------------

Document and fragment classes
"""

import copy
from json_schema_validator.errors import SchemaError
from json_schema_validator.schema  import Schema
from json_schema_validator.validator import Validator

from json_document.errors import OrphanedFragmentError


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
    Wrapper around a fragment of a document.

    Fragment may wrap a single item (such as None, bool, int, float, string) or
    to a container (such as list or dict). You can access the value pointed to
    with the :attr:`value` property.

    Each fragment is linked to a :attr:`parent` fragment and the
    :attr:'`document` itself. When the parent fragment wraps a list or a
    dictionary then the index (or key) that this fragment was references as is
    stored in :attr:`item`. Sometimes this linkage becomes broken and a
    fragment is considered orphaned. Orphaned fragments still allow you to read
    the value they wrap but since they are no longer associated with any
    document you cannot set the value anymore.

    Fragment is also optionally associated with a schema (typically the
    relevant part of the document schema). When schema is available you can
    :meth:`validate()` a fragment for correctness. If the schema designates a
    :attr:`default_value` you can :meth:`revert_to_default()` to discard the
    current value in favour of the one from the schema.

    .. note: 

        Fragments cache their children. If you access a fragment item (through the
        __getitem__ operator) a new fragment instance wrapping that value is
        created and retained. Fragment cache is only purged if you overwrite the
        value directly. This also orphans the fragments that were created so far.
    """

    __slots__ = ('_document', '_parent', '_value', '_item', '_schema',
                 '_fragment_cache')

    def __init__(self, document, parent, value, item=None, schema=None):
        self._document = document
        self._parent = parent
        self._value = value
        self._item = item
        self._schema = schema
        self._fragment_cache = {}

    @property
    def schema(self):
        """
        Schema associated with this fragment
        
        Schema may be None

        This is a read-only property. Schema is automatically provided when a
        sub-fragment is accessed on a parent fragment (all the way up to the
        document). To provide schema for your fragments make sure to include
        them in the ``properties`` or ``items``. Alternatively you can provide
        ``additionalProperties`` that will act as a catch-all clause allowing
        you to define a schema for anything that was not explicitly matched by
        ``properties``.
        """
        if self._schema is not None:
            return Schema(self._schema)

    @property
    def is_default(self):
        """
        Check if this fragment points to a default value.

        .. note::

            A fragment that points to a value equal to the value of the default
            is **not** considered default. Only fragments that were not
            assigned a value previously are considered default.
        """
        return self._value is DefaultValue

    def revert_to_default(self):
        """
        Discard current value and use defaults from the schema.

        @raises TypeError: when default value does not exist 
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
            self._lowlevel_set_value(DefaultValue)
            # Bump the document revision
            self._document._bump_revision()

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
        """
        Returns True if a default value exists for this fragment.

        The default value can be accessed with :attr:`default_value`. You can
        also revert the current value to default by calling
        :meth:`revert_to_default()`.

        When there is no default value any attempt to use or access it will
        raise a SchemaError.
        """
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

    def _get_value(self):
        if self.is_default:
            return self.default_value
        else:
            return self._value

    def _set_value(self, new_value):
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
            self._lowlevel_set_value(new_value)
            # Bump the document revision
            self._document._bump_revision()

    value = property(_get_value, _set_value, None, """
        Value being wrapped by this document fragment.

        Getting reads the value (if not :attr:`is_default`) from the document
        or transparently returns the default values from the schema (if
        :attr:`default_value_exists`).

        Setting a value instantiates default values in this or any parent
        fragment. That is, if the value of this fragment or any of the parent
        fragments is default (:attr:`is_default` returns True), then the
        default value is copied and used as the effective value instead.

        When :attr:`is_default` is True setting any value (including the value
        of :attr:`default_value`) will overwrite the value so that
        :attr:`is_default` will return False. If you want to *set the default
        value* use :meth:`revert_to_default()` explicitly.

        Setting a value that is different from the current value bumps the
        revision of the whole document.
        """)

    def _lowlevel_set_value(self, new_value):
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
            self._lowlevel_set_value(copy.deepcopy(self.schema.default))

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

        .. note::

            This does method _not_ remove the fragment from the parent's
            fragment cache. This is handled by _set_value() which calls
            _orhpan() on sub fragments it knows about.
        """
        self._parent = None
        self._document = None
        self._value = copy.deepcopy(self._value)

    @property
    def is_orphaned(self):
        """
        Check if a fragment is orphaned.

        Orphaned fragments can occur in this scenario::

            >>> doc = Document()
            >>> doc["foo"] = "value"
            >>> foo = doc["foo"]
            >>> doc.value = {}
            >>> foo.is_orphaned
            True

        That is, when the parent fragment value is overwritten.
        """
        return (self._document is None
                and self._parent is None
                and self._item is not None)

    @property
    def document(self):
        """
        The document object (the topmost parent document fragment)
        """
        return self._document

    @property
    def parent(self):
        """
        The parent fragment (if any)

        The document root (typically a :class:`Document` instance) has no
        parent. If the parent exist then ``fragment.parent[fragment.item]``
        points back to the same value as ``fragment`` but wrapped in a
        different instance of DocumentFragment.
        """
        return self._parent

    @property
    def item(self):
        """
        The index of this fragment in the parent collection.

        Item is named somewhat misleadingly. It is the name of the index that
        was used to access this fragment from the parent fragment. Typically
        this is the dictionary key name or list index.
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
                # If that fails try to use additionalProperties,
                # unless it is False
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
                    # implemented in json-schema-validator yet)
                    if self.schema.additionalItems is not False:
                        item_schema = self.schema.additionalItems
            elif isinstance(self.schema.items, dict):
                # For arrays with single schema for each array item just use
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
                # We need to manually bump the document revision
                self._document._bump_revision()
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

        .. note::
        
            unlike :meth:`__getitem__()` this method operates directly on the
            value. It is equivalent to ``fragment[item].value = new_value``
            but it works correctly for missing items.

            See :attr:`value` for details on how assignment works.
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


class Document(DocumentFragment):
    """
    Class representing a smart JSON document

    A document is also a fragment that wraps the entire value. Is inherits all
    of its properties. There are two key differences: a document has no parent
    fragment and it holds the revision counter that is incremented on each
    modification of the document.
    """
    document_schema = {"type": "any"}

    __slots__ = DocumentFragment.__slots__ + ('_revision',)

    def __init__(self, value, schema=None):
        """
        Construct a document with the specified value and schema.

        Value is required. The schema defaults to document_schema attribute
        on the class object (which by default it a very simple schema for any objects).
        """
        # Start with an empty object by default
        # Initialize DocumentFragment
        super(Document, self).__init__(
            document=self,
            parent=None,
            value=value,
            item=None,
            schema=schema or self.__class__.document_schema)
        # Initially set the revision to 0
        self._revision = 0

    @property
    def revision(self):
        """
        Return the revision number of this document.

        Each change increments this value by one. You should not really care
        about the count as sometimes the increments may be not what you
        expected. It is best to use this to spot difference (if your count is
        different than mine we're different).
        """
        return self._revision

    def _bump_revision(self):
        """
        Increment the document revision number.

        This is a private method, it is called by DocumentFragment
        """
        self._revision += 1


class DocumentPersistence(object):
    """
    Simple glue layer between document and storage::

        document <-> serializer <-> storage

    You can have any number of persistence instances associated with a
    single document.
    """

    def __init__(self, document, storage, serializer=None):
        self.document = document
        self.storage = storage
        self.serializer = serializer
        self.last_revision = None

    def load(self):
        """
        Load the document from the storage layer
        """
        text = self.storage.read()
        obj = self.serializer.loads(text)
        self.document.value = obj
        self.last_revision = self.document.revision

    def save(self):
        """
        Save the document to the storage layer.

        The document is only saved if the document was modified since
        it was last saved. The document revision is non-persistent
        property (so you cannot use it as a version control system) but
        as long as the document instance is alive you can optimize
        saving easily.
        """
        if self.last_revision != self.document.revision:
            if self.serializer.needs_real_object:
                obj = self.document
            else:
                obj = self.document.value
            text = self.serializer.dumps(obj)
            self.storage.write(text)
            self.last_revision = self.document.revision

    @property
    def is_dirty(self):
        return self.last_revision != self.document.revision
