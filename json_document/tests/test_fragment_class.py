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

"""Unit tests for fragment classes."""

from unittest2 import TestCase

from json_document.document import DocumentFragment


class DocumentFragmentClassTests(TestCase):
    """Tests related to fragment classes."""

    def test_getitem_uses_sub_value_class_from_object_property(self):

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
        self.assertIsInstance(fragment["item"], SpecialDocumentFragment)
        self.assertEqual(fragment["item"].value, "value")
        self.assertIsNotNone(fragment["item"].schema)

    def test_getitem_uses_sub_value_class_from_array(self):

        class SpecialDocumentFragment(DocumentFragment):
            pass

        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=[{"foo": "bar"}],
            item=None,
            schema={
                "type": "array",
                "items": {
                    "__fragment_cls": SpecialDocumentFragment,
                    "type": "object",
                    "properties": {
                        "foo": {"type": "string"}}}})
        self.assertIsInstance(fragment[0], SpecialDocumentFragment)
        self.assertIsInstance(fragment[0]["foo"], DocumentFragment)
        self.assertNotIsInstance(fragment[0]["foo"], SpecialDocumentFragment)
        self.assertEqual(fragment[0]["foo"].value, "bar")
        self.assertIsNotNone(fragment[0].schema)
        self.assertIsNotNone(fragment[0]["foo"].schema)
        self.assertIn("foo", fragment[0].schema.properties)

    def test_getitem_uses_sub_value_class_from_array_member_property(self):

        class SpecialDocumentFragment(DocumentFragment):
            pass

        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=[{"foo": "bar"}],
            item=None,
            schema={
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "foo": {
                            "__fragment_cls": SpecialDocumentFragment}}}})
        self.assertIsInstance(fragment[0], DocumentFragment)
        self.assertNotIsInstance(fragment[0], SpecialDocumentFragment)
        self.assertIsInstance(fragment[0]["foo"], SpecialDocumentFragment)
        self.assertEqual(fragment[0]["foo"].value, "bar")
        self.assertIsNotNone(fragment[0].schema)
        self.assertIsNotNone(fragment[0]["foo"].schema)
        self.assertIn("foo", fragment[0].schema.properties)

    def test_getitem_uses_sub_value_classes_from_arrays(self):

        class SpecialDocumentFragment(DocumentFragment):
            pass

        class SpecialDocumentFragment2(DocumentFragment):
            pass

        fragment = DocumentFragment(
            document=None,
            parent=None,
            value=[{"foo": [{"foo2": "bar"}]}],
            item=None,
            schema={
                "type": "array",
                "items": {
                    "__fragment_cls": SpecialDocumentFragment,
                    "type": "object",
                    "properties": {
                        "foo": {
                            "type": "array",
                            "items": {
                                "__fragment_cls": SpecialDocumentFragment2,
                                "type": "object",
                                "properties": {
                                    "foo2": {"type": "string"}}}}}}})
        self.assertIsInstance(fragment[0], SpecialDocumentFragment)
        self.assertIsInstance(fragment[0]["foo"], DocumentFragment)
        self.assertIsInstance(fragment[0]["foo"][0], SpecialDocumentFragment2)
        self.assertEqual(fragment[0]["foo"][0]["foo2"].value, "bar")
        self.assertIsNotNone(fragment[0].schema)
        self.assertIsNotNone(fragment[0]["foo"].schema)
        self.assertIsNotNone(fragment[0]["foo"][0].schema)
        self.assertIsNotNone(fragment[0]["foo"][0]["foo2"].schema)
        self.assertIn("foo", fragment[0].schema.properties)
        self.assertIn("foo2", fragment[0]["foo"][0].schema.properties)
