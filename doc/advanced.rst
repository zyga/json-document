Advanced features
^^^^^^^^^^^^^^^^^

If you got this far you know pretty much everything there is about the basic
feature set. The rest of this document will make you more productive by letting
you write less code and by letting you write code that is more natural to read
and use later.

Custom fragments
----------------

Since you get fragment objects every time you access some of its parts would
not it be nice to be able to put your custom methods there? This way you could
somewhat forget about working with JSON and see this as a part of your class
hierarchy.

I thought it was useful so here it is. You need to have a schema for your
document the reason for that is we'll be embedding special schema elements that
will override the instantiated fragment class. Usually this is simple but it is
boiler-plate-ish at times::

For the sake of documentation we'll be writing a word counter program that will
store the count of each encountered word. We'll need to subclass
DocumentFragment so let's pull that in to our namespace::

    >>> from json_document.document import Document, DocumentFragment

The Word class is what will represent each word we've encountered. We'll start
by keeping it simple, just a inc() method::

    >>> class Word(DocumentFragment):
    ...
    ...     def inc(self): 
    ...         self.value += 1


The WordCounter class will be a custom Document that just has the schema. Here
we also see that the schema can be defined once in the document class by
creating a ``document_schema`` property. This is convenient when you have one
schema and want to make the life of your users easier. The schema defines an
object (with a default value of {}). This object can have additional properties
(that is, properties not explicitly mentioned in the schema) but each one has
to be an integer. If missing the default value of each property is zero.
Finally the special ``__fragment_cls`` schema entry instructs which
DocumentFragment sub-class to instantiate::

    >>> class WordCounter(Document):
    ...
    ...     document_schema = {
    ...         'type': 'object',
    ...         'default': {},
    ...         'additionalProperties': {
    ...             'type': 'integer',
    ...             'default': 0,
    ...             '__fragment_cls': Word
    ...         }
    ...     }

Having done that we can now start using this::

    >>> doc = WordCounter()

Default values work::

    >>> doc['json'].value
    0

As did our custom class declaration::

    >>> for word in "json is a nice thing to keep your data, json".split():
    ...     doc[word].inc()

Finally the data is saved and we can inspect it or save it later::

    >>> doc['json'].value
    2

Value bridge
---------------

So we have all the nice features so far, we even have custom fragment classes
to keep our code more maintainable and readable. The last thing that was
annoying me was the need to use dictionary notation to access my fragments. I
wanted to use object traversal notation instead. I ended up writing a lot of
properties that were just exposing the fragment in a more natural syntax.

Let's see what it was like::

    >>> class Config(Document):
    ...
    ...     document_schema = {
    ...         'type': 'object',
    ...         'default': {},
    ...         'properties': {
    ...             'save_on_exit': {
    ...                 'type': 'bool',
    ...                 'default': True 
    ...             }
    ...         }
    ...     }
    ...
    ...     @property
    ...     def save_on_exit(self):
    ...         return self['save_on_exit']

    >>> conf = Config()
    >>> conf.save_on_exit.value
    True

It worked but was somewhat tedious (I had to repeat the name of the property.
It was also annoying if it the property was a simple value (not something more
complicated that itself would be having extra methods/state) and I had to type
.value all the time.

So I wrote three good decorators that made this easy. They are all in the bridge module::

    >>> from json_document import bridge

We can now improve our Config class with one of them the 'readwrite' bridge::

    >>> class BetterConfig(Config):
    ...
    ...     @bridge.readwrite
    ...     def save_on_exit(self):
    ...         ''' documentation on this property '''
 
The intent and code is very clear, it simply allows you to read and write the
.value directly, without having the extra lookup on your side. It also gives
your JSON document pythonic look and documentation.

    >>> conf = BetterConfig()
    >>> conf.save_on_exit
    True
    >>> conf.save_on_exit = False
    >>> conf.save_on_exit
    False

If something is not really going to change (say you are only reading a part of
a document that is modified by third party program) you can make that explicit
in your code by using ``bridge.readonly`` instead.

Fragment bridge
---------------

Fragment bridge is very similar to the value bridge (readonly and readwrite)
but instead of returning the value it returns the fragment itself. It allows
for more readable code that can still access all the methods and properties
that DocumentFragment provides.

I found it useful to document my JSON structure on the python side by mapping
larger pieces of the schema to custom classes and putting fragment bridges in
the document class.

Let's say you have a person record with first and last name strings::

    >>> class PersonName(DocumentFragment):
    ...     """ Person's name """
    ...
    ...     @bridge.readwrite
    ...     def first(self):
    ...         """ First name """
    ...
    ...     @bridge.readwrite
    ...     def last(self):
    ...         """ Last name """
    ...
    ...     @property
    ...     def full(self):
    ...         return "%s %s" % (self.first, self.last)

    >>> class Person(Document):
    ...     """ Person record """
    ...
    ...     document_schema = {
    ...         'type': object,
    ...         'properties': {
    ...             'name': {
    ...                 'type': 'object',
    ...                 'default': {},
    ...                 '__fragment_cls': PersonName,
    ...                 'properties': {
    ...                     'first': {
    ...                         'type': 'string'
    ...                     },
    ...                     'last': {
    ...                         'type': 'string'
    ...                     }
    ...                 }
    ...             }
    ...         }
    ...     }
    ...
    ...     @bridge.fragment
    ...     def name(self):
    ...         """ Name data """

Uh, that was verbose, the good part is that ``after`` the bulky class is
written we can write lean code using that class. Let's see how this works::

    >>> john = Person()
    >>> john.name.first = "John"
    >>> john.name.last = "Doe"
    >>> john.name.full
    'John Doe'
    >>> john.value
    {'name': {'last': 'Doe', 'first': 'John'}}

Did you notice this was a JSON object? Nice eh :-)

That's it

