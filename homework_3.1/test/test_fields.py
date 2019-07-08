import unittest
import api

from datetime import datetime
from test.utils import cases


class TestCharBaseField(unittest.TestCase):

    def setUp(self):
        self.field = api.CharBaseField(required=False, nullable=True)

    @cases(['value', '', None])
    def test_valid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertTrue(is_valid)

    @cases([12312, {}, []])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)


class TestPhoneBaseField(unittest.TestCase):

    def setUp(self):
        self.field = api.PhoneBaseField(required=False, nullable=True)

    @cases(['71234567890', 71234567890, None, ''])
    def test_valid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertTrue(is_valid)

    @cases(['+7123456789', 7123456789, 81234567890])
    def test_invalid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertFalse(is_valid)

    @cases([{}, []])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)


class TestEmailField(unittest.TestCase):

    def setUp(self):
        self.field = api.EmailField(required=False, nullable=True)

    @cases(['@', 'some@email.com', '', None])
    def test_valid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertTrue(is_valid, value)

    @cases(['some_email.com'])
    def test_invalid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertFalse(is_valid)

    @cases([{}, [], 3])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)


class TestDateField(unittest.TestCase):

    def setUp(self):
        self.field = api.DateField(required=False, nullable=True)

    @cases(['24.03.1990', '', None])
    def test_valid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertTrue(is_valid, value)

    @cases(['1990.03.24'])
    def test_invalid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertFalse(is_valid)

    @cases([{}, [], 3])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)
