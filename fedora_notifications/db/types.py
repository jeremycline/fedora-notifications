# SPDX-License-Identifier: GPL-2.0-or-later
#
# Copyright (C) 2018 Red Hat, Inc.
"""Database type definitions."""
import re
import uuid

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Enum, SchemaType, TypeDecorator, CHAR


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    If PostgreSQL is being used, use its native UUID type, otherwise use a CHAR(32) type.
    """

    impl = CHAR

    def load_dialect_impl(self, dialect):
        """
        PostgreSQL has a native UUID type, so use it if we're using PostgreSQL.

        Args:
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            sqlalchemy.types.TypeEngine: Either a PostgreSQL UUID or a CHAR(32) on other
                dialects.
        """
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    def process_bind_param(self, value, dialect):
        """
        Process the value being bound.

        If PostgreSQL is in use, just use the string representation of the UUID.
        Otherwise, use the integer as a hex-encoded string.

        Args:
            value (object): The value that's being bound to the object.
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            str: The value of the UUID as a string.
        """
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    def process_result_value(self, value, dialect):
        """
        Casts the UUID value to the native Python type.

        Args:
            value (object): The database value.
            dialect (sqlalchemy.engine.interfaces.Dialect): The dialect in use.

        Returns:
            uuid.UUID: The value as a Python :class:`uuid.UUID`.
        """
        if value is None:
            return value
        else:
            return uuid.UUID(value)


class EnumSymbol(object):
    """
    Define a fixed symbol tied to a parent class.

    Originally from http://techspot.zzzeek.org/2011/01/14/the-enum-recipe, with
    documentation from Bodhi.
    """

    def __init__(self, cls_, name, value, description):
        """
        Initialize the EnumSymbol.

        Args:
            cls_ (EnumMeta): The metaclass this symbol is tied to.
            name (str): The name of this symbol.
            value (str): The value used in the database to represent this symbol.
            description (str): A human readable description of this symbol.
        """
        self.cls_ = cls_
        self.name = name
        self.value = value
        self.description = description

    def __reduce__(self):
        """
        Allow unpickling to return the symbol linked to the DeclEnum class.

        Returns:
            tuple: A 2-tuple of the ``getattr`` function, and a 2-tuple of the EnumSymbol's member
            class and name.
        """
        return getattr, (self.cls_, self.name)

    def __iter__(self):
        """
        Iterate over this EnumSymbol's value and description.

        Returns:
            iterator: An iterator over the value and description.
        """
        return iter([self.value, self.description])

    def __repr__(self):
        """
        Return a string representation of this EnumSymbol.

        Returns:
            str: A string representation of this EnumSymbol's value.
        """
        return "<%s>" % self.name

    def __str__(self):
        """
        Return a string representation of this EnumSymbol.

        Returns:
            str: A string representation of this EnumSymbol's value.
        """
        return str(self.value)


class EnumMeta(type):
    """Generate new DeclEnum classes."""

    def __init__(cls, classname, bases, dict_):
        """
        Initialize the metaclass.

        Args:
            classname (basestring): The name of the enum.
            bases (list): A list of base classes for the enum.
            dict_ (dict): A key-value mapping for the new enum's attributes.
        Returns:
            DeclEnum: A new DeclEnum.
        """
        cls._reg = reg = cls._reg.copy()
        for k, v in dict_.items():
            if isinstance(v, tuple):
                sym = reg[v[0]] = EnumSymbol(cls, k, *v)
                setattr(cls, k, sym)
        return type.__init__(cls, classname, bases, dict_)

    def __iter__(cls):
        """
        Iterate the enum values.

        Returns:
            iterator: An iterator for the enum values.
        """
        return iter(cls._reg.values())


class DeclEnum(metaclass=EnumMeta):
    """Declarative enumeration."""

    _reg = {}

    @classmethod
    def from_string(cls, value):
        """
        Convert a string version of the enum to its enum type.

        Args:
            value (str): A string that you wish to convert to an Enum value.
        Returns:
            EnumSymbol: The symbol corresponding to the value.
        Raises:
            ValueError: If no symbol matches the given value.
        """
        try:
            return cls._reg[value]
        except KeyError:
            raise ValueError("Invalid value for %r: %r" % (cls.__name__, value))

    @classmethod
    def values(cls):
        """
        Return the possible values that this enum can take on.

        Returns:
            list: A list of strings of the values that this enum can represent.
        """
        return list(cls._reg.keys())

    @classmethod
    def db_type(cls):
        """
        Return a database column type to be used for this enum.

        Returns:
            DeclEnumType: A DeclEnumType to be used for this enum.
        """
        return DeclEnumType(cls)


class DeclEnumType(SchemaType, TypeDecorator):
    """A database column type for an enum."""

    def __init__(self, enum):
        """
        Initialize with the given enum.

        Args:
            enum (.EnumMeta): The enum metaclass.
        """
        self.enum = enum
        self.impl = Enum(
            *enum.values(),
            name="ck%s"
            % re.sub("([A-Z])", lambda m: "_" + m.group(1).lower(), enum.__name__)
        )

    def _set_table(self, table, column):
        """
        Set the table for this object.

        Args:
            table (sqlalchemy.sql.schema.Table): The table that uses this Enum.
            column (sqlalchemy.sql.schema.Column): The column that uses this Enum.
        """
        self.impl._set_table(table, column)

    def copy(self):
        """
        Return a copy of self.

        Returns:
            DeclEnumType: A copy of self.
        """
        return DeclEnumType(self.enum)

    def process_bind_param(self, value, dialect):
        """
        Return the value of the enum.

        Args:
            value (.enum.EnumSymbol): The enum symbol we are resolving the value
                of.
            dialect (sqlalchemy.engine.default.DefaultDialect): Unused.
        Returns:
            basestring: The EnumSymbol's value.
        """
        if value is None:
            return None
        return value.value

    def process_result_value(self, value, dialect):
        """
        Return the enum that matches the given string.

        Args:
            value (str): The name of an enum.
            dialect (sqlalchemy.engine.default.DefaultDialect): Unused.
        Returns:
            EnumSymbol or None: The enum that matches value, or ``None`` if ``value`` is ``None``.
        """
        if value is None:
            return None
        return self.enum.from_string(value.strip())

    def create(self, bind=None, checkfirst=False):
        """Issue CREATE ddl for this type, if applicable."""
        super(DeclEnumType, self).create(bind, checkfirst)
        t = self.dialect_impl(bind.dialect)
        if t.impl.__class__ is not self.__class__ and isinstance(t, SchemaType):
            t.impl.create(bind=bind, checkfirst=checkfirst)

    def drop(self, bind=None, checkfirst=False):
        """Issue DROP ddl for this type, if applicable."""
        super(DeclEnumType, self).drop(bind, checkfirst)
        t = self.dialect_impl(bind.dialect)
        if t.impl.__class__ is not self.__class__ and isinstance(t, SchemaType):
            t.impl.drop(bind=bind, checkfirst=checkfirst)


class DeliveryType(DeclEnum):
    """
    An enumeration of the possible delivery methods.

    Attributes:
        irc (EnumSymbol): Used to represent the IRC delivery method.
        email (EnumSymbol): Used to represent the email delivery method.
    """

    irc = "irc", "Irc"
    email = "email", "Email"


class SeverityType(DeclEnum):
    """
    An enumeration of the possible severity levels a message can have.

    Attributes:
        debug (EnumSymbol): Used to indicate debug-level messages.
        info (EnumSymbol): Used to indicate info-level messages.
        warning (EnumSymbol): Used to indicate warning-level messages.
        error (EnumSymbol): Used to indicate error-level messages.
    """

    debug = "DEBUG", "Debug"
    info = "INFO", "Info"
    warning = "WARNING", "Warning"
    error = "ERROR", "Error"
