import unittest
import api

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

    @cases(['+7123456789', 7123456789, 81234567890, 'abd'])
    def test_invalid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertFalse(is_valid)

    @cases([{}, [], 1.1])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)


class TestEmailField(unittest.TestCase):

    def setUp(self):
        self.field = api.EmailField(required=False, nullable=True)

    @cases(['@', 'some@email.com', '', None])
    def test_valid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertTrue(is_valid, value)

    @cases(['some_email.com', '1asd1'])
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

    @cases(['1990.03.24', '03.24.1990'])
    def test_invalid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertFalse(is_valid)

    @cases([{}, [], 3])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)


class TestBirthDayField(unittest.TestCase):

    def setUp(self):
        self.field = api.BirthDayField(required=False, nullable=True)

    @cases(['24.03.1990', '', None])
    def test_valid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertTrue(is_valid, value)

    @cases(['1990.03.24', '03.24.1990'])
    def test_invalid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertFalse(is_valid)

    @cases([{}, [], 3])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)


class TestGenderBaseField(unittest.TestCase):

    def setUp(self):
        self.field = api.GenderBaseField(required=False, nullable=True)

    @cases([0, 1, 2, None])
    def test_valid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertTrue(is_valid, value)

    @cases([3, -1, 777])
    def test_invalid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertFalse(is_valid)

    @cases([{}, [], 3.1, 'some test'])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)


class TestArgumentsBaseField(unittest.TestCase):

    def setUp(self):
        self.field = api.ArgumentsBaseField(required=True, nullable=True)

    @cases([{}, {1: 2, 3: 4}])
    def test_valid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertTrue(is_valid, value)

    @cases([[], 3, 'test'])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)


class TestClientIDsBaseField(unittest.TestCase):

    def setUp(self):
        self.field = api.ClientIDsBaseField(required=True, nullable=False)

    @cases([[0, 1, 2]])
    def test_valid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertTrue(is_valid, value)

    @cases([[], [0, 1.1], [2.2]])
    def test_invalid_value(self, value):
        is_valid, errors_msg = self.field.is_valid(value)
        self.assertFalse(is_valid)

    @cases([3.1, 'some test'])
    def test_invalid_type(self, value):
        self.assertRaises(TypeError, self.field.validate, value)

    @cases([[]])
    def test_empty_value(self, value):
        self.assertRaises(ValueError, self.field.validate, value)
