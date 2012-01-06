Basic features
^^^^^^^^^^^^^^

If you have a few seconds, just read the next two sub-sections.

Setting and accessing value
---------------------------

You can use a Document class much like a normal python
object. If you are using JSON via raw dictionaries/lists
you'll find that a lot of things are the same::

    >>> from json_document.document import Document
    >>> doc = Document({})
    >>> doc['hello'] = 'world'

The first major difference is evident when you want to refer to data. Instead
of returning the value directly you get an instance of
:class:`~json_document.document.DocumentFragment`. To access the value you'll
have to use the :attr:`~json_document.document.DocumentFragment.value`
property:: 

    >>> doc['hello'].value
    'world'
    >>> doc.value
    {'hello': 'world'}

Accessing the fragment directly is also possible and indeed is where a lot of
the value json_document brings is hidden. To learn about that though you'll
have to learn about using schema with your documents.

Using document schema
---------------------

Schema defines how a valid document looks like. It is constructed of a series
of descriptions (written in JSON itself) and is quite powerful in what can be
expressed. If you have no experience with JSON-Schema you can think of it as
DTD for XML on steroids. Don't worry it's easy to learn by example.

Let's design a simple schema for a personnel registry. Each document will
describe one person and will remember their name and age::

    >>> person_schema = {
    ...     "type": "object",
    ...     "title": "Person record",
    ...     "description": "Simplified description of a person",
    ...     "properties": {
    ...         "name": {
    ...             "type": "string",
    ...             "title": "Full name"
    ...         },
    ...         "age": {
    ...             "type": "number",
    ...             "title": "Age in years"
    ...         }
    ...     }
    ... }

This schema can be read as follows:

* The root element is an object titled "Person record".
* It has a property "name" that is a string titled "Full name".
* It also has a property "age" that is a number titled "Age in years"

This schema is very simple but it already defines the correct shape of a
document. It defines the type of the root object (a json "object", for python
that translates to a dictionary instance). It also describes the attributes of
that object (name and age) and their type. The schema also mixes documentation
elements via the "title" and "description" properties.

Using a schema you can `validate` documents for correctness. Let's see how that
works::

    >>> joe = Document({"name": "joe", "age": 32}, person_schema)
    >>> joe.validate()

Calling :meth:`~json_document.document.DocumentFragment.validate()` would have
raised an exception if joe was not a valid "Person record". Let's set the age
to an invalid type to see how that works::

    >>> joe["age"] = "thirty two"
    >>> joe.validate()
    Traceback (most recent call last):
    ...
    ValidationError: ValidationError: Object has incorrect type (expected number) object_expr='object.age', schema_expr='schema.properties.age.type')

Boom! Not only did the validation fail. We've got a detailed error message that
outlines the problem. It also gives us the JavaScript expression that describes
the part that did not match the schema (``object.age``) and the part of the schema
that was violated (``schema.properties.age.type``).

Because the actual value is hidden behind the .value property we can stash a
set of useful properties and methods in each ``DocumentFragment``. One of them
is ``.schema`` which unsurprisingly returns the associated schema element (if
we have one). Instead of returning the raw JSON schema it returns a smart wrapper
around it that has properties corresponding to each legal schema part (such as
``.type`` and ``.properties``). You can use it to access meta-data such as
title and description::

    >>> joe["age"].schema.title
    'Age in years'
    >>> joe.schema.description
    'Simplified description of a person'

You can also access things like type but be aware that it has some quirks.
Refer to json-schema-validator documentation for details on the Schema class.
For example, the type is automatically converted to a list of valid types::

    >>> joe["name"].schema.type
    ['string']

One useful property is .schema.optional which tells if if an element is
required or not. By default everything is required, unless marked optional::

    >>> joe["name"].schema.optional
    False
