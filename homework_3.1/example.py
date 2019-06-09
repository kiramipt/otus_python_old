class ValidateType:

    def __init__(self, type):
        self.name = None
        self.type = type

    def __get__(self, inst, cls):

        if inst is None:
            return self
        else:
            return inst.__dict__.get('_' + self.name, None)

    def __set__(self, inst, value):
        if not isinstance(value, self.type):
            raise TypeError('%s must be of type(s) %s (got %r)' % (self.name, self.type, value))
        else:
            inst.__dict__['_' + self.name] = value


class Validator(type):

    def __new__(mcs, name, bases, dct):

        for name, attr in dct.items():
            if isinstance(attr, ValidateType):
                attr.name = name

        return super().__new__(mcs, name, bases, dct)


class Person(metaclass=Validator):

    weight = ValidateType(int)
    age = ValidateType(int)
    name = ValidateType(str)


if __name__ == '__main__':

    p = Person()
    p.weight = 9

    print(p.weight)
    print(dir(p))

    # print(p.weight)
    # print(p.age)
    # print(p.name)



