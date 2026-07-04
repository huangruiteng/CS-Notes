*** match case

from dataclasses import dataclass

@dataclass
class Point:
    x: int
    y: int

@dataclass
class Circle:
    center: Point
    radius: float

shape = Circle(Point(10, 20), 5.0)

match shape:
    case Point(x=px, y=py):
        print(f"It's a Point at ({px}, {py})")
    case Circle(center=Point(x=cx, y=cy), radius=r): # 嵌套解构
        print(f"It's a Circle with center ({cx}, {cy}) and radius {r}")
    case _:
        print("Unknown shape")
# 输出: It's a Circle with center (10, 20) and radius 5.0



*** Refcount

sys.getrefcount(object)

inspect.stack()[-1].globals


*** GIL

https://wiki.python.org/moin/GlobalInterpreterLock



*** Decorator

def test_task_decorator(*args, task_filter: Union[str, List[str]] = None, **kwargs):
  def decorator(func: Callable):
    def wrapper(self, *extra_args, **extra_kwargs):
      try:
        for name, t in test_task_store.get_tasks().items():
          if task_filter is None or (isinstance(task_filter, str) and name == task_filter) or (
              isinstance(task_filter, list) and name in task_filter):
            try:
              func(self, *extra_args, task=t, task_name=name, **extra_kwargs, **kwargs)
            except Exception as e:
              logging.error(f"Error occurred while running test for task {name}: {e}", exc_info=True)
      except Exception as e:
        logging.error(f"Error in test decorator: {e}", exc_info=True)

    return wrapper

  return decorator

from pprint import pprint, pformat, PrettyPrinter

data = {"a": [1, 2, {"x": 3}], "b": {"c": 4, "d": 5}}

pprint(data, width=80, compact=True, sort_dicts=False)

s = pformat(data, width=60, compact=True, sort_dicts=False)

pp = PrettyPrinter(indent=2, width=60, compact=True, sort_dicts=False)
pp.pprint(data)
