This is a generic single-database configuration for Alembic.

Alembic integrates with SQLAlchemy and it is possible to auto-generate some
migrations::

    $ alembic revision --autogenerate -m "<migration description here>"

Note that there are some changes that cannot be detected using auto-generated
Consult the `auto-generate documentation`_ for complete details.


.. _auto-generate documentation:
    http://alembic.zzzcomputing.com/en/latest/autogenerate.html
