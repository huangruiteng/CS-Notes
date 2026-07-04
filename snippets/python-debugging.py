def trace_function_call(func):
    """
    A decorator that prints the full, multi-level call stack each time a function 
    is called. The output is formatted to resemble a standard Python traceback.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get the current stack
        stack = inspect.stack()
        
        print(f"\n--- Call Trace: Executing '{func.__name__}' ---")
        
        # Print the stack trace, starting from the immediate caller and going up.
        # stack[0] is the frame for this 'wrapper' function, so we skip it.
        for frame_info in stack[1:]:
            print(f"  File \"{frame_info.filename}\", line {frame_info.lineno}, in {frame_info.function}")
            # frame_info.code_context is a list of lines from the source code.
            # The line that made the call is usually the first one.
            if frame_info.code_context:
                print(f"    {frame_info.code_context[0].strip()}")
                
        print(f"--------------------------------------\n")
        
        # Call the original function
        return func(*args, **kwargs)
    return wrapper


def print_object_details(obj, indent=0, obj_name='object'):
    """
    递归地打印一个对象的所有属性，以便于详细查看和比较。

    Args:
        obj: 需要打印的对象。
        indent (int): 当前打印的缩进级别。
        obj_name (str): 对象的变量名或描述符。
    """
    # 设置缩进字符串
    indent_str = ' ' * indent
    
    # 打印对象的基本信息
    if hasattr(obj, '__class__'):
        print(f"{indent_str}{obj_name} (type: {obj.__class__.__name__}):")
    else:
        print(f"{indent_str}{obj_name} (type: {type(obj).__name__}):")


    # 如果对象是基本类型或没有属性，直接打印其值
    if not hasattr(obj, '__dict__'):
        # 对列表/元组进行特殊处理
        if isinstance(obj, (list, tuple)):
            if not obj:
                print(f"{indent_str}  - empty list/tuple")
            for i, item in enumerate(obj):
                print_object_details(item, indent=indent + 4, obj_name=f"[{i}]")
        # 对字典进行特殊处理
        elif isinstance(obj, dict):
            if not obj:
                print(f"{indent_str}  - empty dict")
            for key, value in obj.items():
                print_object_details(value, indent=indent + 4, obj_name=f"['{key}']")
        else:
             print(f"{indent_str}  Value: {obj}")
        return

    # 遍历对象的所有属性
    attributes = obj.__dict__
    if not attributes:
        print(f"{indent_str}  (No attributes)")
        return

    for attr_name, attr_value in attributes.items():
        # 打印属性名
        print(f"{indent_str}  - {attr_name}:")
        
        # 递归打印属性值
        print_object_details(attr_value, indent=indent + 4, obj_name=f"value")
