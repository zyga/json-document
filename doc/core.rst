Core features
^^^^^^^^^^^^^

So now you know roughly about documents and schema. You know that accessing
items on a document instance returns
:class:`~json_document.document.DocumentFragment` objects (that have a
:attr:`~json_document.document.DocumentFragment.value` and
:attr:`~json_document.document.DocumentFragment.schema` properties) but setting
items sets the value directly. You know that a document may have an associated
schema and that calling
:meth:`~json_document.document.DocumentFragment.validate()` checks for errors. 

Supported types
---------------

Now let's expand that. So far we've only used objects (that map to Python
dictionaries). We can use the following types in our documents:

* Dictionaries (JSON objects, schema type "object")
* Lists (JSON arrays, schema type "array")
* Strings (and Unicode strings, schema type "string")
* Integers, floating point numbers and Decimals (JSON numbers, schema types "integer", "number")
* True and False (JSON true and false values, schema type "boolean")
* None (JSON null value, schema type "null")

You can use any of those items as the root object::

    >>> from json_document.document import Document

    >>> shopping_list = Document([])
    >>> shopping_list.value.append("milk")
    >>> shopping_list.value.append("cookies")
    >>> shopping_list.value
    ['milk', 'cookies']

    >>> yummy = Document("json")
    >>> yummy.value
    'json'

    >>> life = Document(42)
    >>> life.value
    42

    >>> long_example = Document(True)
    >>> long_example.value
    True

    >>> surprise = Document(None)
    >>> surprise.value
    None
    

Default schema
--------------

All documents have a schema, even if you don't specify one. By default the schema
describes an arbitrary JSON value (one of any type)::

    >>> doc = Document({})
    >>> doc.schema
    Schema({'type': 'any'})

This does not apply to fragments you create yourself. Those always inherit the schema from their
parent document (depending on the item used to create or access that fragment). Since the default
schema does not describe the ``foo`` property it is assigned an empty schema instead::

    >>> doc['foo'] = 'bar'
    >>> doc['foo'].schema
    Schema({})

It's important to point out that default type is ``any``. It allows the value
to be of any previously mentioned type::

    >>> doc['foo'].schema.type
    ['any']


Schema on fragments
-------------------

It's pretty obvious but important to point out that when a schema describes a
document and you access a fragment of that document the fragment's schema is
the corresponding fragment of the whole::

    >>> doc = Document({"foo": "bar"}, {"properties": {"foo": {"type": "string"}}})
    >>> doc["foo"].schema
    Schema({'type': 'string'})

This is very useful when you consider that a schema can specify default values
for missing elements.

Using default values
--------------------

Having a schema for a document is not only useful because you can validate it.
It is also useful because you can embed default values in the schema and
transparently use them as if they were specified in the document.

Let's see how this works. Imagine a simple application that has a *save on
exit* feature. The application starts up, loads settings from a configuration
file and does something useful. When the user quits the application it can save
the current document without asking for confirmation. Traditionally you'd embed
the default value in the code of your application. If you were smart you'd
build an API for your configuration to transparently provide the default for
you (or you'd generate the default configuration file if it was missing).

Both of those approaches are not very nice in practice. The former requires you
to build additional layers of API around your basic notion of configuration.
The latter prevents you from differentiating default values and settings
identical to default values.

We can do better than that. Let's start with describing our configuration
schema::

    >>> schema = {
    ...     "type": "object",
    ...     "properties": {
    ...         "save_on_exit": {
    ...             "type": "boolean",
    ...             "default": True,
    ...             "optional": True
    ...         }
    ...     }
    ... }

There are a couple of new elements here:

* The default value is specified, exactly once, in the schema
* The property is marked as optional, when missing the document will
  still be valid.

Let's create a configuration object to see how this works::

    >>> config = Document({}, schema)
    >>> config["save_on_exit"].value
    True

Success! Still a little verbose but already doing much, much better. The
default value was looked up in the schema and provided in place of our missing
configuration option. We can see this option is default by accessing a few
methods and properties.  With
:attr:`~json_document.DocumentFragment.is_default` you can check if .value is a
real thing or a substitute from the schema. With
:attr:`~json_document.document.DocumentFragment.default_value` you can see what
the default is. Lastly, with
:attr:`~json_document.document.DocumentFragment.default_value_exists` you can
check if there even is a default specified. After all, if the schema has no
defaults then your code will simply trigger an exception instead::

    >>> config["save_on_exit"].is_default
    True
    >>> config["save_on_exit"].default_value
    True
    >>> config["save_on_exit"].default_value_exists
    True

We can still change the value as we had before, all of that works as expected.
The non-obvious part is what the value of our document is. Before we change
anything it is still left as-is, as we provided it initially, that is, empty.::

    >>> config.value
    {}

If we change it, however, it reflects that change:: 

    >>> config["save_on_exit"] = False
    >>> config.value
    {'save_on_exit': False}

Reverting to defaults
---------------------

Let's suppose our application wants to provide a "revert to defaults" button
that resets all configuration options to what was provided out of the box.
JSON document has a sweet feature to support this kind of behavior.

Let's start with some settings we loaded for this user (we are reusing the
schema from the previous example)::

    >>> config = Document({"save_on_exit": True}, schema)

The first thing to point out is that a default value is a 'special' thing.
Being equal to the default value is not the same as being default. Here, the
``save_on_exit`` option is True, the same as the default from the schema. It is
not default though::

    >>> config["save_on_exit"].is_default
    False

To really make it default you need to call the
:meth:`~json_document.document.DocumentFragment.revert_to_default()` method::

    >>> config["save_on_exit"].revert_to_default()
    >>> config["save_on_exit"].value
    True
    >>> config["save_on_exit"].is_default
    True

When you do that the document is transformed and the part we've customized is
removed. Obviously without a default value in the schema this method would
raise an exception with an appropriate message::

    >>> config.value
    {}

Defaults are a very powerful system. Used correctly they allow applications to
recover from manually edited configuration files (config errors), allow users
to customize parts of their configuration while allowing defaults to evolve
with future versions and significantly simplify application configuration
handling for programmers where less checking is needed, especially when coupled
with JSON schema validation that can not only shape but constrain values of
specific properties. 

Fragments and references
------------------------

So far in this document we've been referring to document fragments by accessing
dictionary items and array elements on the root document object. Accessing
those items transparently creates
:class:`~json_document.document.DocumentFragment` instances. Wrapper objects
pointing to a sub-tree of the document object. It is possible to save those
references and use them freely for convenience. Let's see how this works::

    >>> doc = Document({})
    >>> doc["list"] = [1, 2, 3]
    >>> doc["dict"] = {"hello": "world"}
    >>> doc["value"] = "I'm a plain string"

For clarity, this is how the document looks like now::

    >>> doc.value
    {'dict': {'hello': 'world'}, 'list': [1, 2, 3], 'value': "I'm a plain string"}

Let's obtain a reference to the list::

    >>> lst = doc["list"]

A document fragment is much like a document itself
(:class:`~json_document.fragment.Document` is also a DocumentFragment subclass)
it has a .value and .schema properties. It has a revert_to_default() method and
everything you've learned so far.

It can also be modified, and here it gets interesting. You can modify the value
by assigning to the .value property::

    >>> lst.value
    [1, 2, 3]
    >>> lst.value = [4, 5]
    >>> lst.value
    [4, 5]

The interesting part is that this automatically integrates into the document
this fragment is a part of::

    >>> doc.value
    {'dict': {'hello': 'world'}, 'list': [4, 5], 'value': "I'm a plain string"}

In general it you can freely modify the tree and it will work as expected::

    >>> dct = doc["dict"]
    >>> dct.value = {'hello': 'there'}
    >>> val = doc["value"]
    >>> val.value = 42
    >>> doc.value
    {'dict': {'hello': 'there'}, 'list': [4, 5], 'value': 42}

You can also use mutating methods (those that alter the state of the value), in
this case you are not assigning a new value to the .value property but rather
calling some method on it::

    >>> lst.value.append(6)
    >>> dct.value['hello'] = 'joe'
    >>> doc.value
    {'dict': {'hello': 'joe'}, 'list': [4, 5, 6], 'value': 42}

Fragments also have a few interesting properties. The .document property allows
you to reach the document object this fragment is a part of. The .parent
property points to the parent fragment (say, if you have a fragment to member
of a list then the .parent will be pointing to the list itself). The .item
property is perhaps named confusingly but it is the index of this fragment in
the parent fragment (the list index or dictionary key)

Fragments also have few special methods that make using them more natural in
python. You can check the length (of strings, dicts and lists), you can check
for membership using the ``foo in bar`` syntax. You can also iterate over
containers (lists and dicts only)

Orphaned fragments
------------------

Since you can keep references to fragments around for as long as you like it is
possible to create an interesting situation. It is only interesting in a
problematic way though. A fragment can become orphaned (and useless) when its
parent (or its parent, all the way up to the root document object) are
overwritten. Let's see how this works::

    >>> doc = Document({})
    >>> doc['foo'] = 'bar'
    >>> foo = doc['foo']
    >>> doc.value = {}
    >>> foo.is_orphaned
    True

So now the ``foo`` fragment is an orphaned. A few things happen when this
occurs:

* The .document property is set to None
* The .parent property is set to None
* The .value is set to a deep copy of the original value

So for all intents and purposes an orphaned node is independent leftover that
is totally disconnected from the original. This means that changing its value
is not going to alter the document anymore (since this would make no sense). In
fact, attempting to change the value will raise an
:class:`~json_document.errors.OrphanedFragmentError`::

    >>> foo.value = "barf"
    Traceback (most recent call last):
    ...
    OrphanedFragmentError: Attempt to modify orphaned document fragment

Usually when you see this it indicates a programming error. If you want to keep
using something don't overwrite its parent. For convenience it is not an error
to read from an orphaned fragment as it is useful in some cases and provides
some level of 'transaction isolation' where you can bet that you've got a
working fragment (just that the writes will fail)
