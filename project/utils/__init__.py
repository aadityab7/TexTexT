# TexTexT/app/utils/__init__.py

import pkgutil
import inspect
import importlib

# Collect all functions from all modules in the utils package
def collect_functions():
    functions = []
    for module_info in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f'{__name__}.{module_info.name}')
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if obj.__module__ == module.__name__:  # Ensure it's defined in the module
                functions.append(name)
    return functions

# Dynamically populate the __all__ list
__all__ = collect_functions()