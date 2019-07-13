import argparse
import datetime
import json
import hashlib
import logging
import uuid

from abc import ABCMeta, abstractmethod
from http.server import BaseHTTPRequestHandler, HTTPServer

from store import Store, RedisStorage
from scoring import get_interests, get_score

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


class BaseField(metaclass=ABCMeta):
    """
    Base abstract class for field validating
    """

    def __init__(self, required=False, nullable=False):

        self.required = required
        self.nullable = nullable
        self.name = None

    def __get__(self, inst, cls):

        if inst is None:
            return self
        else:
            return inst.__dict__.get('_' + self.name, None)

    def __set__(self, inst, value):
        inst.__dict__['_' + self.name] = value

    @abstractmethod
    def validate(self, value, valid_type_list=()):
        """
        Validate field value
        :param value: value which we want to validate
        :param valid_type_list: if it not empty, than at least for one type should be: isinstance(value, type) == True
        :type valid_type_list: tuple
        """
        # check if value is None and field is required
        if (value is None) and (self.required is True):
            raise ValueError(f"Field is required: '{value}'")

        # check if value is null and field is not nullable
        if (bool(value) is False) and (self.nullable is False):
            raise ValueError(f"Field must be not nullable: '{value}'")

        # check if field type in valid_type
        if value is not None:
            checked_valid_type = [isinstance(value, _type) for _type in valid_type_list]
            if len(checked_valid_type) != 0 and sum(checked_valid_type) == 0:
                raise TypeError(f"Field must be in {valid_type_list}. Your type is: {type(value)}")

    def is_valid(self, value):
        """
        Check that field value is valid

        :param value: field value which we want to validate
        """

        try:
            self.validate(value)
        except Exception as e:
            error_msg = repr(e)
        else:
            error_msg = ''

        return not error_msg, error_msg


class CharBaseField(BaseField):
    """
    Validate char field
    Char field value should:
    * be field
    * be instance of str
    """

    def validate(self, value, valid_type_list=()):
        super().validate(value, valid_type_list=(str,))


class PhoneBaseField(BaseField):
    """
    Validate phone field
    Phone field value should:
    * be a string or integer
    * consist of 11 digits
    * start with 7
    """

    def validate(self, value, valid_type_list=()):
        super().validate(value, valid_type_list=(str, int))

        # check that value looks like phone number
        if value and not str(value).startswith("7"):
            raise ValueError(f"Not correct phone number, should start with 7: '{value}'")
        if value and not len(str(value)) == 11:
            raise ValueError(f"Not correct phone number, should be 11 digits: '{value}'")


class EmailField(CharBaseField):
    """
    Validate email field
    Email field value should:
    * be char field
    * contain '@' symbol
    """

    def validate(self, value, valid_type_list=()):
        super().validate(value)

        # validate email
        if value and '@' not in value:
            raise ValueError(f"Not correct email address, email should contain '@' symbol: '{value}'")


class DateField(CharBaseField):
    """
    Validate date field
    Date field value should:
    * be a char field
    * match to 'DD.MM.YYYY' format
    """

    def validate(self, value, valid_type_list=()):
        super().validate(value)

        # check that value is in right date format
        if value:
            try:
                datetime.datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                is_date_valid = False
            else:
                is_date_valid = True

            if not is_date_valid:
                raise ValueError(f"Incorrect date format, should be 'DD.MM.YYYY': {value}")


class BirthDayField(DateField):
    """
    Validate birthday field
    Birthday field value should:
    * be a date field
    * be less then 70 years and greater than 0
    """

    def validate(self, value, valid_type_list=()):
        super().validate(value)

        # check birthday
        if value:
            birthday_datetime = datetime.datetime.strptime(value, '%d.%m.%Y')
            current_datetime = datetime.datetime.now()
            age_in_years = (current_datetime - birthday_datetime).days / 365
            is_birthday_valid = (0 <= age_in_years <= 70)

            if not is_birthday_valid:
                raise ValueError(f"Incorrect birthday date, should be not greater than 70 "
                                 f"and greater than 0: {age_in_years}")


class GenderBaseField(BaseField):
    """
    Validate gender field
    Gender field value should:
    * be a field
    * be integer
    * be in [0, 1, 2]: unknown - 0, male - 1, female - 2
    """

    def validate(self, value, valid_type_list=()):
        super().validate(value, valid_type_list=(int,))

        # check gender values
        if value and value not in GENDERS:
            raise ValueError(f"Incorrect gender, should be in [0, 1, 2]: {value}")


class ArgumentsBaseField(BaseField):
    """
    Validate arguments field
    Arguments field value should:
    * be field
    * be instance of dict
    """

    def validate(self, value, valid_type_list=()):
        super().validate(value, valid_type_list=(dict,))


class ClientIDsBaseField(BaseField):
    """
    Validate client_ids field
    ClientIDs field value should:
    * be a field
    * be array of integers
    """

    def validate(self, value, valid_type=()):
        super().validate(value, valid_type_list=(list, tuple))

        # check that all values in array is integers
        if value and not all(isinstance(v, int) for v in value):
            raise ValueError(f"Incorrect client_ids, should be list of integers: {value}")


class MetaRequest(type):

    def __new__(mcs, name, bases, attrs):

        fields = []
        for field_name, field in attrs.items():
            if isinstance(field, BaseField):
                field.name = field_name
                fields.append(field_name)
        attrs['fields'] = fields

        return super().__new__(mcs, name, bases, attrs)


class BaseRequest(metaclass=MetaRequest):

    def __init__(self, request):

        self.errors = []
        for field_name in self.fields:
            field_value = request.get(field_name, None)
            setattr(self, field_name, field_value)
        self.validate()

    def validate(self):

        for field_name in self.fields:

            field_value = getattr(self, field_name, None)
            is_valid, error_msg = getattr(self.__class__, field_name).is_valid(field_value)

            if not is_valid:
                self.errors.append(f"{field_name} field is incorrect: {error_msg}")

    def is_valid(self):
        return not self.errors, '\n'.join(self.errors)


class ClientsInterestsRequest(BaseRequest):
    """
    Class for calling get interests api
    """

    client_ids = ClientIDsBaseField(required=True, nullable=False)
    date = DateField(required=False, nullable=True)

    def get_response(self, store, context, is_admin):

        result = {}
        for cid in self.client_ids:
            result[str(cid)] = get_interests(store, cid)

        context["nclients"] = len(self.client_ids)

        return result


class OnlineScoreRequest(BaseRequest):
    """
    Class for calling online score api
    """

    first_name = CharBaseField(required=False, nullable=True)
    last_name = CharBaseField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneBaseField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderBaseField(required=False, nullable=True)

    needed_pairs = [
        ['phone', 'email'],
        ['first_name', 'last_name'],
        ['gender', 'birthday']
    ]

    def validate(self):
        super().validate()
        is_anyone_pair_is_not_nullable = False
        for field_name_1, field_name_2 in self.needed_pairs:

            if getattr(self, field_name_1) is not None and getattr(self, field_name_2) is not None:
                is_anyone_pair_is_not_nullable = True

        if not is_anyone_pair_is_not_nullable:
            self.errors.append('OnlineScoreRequest: there is no required pair of values')

    def get_response(self, store, context, is_admin):

        if is_admin:
            result = 42
        else:
            result = get_score(
                store,
                self.phone,
                self.email,
                self.birthday,
                self.gender,
                self.first_name,
                self.last_name,
            )

        filled_field_names = [
            field_name
            for field_name in self.fields
            if getattr(self, field_name, None)
        ]
        context["has"] = ", ".join(filled_field_names)

        return {"score": result}


class MethodRequest(BaseRequest):
    """
    Class for request initialisation
    """

    account = CharBaseField(required=False, nullable=True)
    login = CharBaseField(required=True, nullable=True)
    token = CharBaseField(required=True, nullable=True)
    arguments = ArgumentsBaseField(required=True, nullable=True)
    method = CharBaseField(required=True, nullable=False)

    def is_admin(self):
        return self.login == ADMIN_LOGIN


def method_handler(request, context, store):
    """
    Function for request handling. Used for arguments validating and results returning.
    """
    handlers = {
        "online_score": OnlineScoreRequest,
        "clients_interests": ClientsInterestsRequest
    }

    # validate MethodRequest args
    methodrequest = MethodRequest(request["body"])
    is_valid, errors_msg = methodrequest.is_valid()
    if not is_valid:
        return errors_msg, INVALID_REQUEST

    # validate auth
    if not check_auth(methodrequest):
        return ERRORS[FORBIDDEN], FORBIDDEN

    # check if method exists
    if methodrequest.method not in handlers:
        msg = f"Method {methodrequest.method} is not defined"
        return msg, NOT_FOUND

    # validate handler args
    handler = handlers[methodrequest.method](request["body"].get("arguments", {}))
    is_valid, errors_msg = handler.is_valid()
    if not is_valid:
        return errors_msg, INVALID_REQUEST

    return handler.get_response(store, context, methodrequest.is_admin()), OK


class MainHTTPHandler(BaseHTTPRequestHandler):

    router = {
        "method": method_handler
    }
    store = Store(RedisStorage())

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        data_string = ''

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
        self.wfile.write(json.dumps(r).encode())
        return


def check_auth(request):

    if request.is_admin():
        msg = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
    else:
        msg = request.account + request.login + SALT

    digest = hashlib.sha512(msg.encode('utf-8')).hexdigest()

    if digest == request.token:
        return True
    return False


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--port', type=int, default=8080)
    parser.add_argument('-l', '--log',  default=None)
    args = parser.parse_args()

    logging.basicConfig(filename=args.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')

    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info(f"Starting server at {args.port}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
