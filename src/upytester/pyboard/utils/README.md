# `upytester.pyboard.utils` module

The `utils` module will differ when run on different platforms.

Each sub-module is named for: `"utils_{}.py".format(sys.platform)`\
See [`sys.platform` documentation](https://docs.python.org/3/library/sys.html#sys.platform) for details.

Mostly an end-user wouldn't need to access this module directly.\
All functionality is implemented via the `upytester.PyBoard` class.
