
import functools

def my_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("Before function call")
        result = func(*args, **kwargs)
        print("After function call")
        return result
    return wrapper

@my_decorator
def add(a, b):
    """This function adds two numbers."""
    return a + b

print(add.__name__)  # 输出 'add'
print(add.__doc__)   # 输出 'This function adds two numbers.'



*** get_var_from_closure

from typing import Any, Callable

def get_var_from_closure(func_obj: Callable, var_name: str) -> Any:
    """
    Attempts to extract the value of a free variable with the specified name
    from the closure of a function object.

    Args:
        func_obj (Callable): The target function object.
        var_name (str): The name of the variable to extract from the closure.

    Returns:
        Any: The value of the extracted variable.

    Raises:
        TypeError: If the provided object is not a valid function or
                   does not have the characteristics of a closure.
        ValueError: If the specified var_name is not one of the function
                    object's free variables.
        IndexError: If an index error occurs while accessing the closure's
                    contents (theoretically should not happen if ValueError
                    is correctly caught).
    """
    if not callable(func_obj) or \
       not hasattr(func_obj, '__code__') or \
       not hasattr(func_obj, '__closure__') or \
       func_obj.__closure__ is None:
        raise TypeError(
            "Error: The provided object is not a valid function or does not "
            "meet the characteristics of a closure (missing __code__ or "
            "__closure__ attribute, or __closure__ is None)."
        )

    free_var_names = func_obj.__code__.co_freevars

    try:
        target_var_index = free_var_names.index(var_name)  # Find the position of var_name in the tuple of free variables
    except ValueError:
        raise ValueError(
            f"Error: '{var_name}' is not one of the free variables of function "
            f"{getattr(func_obj, '__name__', 'Unnamed function')}. "
            f"Available free variables: {free_var_names}"
        ) from None

    try:
        target_var_cell = func_obj.__closure__[target_var_index]
        target_var_value = target_var_cell.cell_contents
        return target_var_value
    except IndexError:
        # Theoretically, if free_var_names.index(var_name) succeeds,
        # then target_var_index should be a valid index for __closure__.
        raise IndexError(
            f"Error: Index {target_var_index} is out of range for the __closure__ of function "
            f"{getattr(func_obj, '__name__', 'Unnamed function')}. "
            f"This should not normally occur if '{var_name}' is in co_freevars."
        ) from None