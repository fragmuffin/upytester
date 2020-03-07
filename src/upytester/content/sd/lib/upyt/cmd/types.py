type_func = type((lambda: None))
# ref: https://forum.micropython.org/viewtopic.php?t=5538
type_gen = type((lambda: (yield))())  # Generator type
type_gen_func = type((lambda: (yield)))  # Generator function

# Async types
type_coro = type((lambda: (yield))())
type_bound_coro = type(type('_', (object,), {'x': lambda s: (yield)})().x())
