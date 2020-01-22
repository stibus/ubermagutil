import numbers
import itertools
import collections
import numpy as np


class Descriptor:
    """Descriptor base class from which all descriptors in
    `ubermagutil.typesystem` are derived.

    Before setting the attribute value of a decorated class is allowed, certain
    type and value checks are performed. If they are not according to the
    specifications in the `__set__` method (defined in the derived class),
    `TypeError` or `ValueError` is raised. If `const=True` is passed when the
    class is instantiated, no value changes are allowed after the initial
    assignment. Deleting attributes of a decorated class is never allowed.

    Parameters
    ----------
    name : str
        Attribute name (the default is None). It must be a valid Python
        variable name.

    const : bool, optional
        If `const=True`, the attribute of the decorated class is
        constant and its value cannot be changed after the first set.

    Example
    -------
    1. Deriving a descriptor class from the base class `Descriptor`, which only
    allows positive integer values.

    >>> import ubermagutil.typesystem as ts
    ...
    >>> class PositiveInt(ts.Descriptor):
    ...     def __set__(self, instance, value):
    ...        if not isinstance(value, int):
    ...            raise TypeError('Allowed only type(value) == int.')
    ...        if value < 0:
    ...            raise ValueError('Allowed only value >= 0.')
    ...        super().__set__(instance, value)
    ...
    >>> @ts.typesystem(myattribute=PositiveInt)
    ... class DecoratedClass:
    ...     def __init__(self, myattribute):
    ...         self.myattribute = myattribute
    ...
    >>> dc = DecoratedClass(myattribute=5)
    >>> dc.myattribute
    5
    >>> dc.myattribute = 101  # valid set
    >>> dc.myattribute
    101
    >>> dc.myattribute = -1  # invalid set - negative value
    Traceback (most recent call last):
       ...
    ValueError: ...
    >>> dc.myattribute = 3.14  # invalid set - float value
    Traceback (most recent call last):
       ...
    TypeError: ...
    >>> dc.myattribute  # value has not beed affected by invalid sets
    101

    """
    def __init__(self, name=None, **kwargs):
        self.name = name
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __set__(self, instance, value):
        """If `self.const=True`, changing the value of a decorated class
        attribute after the initial set is not allowed.

        Raises
        ------
        AttributeError
            If changing the value of a decorated class attribute is attempted.

        Example
        -------
        1. Changing the value of a constant decorated class attribute.

        >>> import ubermagutil.typesystem as ts
        ...
        >>> @ts.typesystem(myattribute=ts.Descriptor(const=True))
        ... class DecoratedClass:
        ...     def __init__(self, myattribute):
        ...         self.myattribute = myattribute
        ...
        >>> dc = DecoratedClass(myattribute="John Doe")
        >>> dc.myattribute
        'John Doe'
        >>> dc.myattribute = 'Jane Doe'
        Traceback (most recent call last):
           ...
        AttributeError: ...

        """
        if hasattr(self, 'const'):
            if (self.name not in instance.__dict__ and self.const) or \
                not self.const:
                instance.__dict__[self.name] = value
            else:
                msg = f'Changing {self.name} not allowed.'
                raise AttributeError(msg)
        else:
            instance.__dict__[self.name] = value

    def __delete__(self, instance):
        """Deleting the decorated class attribute is never allowed.

        Raises
        ------
        AttributeError
            If deleting decorated class attribute is attempted.

        Example
        -------
        1. Deleting an attribute of a decorated class.

        >>> import ubermagutil.typesystem as ts
        ...
        >>> @ts.typesystem(myattribute=ts.Descriptor)
        ... class DecoratedClass:
        ...     def __init__(self, myattribute):
        ...         self.myattribute = myattribute
        ...
        >>> dc = DecoratedClass(myattribute="Nikola Tesla")
        >>> dc.myattribute
        'Nikola Tesla'
        >>> del dc.myattribute
        Traceback (most recent call last):
           ...
        AttributeError: ...

        """
        msg = f'Deleting {self.name} not allowed.'
        raise AttributeError(msg)


class Typed(Descriptor):
    """Descriptor allowing setting attributes only with values of a certain
    type.

    Parameters
    ----------
    expected_type : type
        Allowed type of value.

    Raises
    ------
    TypeError
        If `type(value) != expected_type`.

    Example
    -------
    1. Usage of Typed descriptor.

    >>> import ubermagutil.typesystem as ts
    ...
    >>> @ts.typesystem(myattribute=ts.Typed(expected_type=str))
    ... class DecoratedClass:
    ...     def __init__(self, myattribute):
    ...         self.myattribute = myattribute
    ...
    >>> dc = DecoratedClass(myattribute='Nikola Tesla')
    >>> dc.myattribute
    'Nikola Tesla'
    >>> dc.myattribute = 'Mihajlo Pupin'  # valid set
    >>> dc.myattribute
    'Mihajlo Pupin'
    >>> dc.myattribute = 3.14  # invalid set
    Traceback (most recent call last):
       ...
    TypeError: ...

    .. note::

           This class was derived from `ubermagutil.typesystem.Descriptor` and
           inherits its functionality.

    .. seealso:: :py:class:`~ubermagutil.typesystem.Descriptor`

    """
    def __set__(self, instance, value):
        if not isinstance(value, self.expected_type):
            msg = f'Cannot set {self.name} with {type(value)}.'
            raise TypeError(msg)
        super().__set__(instance, value)


class Scalar(Descriptor):
    """Descriptor allowing setting attributes only with scalars
    (`numbers.Real`).

    Parameters
    ----------
    expected_type : int or float type, optional
        Allowed type(value). It should be a subset of `numbers.Real`
        (e.g. `int`, `float`).
    positive : bool, optional
        If `positive=True`, value must be positive (>0).
    unsigned : bool, optional
        If `unsigned=True`, value must be unsigned (>=0).
    otherwise : type
        This type would also be accepted if specified. It has priority over
        other descriptor specification.

    Raises
    ------
    TypeError
        If `type(value)` is neither `numbers.Real` nor `expected_type` (if
        passed).
    ValueError
        If `value < 0` and `unsigned=True` is passed or `value <= 0` and
        `positive=True` is passed.

    Example
    -------
    1. Usage of the Scalar descriptor for defining a positive integer.

    >>> import ubermagutil.typesystem as ts
    ...
    >>> @ts.typesystem(myattribute=ts.Scalar(expected_type=int, positive=True))
    ... class DecoratedClass:
    ...     def __init__(self, myattribute):
    ...         self.myattribute = myattribute
    ...
    >>> dc = DecoratedClass(myattribute=5)
    >>> dc.myattribute
    5
    >>> dc.myattribute = 10  # valid set
    >>> dc.myattribute
    10
    >>> dc.myattribute = 3.14  # invalid set
    Traceback (most recent call last):
       ...
    TypeError: ...
    >>> dc.myattribute = 0  # invalid set
    Traceback (most recent call last):
       ...
    ValueError: ...
    >>> dc.myattribute  # the value was not affected by invalid sets
    10

    .. note::

           This class was derived from `ubermagutil.typesystem.Descriptor` and
           inherits its functionality.

    .. seealso:: :py:class:`~ubermagutil.typesystem.Descriptor`

    """
    def __set__(self, instance, value):
        if hasattr(self, 'otherwise'):
            if isinstance(value, self.otherwise):
                super().__set__(instance, value)
                return None  # prevent it going further
        if not isinstance(value, numbers.Real):
            msg = f'Cannot set {self.name} with {type(value)}.'
            raise TypeError(msg)
        if hasattr(self, 'expected_type'):
            if not isinstance(value, self.expected_type):
                msg = f'Cannot set {self.name} with {type(value)}.'
                raise TypeError(msg)
        if hasattr(self, 'unsigned'):
            if self.unsigned and value < 0:
                msg = f'Cannot set {self.name} with value = {value} < 0.'
                raise ValueError(msg)
        if hasattr(self, 'positive'):
            if self.positive and value <= 0:
                msg = f'Cannot set {self.name} with value = {value} <= 0.'
                raise ValueError(msg)
        super().__set__(instance, value)


class Vector(Descriptor):
    """Descriptor allowing setting attributes only with vectors (`list`,
    `tuple`, or `numpy.ndarray`) whose elements are of `numbers.Real` type.

    Parameters
    ----------
    component_type : int or float type, optional
        Type of the vector components. It should be a subset of `numbers.Real`
        (`int`, `float`).
    size : int, optional
        Size (length, number of elements) of the vector.
    positive : bool, optional
        If `positive=True`, values of all vector elements must be positive
        (>0).
    unsigned : bool, optional
        If `unsigned=True`, values of all vector components must be unsigned
        (>=0).
    otherwise : type
        This type would also be accepted if specified. It has priority over
        other descriptor specification.

    Raises
    ------
    TypeError
        If the `type(value)` is not `list`, `tuple`, or `numpy.ndarray` or if
        the type of vector components is neither `numbers.Real` nor
        `expected_type` (if passed).
    ValueError
        If vector component value is `value < 0` and `unsigned=True` or `value <=
        0` and `positive=True`.

    Example
    -------
    1. Usage of the Vector descriptor for defining a three-dimensional vector
    composed of only positive integer components.

    >>> import ubermagutil.typesystem as ts
    ...
    >>> @ts.typesystem(myattribute=ts.Vector(size=3, component_type=int,
    ...                                      positive=True))
    ... class DecoratedClass:
    ...     def __init__(self, myattribute):
    ...         self.myattribute = myattribute
    ...
    >>> dc = DecoratedClass(myattribute=(1, 2, 12))
    >>> dc.myattribute
    (1, 2, 12)
    >>> dc.myattribute = (10, 11, 12)  # valid set
    >>> dc.myattribute
    (10, 11, 12)
    >>> dc.myattribute = (11, 12)  # invalid set
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> dc.myattribute = (0, 1, 2)  # invalid set
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> dc.myattribute = (1, 3.14, 2)  # invalid set
    Traceback (most recent call last):
        ...
    TypeError: ...
    >>> dc.myattribute  # the value was not affected by invalid sets
    (10, 11, 12)

    .. note::

           This class was derived from `ubermagutil.typesystem.Descriptor` and
           inherits its functionality.

    .. seealso:: :py:class:`~ubermagutil.typesystem.Descriptor`

    """
    def __set__(self, instance, value):
        if hasattr(self, 'otherwise'):
            if isinstance(value, self.otherwise):
                super().__set__(instance, value)
                return None
        if not isinstance(value, (list, tuple, np.ndarray)):
            msg = f'Cannot set {self.name} with {type(value)}.'
            raise TypeError(msg)
        if not all(isinstance(i, numbers.Real) for i in value):
            msg = 'Allowed only type(value[i]) == number.Real.'
            raise TypeError(msg)
        if hasattr(self, 'size'):
            if len(value) != self.size:
                msg = f'Cannot set {self.name} with length {len(value)} value.'
                raise ValueError(msg)
        if hasattr(self, 'component_type'):
            if not all(isinstance(i, self.component_type) for i in value):
                msg = f'Allowed only type(value[i]) == {self.component_type}.'
                raise TypeError(msg)
        if hasattr(self, 'unsigned'):
            if self.unsigned and not all(i >= 0 for i in value):
                raise ValueError('Allowed only value[i] >= 0.')
        if hasattr(self, 'positive'):
            if self.positive and not all(i > 0 for i in value):
                raise ValueError('Allowed only value[i] > 0.')
        super().__set__(instance, value)


class Name(Descriptor):
    """Descriptor allowing setting attributes only with strings representing a
    valid Python variable name.

    Raises
    ------
    TypeError
        If the `type(value)` is not `str`.
    ValueError
        If the string passed does not begin with a letter or an underscore, or
        if the passed string contains spaces.

    Example
    -------
    1. Usage of the Name descriptor for defining a name attribute.

    >>> import ubermagutil.typesystem as ts
    ...
    >>> @ts.typesystem(myattribute=ts.Name())
    ... class DecoratedClass:
    ...     def __init__(self, myattribute):
    ...         self.myattribute = myattribute
    ...
    >>> dc = DecoratedClass(myattribute='object_name')
    >>> dc.myattribute
    'object_name'
    >>> dc.myattribute = 'newname'  # valid set
    >>> dc.myattribute
    'newname'
    >>> dc.myattribute = '123newname'  # invalid set
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> dc.myattribute = 'Nikola Tesla'  # invalid set
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> dc.myattribute  # the value was not affected by invalid sets
    'newname'

    .. note::

           This class was derived from `ubermagutil.typesystem.Descriptor` and
           inherits its functionality.

    .. seealso:: :py:class:`~ubermagutil.typesystem.Descriptor`

    """
    def __set__(self, instance, value):
        if not isinstance(value, str):
            msg = f'Cannot set {self.name} with {type(value)}.'
            raise TypeError(msg)
        if not (value[0].isalpha() or value.startswith('_')):
            msg = 'String must start with a letter or an underscore.'
            raise ValueError(msg)
        if any(i.isspace() for i in value):
            msg = 'Whitespace characters not allowed.'
            raise ValueError(msg)
        super().__set__(instance, value)


class Dictionary(Descriptor):
    """Descriptor allowing setting attributes with a dictionary with keys
    defined by `key_descriptor` and values defined by `value_descriptor`.

    Parameters
    ----------
    key_descriptor : ubermagutil.typesystem.Descriptor or its derived class
        Accepted dictionary key type.
    value_descriptor : ubermagutil.typesystem.Descriptor or its derived class
        Accepted dictionary type.
    allow_empty : bool, optional
        If `allow_empty=True`, the value can be an empty dictionary.
    otherwise : type
        This type would also be accepted if specified. It has priority over
        other descriptor specification.

    Raises
    ------
    AttributeError
        If `key_descriptor` or `value_descriptor` argument is not passed.
    ValueError
        If an empty dictionary is passed.

    Example
    -------
    1. Usage of the Dictionary descriptor allowing keys defined by
    `ubermagutil.typesystem.Name` and values by
    `ubermagutil.typesystem.Scalar`.

    >>> import ubermagutil.typesystem as ts
    ...
    >>> @ts.typesystem(myattribute=ts.Dictionary(key_descriptor=ts.Name(),
    ...                                          value_descriptor=ts.Scalar()))
    ... class DecoratedClass:
    ...     def __init__(self, myattribute):
    ...         self.myattribute = myattribute
    ...
    >>> dc = DecoratedClass(myattribute={'a': 1, 'b': -1.1})
    >>> dc.myattribute
    {'a': 1, 'b': -1.1}
    >>> dc.myattribute = {'a': 1, 'b': -3}  # valid set
    >>> dc.myattribute
    {'a': 1, 'b': -3}
    >>> dc.myattribute = {1: 1, 'b': 3}  # invalid set
    Traceback (most recent call last):
        ...
    TypeError: ...
    >>> dc.myattribute = {'a': 1, 'c': 'd'}  # invalid set
    Traceback (most recent call last):
        ...
    TypeError: ...
    >>> dc.myattribute = {}  # invalid set
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> dc.myattribute  # the value was not affected by invalid sets
    {'a': 1, 'b': -3}

    .. note::

           This class was derived from `ubermagutil.typesystem.Descriptor` and
           inherits its functionality.

    .. seealso:: :py:class:`~ubermagutil.typesystem.Descriptor`

    """
    def __set__(self, instance, value):
        if hasattr(self, 'otherwise'):
            if isinstance(value, self.otherwise):
                super().__set__(instance, value)
                return None
        if not hasattr(self, 'key_descriptor') or \
        not hasattr(self, 'value_descriptor'):
            msg = ('Dictionary descriptor must have key_descriptor '
                   'and value_descriptor attributes.')
            raise AttributeError(msg)
        if not isinstance(value, dict):
            msg = f'Cannot set {self.name} with {type(value)}.'
            raise TypeError(msg)
        if not value:
            if hasattr(self, 'allow_empty'):
                if not self.allow_empty:
                    msg = f'Cannot set {self.name} with an empty dictionary.'
                    raise ValueError(msg)
            else:
                msg = f'Cannot set {self.name} with an empty dictionary.'
                raise ValueError(msg)
        for key, val in value.items():
            self.key_descriptor.__set__(self.key_descriptor, key)
            self.value_descriptor.__set__(self.value_descriptor, val)
        super().__set__(instance, value)


class Parameter(Descriptor):
    """Descriptor allowing setting attributes with a value described as
    `descriptor` or a dictionary. Dictionary keys are strings defined with
    `ubermagutil.typesystem.Name` descriptor, and the items are defined by
    `descriptor`.

    Parameters
    ----------
    descriptor : ubermagutil.typesystem.Descriptor or its derived class
        Accepted value, or if a dictionary is passed, allowed item type.
    otherwise : type
        This type would also be accepted if specified. It has priority over
        other descriptor specification.

    Raises
    ------
    AttributeError
        If `descriptor` argument is not passed.
    ValueError
        If an empty dictionary is passed.

    Example
    -------
    1. Usage of the Property descriptor allowing scalars.

    >>> import ubermagutil.typesystem as ts
    ...
    >>> @ts.typesystem(myattribute=ts.Parameter(descriptor=ts.Scalar()))
    ... class DecoratedClass:
    ...     def __init__(self, myattribute):
    ...         self.myattribute = myattribute
    ...
    >>> dc = DecoratedClass(myattribute=-2)
    >>> dc.myattribute
    -2
    >>> dc.myattribute = {'a': 1, 'b': -3}  # valid set
    >>> dc.myattribute
    {'a': 1, 'b': -3}
    >>> dc.myattribute = {'a': 1, 'b': 'abc'}  # invalid set
    Traceback (most recent call last):
        ...
    TypeError: ...
    >>> dc.myattribute = {'a b': 1, 'c': -3}  # invalid set
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> dc.myattribute = {}  # invalid set
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> dc.myattribute  # the value was not affected by invalid sets
    {'a': 1, 'b': -3}

    .. note::

           This class was derived from `ubermagutil.typesystem.Descriptor` and
           inherits its functionality.

    .. seealso:: :py:class:`~ubermagutil.typesystem.Descriptor`

    """
    def __set__(self, instance, value):
        if hasattr(self, 'otherwise'):
            if isinstance(value, self.otherwise):
                super().__set__(instance, value)
                return None
        if not hasattr(self, 'descriptor'):
            msg = 'Parameter must have descriptor attribute.'
            raise AttributeError(msg)
        if isinstance(value, dict):
            dictdescriptor = Dictionary(key_descriptor=Name(),
                                        value_descriptor=self.descriptor)
            dictdescriptor.__set__(dictdescriptor, value)
        else:
            self.descriptor.__set__(self.descriptor, value)
        super().__set__(instance, value)


class InSet(Descriptor):
    """Descriptor allowing setting attributes only with a value from a
    predefined set.

    Parameters
    ----------
    allowed_values : set
        Defines the set of allowed values.

    Raises
    ------
    ValueError
        If the value is not in the `allowed_values` set.

    Example
    -------
    1. Usage of the InSet descriptor.

    >>> import ubermagutil.typesystem as ts
    ...
    >>> @ts.typesystem(myattribute=ts.InSet(allowed_values={'x', 'y'}))
    ... class DecoratedClass:
    ...     def __init__(self, myattribute):
    ...         self.myattribute = myattribute
    ...
    >>> dc = DecoratedClass(myattribute='x')
    >>> dc.myattribute
    'x'
    >>> dc.myattribute = 'y'  # valid set
    >>> dc.myattribute
    'y'
    >>> dc.myattribute = 'z'  # invalid set
    Traceback (most recent call last):
        ...
    ValueError: ...
    >>> dc.myattribute  # the value was not affected by invalid sets
    'y'

    .. note::

           This class was derived from `ubermagutil.typesystem.Descriptor` and
           inherits its functionality.

    .. seealso:: :py:class:`~ubermagutil.typesystem.Descriptor`

    """
    def __set__(self, instance, value):
        if value not in self.allowed_values:
            msg = f'Cannot set {self.name} with {value}.'
            raise ValueError(msg)
        super().__set__(instance, value)


class Subset(Descriptor):
    """Descriptor allowing setting attributes only with a subset from a
    predefined set.

    A valid value can be any combination with repetitions of elements
    from `sample_set`.

    Parameters
    ----------
    sample_set : collections.abc.Iterable
        Defines the set of allowed values.

    Raises
    ------
    ValueError
        If value is not a combination of elements in `sample_set`.

    Example
    -------
    1. Usage of the Subset descriptor.

    >>> import ubermagutil.typesystem as ts
    ...
    >>> @ts.typesystem(myattribute=ts.Subset(sample_set='xyz'))
    ... class DecoratedClass:
    ...     def __init__(self, myattribute):
    ...         self.myattribute = myattribute
    ...
    >>> dc = DecoratedClass(myattribute='yx')
    >>> dc.myattribute = 'zyyyyx'  # valid set
    >>> dc.myattribute = 'a'  # invalid set
    Traceback (most recent call last):
        ...
    ValueError: ...

    .. note::

           This class was derived from `ubermagutil.typesystem.Descriptor` and
           inherits its functionality.

    .. seealso:: :py:class:`~ubermagutil.typesystem.Descriptor`

    """
    def __set__(self, instance, value):
        if not isinstance(value, collections.abc.Iterable):
            msg = f'Cannot set {self.name} with {type(value)}.'
            raise TypeError(msg)
        combs = []
        for i in range(0, len(self.sample_set)+1):
            combs += list(itertools.combinations(self.sample_set, r=i))
        if set(value) not in map(set, combs):
            msg = f'Cannot set {self.name} with {value}.'
            raise ValueError(msg)
        super().__set__(instance, set(value))
