#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import datetime
import logging
import hashlib
import uuid

import re

from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from abc import ABCMeta, abstractmethod

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class Field(metaclass=ABCMeta):
    """
    Abstract class for field validating
    """

    def __init__(self, required=False, nullable=False):
        self.required = required
        self.nullable = nullable

    @abstractmethod
    def validate(self, value, valid_type=()):
        """
        Validate field value
        """
        # check if value is None and field is required
        if (value is None) and (self.required is True):
            raise ValueError(f"Field is required: '{value}'")

        # check if value is null and field is not nullable
        if (bool(value) is False) and (self.nullable is False):
            raise ValueError(f"Field must be not nullable: '{value}'")

        # check if field type in valid_type_list
        checked_valid_type_list = [isinstance(value, _type) for _type in valid_type]
        if len(checked_valid_type_list) != 0 and sum(checked_valid_type_list) == 0:
            raise TypeError(f"Field must be in {valid_type}. Your type is: {type(value)}")


class CharField(Field):
    """
    Validate char field

    Char field value should:
    * be field
    * be instance of str
    """
    def validate(self, value, valid_type_list=()):
        # call parent validate method
        super().validate(value, valid_type=(str))


class ArgumentsField(Field):
    """
    Validate arguments field

    Arguments field value should:
    * be field
    * be instance of dict
    """
    def validate(self, value, valid_type_list=()):
        # call parent validate method
        super().validate(value, valid_type=(dict,))


class EmailField(CharField):
    """
    Validate email field

    Email field value should:
    * be char field
    * contain '@' symbol
    """
    def validate(self, value, valid_type=()):
        # call parent validate method
        super().validate(value)

        # validate email
        if '@' not in value:
            raise ValueError(f"Not correct email address, should contain '@' symbol: '{value}'")


class PhoneField(Field):
    """
    Validate phone field

    Phone field value should:
    * be a string or integer
    * consist of 11 digits
    * start with 7
    """
    def validate(self, value, valid_type=()):
        # call parent validate method
        super().validate(value, valid_type=(str, int))

        # check that value look like phone number
        if not str(value).startswith("7") and len(value) == 11:
            raise ValueError(f"Not correct phone number, should be 11 digits and start with 7: '{value}'")


class DateField(CharField):
    """
    Validate date field

    Date field value should:
    * be a char field
    * match to 'DD.MM.YYYY' format
    """
    def validate(self, value, valid_type=()):
        # call parent validate method
        super().validate(value)

        # check that value is in date format
        try:
            datetime.datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            raise ValueError(f"Incorrect data format, should be 'DD.MM.YYYY': {value}")


class BirthDayField(DateField):
    """
    Validate birthday field

    Birthday field value should:
    * be a date field
    * be less then 70 years and greater than 0
    """
    def validate(self, value, valid_type=()):
        # call parent validate method
        super().validate(value)

        # check birthday
        birthday_datetime = datetime.datetime.strptime(value, '%d.%m.%Y')
        current_datetime = datetime.datetime.now()
        age_in_years = (current_datetime - birthday_datetime).days / 365
        if age_in_years <= 0 or age_in_years >= 70:
            raise ValueError(f"Incorrect birthday date, should be not greater than 70 "
                             f"and greater than 0: {age_in_years}")


class GenderField(Field):
    """
    Validate gender field

    Gender field value should:
    * be a field
    * be integer
    * be in [0, 1, 2]: unknown - 0, male - 1, female - 2
    """
    def validate(self, value, valid_type=()):
        # call parent validate method
        super().validate(value, valid_type=(int,))

        # check gender values
        if value not in [0, 1, 2]:
            raise ValueError(f"Incorrect gender, should be in [0, 1, 2]: {value}")


class ClientIDsField(Field):
    """
    Validate client_ids field

    ClientIDs field value should:
    * be a field
    * be array of integers
    * be non empty
    """
    def validate(self, value, valid_type=()):
        # call parent validate method
        super().validate(value, valid_type=(list, tuple))

        # check that array is non empty
        if not value:
            raise ValueError(f"Incorrect client_ids, should be non empty array: {value}")

        # check that all values in array is integers
        if not all(isinstance(v, int) for v in value):
            raise ValueError(f"Incorrect client_ids, should be list of integers: {value}")


class ClientsInterestsRequest:
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest:
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


class MethodRequest:
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    response, code = None, None
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
