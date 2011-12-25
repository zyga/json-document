JSON Document
=============

This package provides intuitive and powerful binding system for JSON documents.
It bridged the gap between raw python objects, json schema and json files.  A
powerful default system also allows developers to access an empty document and
see the default values from the schema without any code changes.


Basics
^^^^^^

If you have a few seconds, just read the next two sections.

Setting and accessing value
---------------------------

You can use a Document class much like a normal python
object. If you are using JSON via raw dictionaries/lists
you'll find that a lot of things are the same::

    >>> from json_document.document import Document
    >>> doc = Document({})
    >>> doc['hello'] = 'world'

The first major difference is evident when you want to refer to data. Instead
of returning the value directly you get an instance of DocumentFragment. To
access the value just use the value property:: 

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

This schema can be read as follows::

    The root element is an object titled "Person record".
    It has a property "name" that is a string titled "Full name".
    It also has a property "age" that is a number titled "Age in years"

This schema is very simple but it already defines the correct shape of a
document. It defines the type of the root object (a json "object", for python
that translates to a dictionary instance). It also describes the attributes of
that object (name and age) and their type. The schema also mixes documentation
elements via the "title" and "description" properties.

Using a schema you can ``validate`` documents for correctness. Let's see how that
works::

    >>> joe = Document({"name": "joe", "age": 32}, person_schema)
    >>> joe.validate()

Calling validate() would have raised an exception if joe was not a valid
"Person record". Let's set the age to an invalid type to see how that works::

    >>> joe["age"] = "thirty two"
    >>> joe.validate()
    Traceback (most recent call last):
    ...
    ValidationError: ValidationError: Object has incorrect type (expected number) object_expr='object.age', schema_expr='schema.properties.age.type')

Boom! Not only did the validation fail. We've got a detailed error message that
outlines the problem. It also gives us the JavaScript expression that describes
the part that did not match the schema (object.age) and the part of the schema
that was violated (schema.properties.age.type).

Because the actual value is hidden behind the .value property we can stash a
set of useful properties and methods in each DocumentFragment. One of them is
.schema which unsurprisingly returns the associated schema element (if we have
one). Unlike returning the raw JSON schema it returns a smart wrapper around it
that has properties corresponding to each legal schema part (such as .type and
.properties). You can use it to access meta-data such as title and description::

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

Digging deeper
^^^^^^^^^^^^^^

So now you know roughly about documents and schema. You know that accessing
items on a document instance returns DocumentFragment objects (that have a
.value and .schema properties) but setting items sets the value directly. You
know that a document may have an associated schema and calling validate()
checks for errors. 

Supported types
---------------

Now let's expand that. So far we've only used objects (dictionaries). We 
can use the following types in our documents:

* Dictionaries (JSON objects, schema type "object")
* Lists (JSON arrays, schema type "array")
* Strings (and Unicode strings, schema type "string")
* Integers, floating point numbers and Decimals (JSON numbers, schema types "integer", "number")
* True and False (JSON true and false values, schema type "boolean")
* None (JSON null value, schema type "null")

You can use any of those items as the root object.

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

Well, all except for the None which transparently translates to an empty object
for convenience::

    >>> surprise = Document(None)
    >>> surprise.value
    {}

Default schema
--------------

All documents have a schema, even if you don't specify one. By default the schema
describes an arbitrary object (one with any properties)::

    >>> doc = Document()
    >>> doc.schema
    Schema({'type': 'object'})

This does not apply to fragments you create yourself. Those always inherit the schema from their
parent document (depending on the item used to create or access that fragment). Since the default
schema does not describe the 'foo' property it is assigned an empty schema instead::

    >>> doc['foo'] = 'bar'
    >>> doc['foo'].schema
    Schema({})

It's important to point out that default type is 'any'. It allows the value to
be of any previously mentioned type::

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

Let's see how this works. Imagine a simple application that has a 'save on
exit' feature. The application starts up, loads settings from a configuration
file and does something useful. When the user quits the application it can save
the current document without asking for confirmation. Traditionally you'd embed
the default value in the code of your application. If you were smart you'd
build an API for your configuration to transparently provide the default for
you (or you'd generate the default configuration file if it was missing).

Both of those approaches are not very nice in practice. The former requires you
to build additional layers of API around your basic notion of configuration.
The latter prevents you from differentiating default values and settings
identical to default values.

We can do better than that. Let's start with describing our configuration schema::

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

* The default value is specified
* The property is marked as optional

Let's create a configuration object to see how this works::

    >>> config = Document({}, schema)
    >>> config["save_on_exit"].value
    True

Success! Still a little verbose but already doing much, much better. The
default value was looked up in the schema and provided in place of our missing
configuration option. We can see this option is default by accessing a few
methods and properties.  With .is_default you can check if .value is a real
thing or a substitute from the schema. With .default_value you can see what the
default is. Lastly, with .default_value_exists you can check if there even is a
default specified. After all, if the schema has no defaults then your code will
simply trigger an exception instead::

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

Let's start with some settings we loaded for this user::

    >>> config = Document({"save_on_exit": True}, schema)

The first thing to point out is that a default value is a 'special' thing. Being
equal to the default value is not the same as being default. Here, the save_on_exit
option is True, the same as the default from the schema. It is not default though::

    >>> config["save_on_exit"].is_default
    False
    
To really make it default you need to call the revert_to_default() method::

    >>> config["save_on_exit"].revert_to_default()
    >>> config["save_on_exit"].value
    True
    >>> config["save_on_exit"].is_default
    True
    
When you do that the document is transformed and the part we've customized
is removed::

    >>> config.value
    {}
