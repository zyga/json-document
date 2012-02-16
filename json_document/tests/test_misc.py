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
json_document.tests
-------------------

Unit tests for this package
"""

from StringIO import StringIO
from decimal import Decimal

from json_schema_validator.errors import ValidationError
from simplejson import OrderedDict
from testtools import TestCase, ExpectedException

from json_document.document import (
    DefaultValue,
    Document,
    DocumentFragment,
    DocumentPersistence)
from json_document.serializers import JSON
from json_document import bridge


class JSONTests(TestCase):
    """
    Various tests checking how JSON.load() and loads() operate
    """

    def setUp(self):
        super(JSONTests, self).setUp()
        self.text = ('{"format": "Dashboard Bundle Format 1.0", '
                     '"test_runs": []}')
        self.stream = StringIO(self.text)
        self.expected_doc = {
            "format": "Dashboard Bundle Format 1.0",
            "test_runs": []}
        self.expected_keys = ["format", "test_runs"]

    def test_loads__return_value(self):
        doc = JSON.loads(self.text)
        self.assertEqual(doc, self.expected_doc)

    def test_load__return_value(self):
        doc = JSON.load(self.stream)
        self.assertEqual(doc, self.expected_doc)

    def test_loads__with_enabled_retain_order__key_order(self):
        doc = JSON.loads(self.text, retain_order=True)
        observed_keys = doc.keys()
        self.assertEqual(observed_keys, self.expected_keys)

    def test_load__with_enabled_retain_order__key_order(self):
        doc = JSON.load(self.stream, retain_order=True)
        observed_keys = doc.keys()
        self.assertEqual(observed_keys, self.expected_keys)

    def test_loads__with_enabled_retain_order__dict_class(self):
        doc = JSON.loads(self.text, retain_order=True)
        observed_impl = type(doc)
        # Note:    VVV
        self.assertNotEqual(observed_impl, dict)
        #          ^^^
        # The returned object is _not_ a plain dictionary

    def test_load__with_enabled_retain_order__dict_class(self):
        doc = JSON.load(self.stream, retain_order=True)
        observed_impl = type(doc)
        # Note:    VVV
        self.assertNotEqual(observed_impl, dict)
        # The returned object is _not_ a plain dictionary

    def test_loads__with_disabled_retain_order__dict_class(self):
        doc = JSON.loads(self.text, retain_order=False)
        expected_impl = dict
        observed_impl = type(doc)
        self.assertEqual(observed_impl, expected_impl)

    def test_load__with_disabled_retain_order__dict_class(self):
        doc = JSON.load(self.stream, retain_order=False)
        expected_impl = dict
        observed_impl = type(doc)
        self.assertEqual(observed_impl, expected_impl)


class JSONDumpTests(TestCase):
    """
    Sanity checks for various serialization options
    """

    def setUp(self):
        super(JSONDumpTests, self).setUp()
        self.doc = OrderedDict([
            ("test_runs", []),
            ("format", "Dashboard Bundle Format 1.0"),
        ])
        self.expected_readable_text = (
            '{\n  "test_runs": [], \n  "format": '
            '"Dashboard Bundle Format 1.0"\n}')
        self.expected_readable_sorted_text = (
            '{\n  "format": "Dashboard Bundle Format 1.0",'
            ' \n  "test_runs": []\n}')
        self.expected_compact_text = (
            '{"test_runs":[],"format":"Dashboard Bundle Format 1.0"}')
        self.expected_compact_sorted_text = (
            '{"format":"Dashboard Bundle Format 1.0","test_runs":[]}')

    def test_dumps_produces_readable_ouptut(self):
        observed_text = JSON.dumps(self.doc, human_readable=True)
        self.assertEqual(observed_text, self.expected_readable_text)

    def test_dumps_produces_readable_sorted_ouptut(self):
        observed_text = JSON.dumps(
            self.doc, human_readable=True, sort_keys=True)
        self.assertEqual(observed_text, self.expected_readable_sorted_text)

    def test_dumps_produces_compact_ouptut(self):
        observed_text = JSON.dumps(self.doc, human_readable=False)
        self.assertEqual(observed_text, self.expected_compact_text)

    def test_dumps_produces_compact_sorted_ouptut(self):
        observed_text = JSON.dumps(
            self.doc, human_readable=False, sort_keys=True)
        self.assertEqual(observed_text, self.expected_compact_sorted_text)

    def test_dump_produces_readable_output(self):
        stream = StringIO()
        JSON.dump(stream, self.doc, human_readable=True)
        observed_text = stream.getvalue()
        self.assertEqual(observed_text, self.expected_readable_text)

    def test_dump_produces_compact_output(self):
        stream = StringIO()
        JSON.dump(stream, self.doc, human_readable=False)
        observed_text = stream.getvalue()
        self.assertEqual(observed_text, self.expected_compact_text)

    def test_dump_produces_readable_sorted_output(self):
        stream = StringIO()
        JSON.dump(stream, self.doc, human_readable=True, sort_keys=True)
        observed_text = stream.getvalue()
        self.assertEqual(observed_text, self.expected_readable_sorted_text)

    def test_dump_produces_compact_sorted_output(self):
        stream = StringIO()
        JSON.dump(stream, self.doc, human_readable=False, sort_keys=True)
        observed_text = stream.getvalue()
        self.assertEqual(observed_text, self.expected_compact_sorted_text)


class JSONParsingTests(TestCase):
    """
    Sanity checks for deserialization options
    """

    def test_loader_uses_decimal_to_parse_numbers(self):
        text = """
        {
            "number": 1.5
        }
        """
        doc = JSON.loads(text)
        number = doc["number"]
        self.assertEqual(number, Decimal("1.5"))
        self.assertTrue(isinstance(number, Decimal))

    def test_dumper_can_dump_decimals(self):
        doc = {
            "format": "Dashboard Bundle Format 1.0",
            "test_runs": [
                {
                    "test_id": "NOT RELEVANT",
                    "analyzer_assigned_date": "2010-11-14T01:03:06Z",
                    "analyzer_assigned_uuid": "NOT RELEVANT",
                    "time_check_performed": False,
                    "test_results": [
                        {
                            "test_case_id": "NOT RELEVANT",
                            "result": "unknown",
                            "measurement": Decimal("1.5")}]}]}
        text = JSON.dumps(doc)
        self.assertIn("1.5", text)


class FakeDocument(object):

    _revision = None

    def _bump_revision(self):
        self._revision = object()

    @property
    def revision(self):
        return self._revision


class DocumentFragmentDefaultValueTests(TestCase):
    """
    Tests related to defaults system
    """

    def test_is_default_with_value_equal_to_default_from_schema(self):
        fragment = DocumentFragment(
            None, None, "value", None, {"default": "value"})
        self.assertFalse(fragment.is_default)

    def test_is_defalt_with_DefaultValue(self):
        fragment = DocumentFragment(
            None, None, DefaultValue, None, {"default": "value"})
        self.assertTrue(fragment.is_default)

    def test_revert_to_default(self):
        document = FakeDocument()
        fragment = DocumentFragment(
            document, None, "value", None, {"default": "value"})
        fragment.revert_to_default()
        self.assertIs(fragment._value, DefaultValue)

    def test_revert_to_default_marks_document_as_dirty(self):
        document = FakeDocument()
        start_revision = document.revision
        fragment = DocumentFragment(
            document, None, "value", None, {"default": "value"})
        fragment.revert_to_default()
        self.assertNotEqual(document.revision, start_revision)

    def test_default_value(self):
        fragment = DocumentFragment(
            None, None, "other value", None, {"default": "value"})
        self.assertEqual(fragment.default_value, "value")


class DocumentFragmentMiscPropertiesTests(TestCase):
    """
    Miscellaneous tests
    """

    def test_document_works(self):
        document = object()
        fragment = DocumentFragment(document, None, {})
        self.assertIs(fragment._document, document)
        self.assertIs(fragment.document, document)

    def test_parent_works(self):
        parent = object()
        fragment = DocumentFragment(None, parent, None, {})
        self.assertIs(fragment._parent, parent)
        self.assertIs(fragment.parent, parent)


class DocumentFragmentOrhpanTests(TestCase):
    """
    Tests related to orphaned fragments
    """

    def test_is_orphaned_for_typical_fragments(self):
        document = object()
        parent = object()
        value = object()
        item = "item"
        fragment = DocumentFragment(document, parent, value, item)
        self.assertFalse(fragment.is_orphaned)

    def test_is_orphaned_for_root_fragment(self):
        document = object()
        parent = None
        value = object()
        item = None
        fragment = DocumentFragment(document, parent, value, item)
        self.assertFalse(fragment.is_orphaned)

    def test_is_orphaned_for_orphans(self):
        document = None
        parent = None
        value = object()
        item = "item"
        fragment = DocumentFragment(document, parent, value, item)
        self.assertTrue(fragment.is_orphaned)


class DocumentFragmentValueReadTests(TestCase):
    """
    Tests related to reading values
    """

    def test_value_uses_schema_to_find_default_value(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=DefaultValue,
            item=None,
            schema={"default": "default value"})
        self.assertEqual(fragment.value, "default value")

    def test_value_returns_normal_values(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value="value")
        self.assertEqual(fragment.value, "value")

    def test_value_returns_None_normally(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=None)
        self.assertEqual(fragment.value, None)


class DocumentFragmentSetTests(TestCase):
    """
    Tests related to writing values
    """

    def setUp(self):
        super(DocumentFragmentSetTests, self).setUp()
        self.document = FakeDocument()
        self.start_revision = self.document.revision

    def test_setitem_mutates_value(self):
        fragment = DocumentFragment(
            document=self.document,
            parent=None,
            value={})
        fragment["item"] = "value"
        self.assertEqual(fragment._value, {"item": "value"})

    def test_setitem_bumps_revision(self):
        fragment = DocumentFragment(
            document=self.document,
            parent=None,
            value={})
        fragment["item"] = "value"
        self.assertNotEqual(self.document.revision, self.start_revision)

    def test_overwriting_setitem_mutates_value(self):
        fragment = DocumentFragment(
            document=self.document,
            parent=None,
            value={"item": "value"})
        sub_fragment = fragment["item"]
        self.assertEqual(sub_fragment.value, "value")
        fragment["item"] = "new value"
        self.assertEqual(sub_fragment.value, "new value")
        self.assertEqual(fragment._value, {"item": "new value"})

    def test_overwriting_setitem_bumps_revision(self):
        fragment = DocumentFragment(
            document=self.document,
            parent=None,
            value={"item": "value"})
        fragment["item"] = "new value"
        self.assertNotEqual(self.document.revision, self.start_revision)

    def test_overwriting_setitem_with_same_value_retains_revision(self):
        fragment = DocumentFragment(
            document=self.document,
            parent=None,
            value={"item": "value"})
        fragment["item"] = "value"
        self.assertEqual(self.document.revision, self.start_revision)


class DocumentFragmentGetTests(TestCase):
    """
    Tests related to referencing fragments
    """

    def test_getitem_raises_item_error_for_missing_sub_values(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={})
        self.assertRaises(KeyError, fragment.__getitem__, "item")

    def test_getitem_uses_existing_sub_value(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={"item": "value"})
        self.assertEqual(fragment["item"]._value, "value")
        self.assertIn("item", fragment._fragment_cache)

    def test_getitem_uses_default_value_for_missing_elements_with_schema(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={},
            item=None,
            schema={
                "type": "object",
                "properties": {
                    "item": {
                        "default": "default value"}}})
        self.assertIs(fragment["item"]._value, DefaultValue)
        self.assertIn("item", fragment._fragment_cache)

    def test_getitem_passes_sub_schema_propertly_when_sub_value_exists(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={
                "item": "value"},
            item=None,
            schema={
                "type": "object",
                "properties": {
                    "item": {
                        "default": "default value"}}})
        self.assertIs(
            fragment["item"]._schema,
            fragment.schema.properties['item'])

    def test_getitem_passes_sub_item(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={
                "item": "value"})
        self.assertEqual(fragment["item"]._item, "item")

    def test_getitem_passes_sub_schema_when_sub_value_is_missing(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={},
            item=None,
            schema={
                "type": "object",
                "properties": {
                    "item": {
                        "default": "default value"}}})
        self.assertIs(
            fragment["item"]._schema,
            fragment.schema.properties['item'])

    def test_get_passes_sub_schema_properly_when_no_schema_is_around(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={"item": "value"},
            item=None,
            schema={"type": "object"})
        # This is coming from additionalProperties.default schema which allows
        # any objects.
        self.assertEqual(fragment["item"]._schema, {})

    def test_getitem_uses_sub_value_class_from_schema(self):

        class SpecialDocumentFragment(DocumentFragment):
            pass

        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={
                "item": "value"},
            item=None,
            schema={
                "type": "object",
                "properties": {
                    "item": {
                        "__fragment_cls": SpecialDocumentFragment}}})
        self.assertIsInstance(fragment["item"], DocumentFragment)


class DocumentFragmentLengthTests(TestCase):
    """
    Tests related to collection size methods
    """

    def test_length_works_on_lists(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=[1, 2, 3])
        self.assertIs(len(fragment), 3)

    def test_length_works_on_dictionaries(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={'one': 1, 'two': 2})
        self.assertIs(len(fragment), 2)

    def test_length_works_on_strings(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value="1234")
        self.assertIs(len(fragment), 4)

    def test_length_raises_type_error_on_ints(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=1)
        self.assertRaises(TypeError, len, fragment)

    def test_length_raises_type_error_on_bools(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=True)
        self.assertRaises(TypeError, len, fragment)

    def test_length_raises_type_error_on_none(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=None)
        self.assertRaises(TypeError, len, fragment)


class DocumentFragmentContainsTests(TestCase):
    """
    Tests related to collection membership methods
    """

    def test_contains_works_on_lists(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=[1, 2, 3])
        self.assertIn(2, fragment)

    def test_contains_works_on_dictionaries(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={'one': 1, 'two': 2})
        self.assertIn('two', fragment)

    def test_contains_works_on_strings(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value="1234")
        self.assertIn("3", fragment)

    def test_contains_raises_type_error_on_ints(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=1)
        self.assertRaises(TypeError, fragment.__contains__, 1)

    def test_contains_raises_type_error_on_bools(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=True)
        self.assertRaises(TypeError, fragment.__contains__, None)

    def test_contains_raises_type_error_on_none(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=None)
        self.assertRaises(TypeError, fragment.__contains__, None)


class DocumentFragmentIterTests(TestCase):
    """
    Tests related to collection iteration
    """

    def test_iter_works_on_lists(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=[1, 2, 3])
        self.assertEqual([item.value for item in fragment], [1, 2, 3])

    def test_iter_works_on_dictionaries(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value={'one': 1, 'two': 2})
        self.assertEqual(sorted([item.value for item in fragment]), [1, 2])

    def test_iter_raises_type_error_on_strings(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value="1234")
        self.assertRaises(TypeError, iter, fragment)

    def test_iter_raises_type_error_on_ints(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=1)
        self.assertRaises(TypeError, iter, fragment)

    def test_iter_raises_type_error_on_bools(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=True)
        self.assertRaises(TypeError, iter, fragment)

    def test_iter_raises_type_error_on_none(self):
        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=None)
        self.assertRaises(TypeError, iter, fragment)


class DocumentTests(TestCase):
    """
    Tests related to the Document class
    """

    def test_document_has_initial_revision(self):
        doc = Document({})
        self.assertEqual(doc.revision, 0)

    def test_document_is_empty_initially(self):
        doc = Document({})
        self.assertEqual(doc._value, {})

    def test_document_is_valid_initially(self):
        doc = Document({})
        try:
            doc.validate()
        except ValidationError:
            self.fail("Document was not valid")

    def test_document_initial_schema(self):
        doc = Document({})
        self.assertEqual(doc.document_schema, {"type": "any"})

    def test_document_is_its_own_document(self):
        doc = Document({})
        self.assertIs(doc._document, doc)

    def test_document_has_no_item(self):
        doc = Document({})
        self.assertIs(doc._item, None)


class DocumentUsageTests(TestCase):
    """
    Tests related to using document features
    """

    def test_deeply_nested_defaults_unwind(self):
        doc = Document(
            value={},
            schema={
                "type": "object",
                "default": {},
                "properties": {
                    "a": {
                        "type": "object",
                        "default": {},
                        "properties": {
                            "b": {
                                "type": "object",
                                "default": {},
                                "properties": {
                                    "c": {
                                        "type": "integer",
                                        "default": 0}}}}}}})
        self.assertEqual(doc._value, {})
        self.assertTrue(doc['a']['b']['c'].is_default)
        self.assertEqual(doc['a']['b']['c'].value, 0)
        self.assertEqual(doc._value, {})
        doc['a']['b']['c'].value = 0
        self.assertFalse(doc['a']['b']['c'].is_default)
        self.assertEqual(doc._value, {'a': {'b': {'c': 0}}})

    def test_is_orphaned(self):
        doc = Document({})
        doc["foo"] = "value"
        foo = doc["foo"]
        doc.value = {}
        self.assertTrue(foo.is_orphaned)


class DecoratorTests(TestCase):
    """
    Tests related to document fragment decorators
    """

    class TestDocument(Document):

        @bridge.fragment
        def bridge_to_fragment(self):
            """fragment"""
            pass

        @bridge.readonly
        def bridge_to_readonly(self):
            """readonly"""
            pass

        @bridge.readwrite
        def bridge_to_readwrite(self):
            """readwrite"""
            pass

    def setUp(self):
        super(DecoratorTests, self).setUp()
        self.doc = self.TestDocument({})

    def test_fragment(self):
        obj = object()
        self.doc["bridge_to_fragment"] = obj
        self.assertIsInstance(self.doc.bridge_to_fragment, DocumentFragment)
        self.assertIs(self.doc.bridge_to_fragment.value, obj)

    def test_readonly(self):
        obj = object()
        self.doc["bridge_to_readonly"] = obj
        self.assertIs(self.doc.bridge_to_readonly, obj)
        with ExpectedException(AttributeError, "can't set attribute"):
            self.doc.bridge_to_readonly = object()

    def test_readwrite(self):
        obj1 = object()
        obj2 = object()
        self.doc["bridge_to_readwrite"] = obj1
        self.assertIs(self.doc.bridge_to_readwrite, obj1)
        self.doc.bridge_to_readwrite = obj2
        self.assertIs(self.doc.bridge_to_readwrite, obj2)
