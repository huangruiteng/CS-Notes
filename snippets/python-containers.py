
### basic containers

range和xrange的区别：xrange返回生成器，可以转化成list;   xrange在python3已经被range替代

list.extend(list)
list.append(item)
list.index(item)

- split不加参数，默认为所有的空字符，包括空格、换行(\n)、制表符(\t)等

list = [x.strip() for x in list_string.split() if x.strip()]
list = filter(lambda x: x != 2, iterable)


dict: 同一dict中存储的value类型可以不一样

# 普通dict的default插入方式（类似于C++的[]）
obj = dict.setdefault(key, default=None)
dict.get(key, 'default')

# set
unique_elements = list(set([2,1,2])) # Remove duplicates
myset.remove(elem)
if not myset: # 判断set是否空

# set operations: https://www.linuxtopia.org/online_books/programming_books/python_programming/python_ch16s03.html
&, |, -, ^
异或操作



### SimpleNamespace

from types import SimpleNamespace as ns
person = ns(name="Alice", age=30, city="New York")
ns.x = xxx


### 嵌套遍历

def pin_memory(data):
    if isinstance(data, torch.Tensor):
        return data.pin_memory()
    elif isinstance(data, string_classes):
        return data
    elif isinstance(data, container_abcs.Mapping):
        return {k: pin_memory(sample) for k, sample in data.items()}
    elif isinstance(data, tuple) and hasattr(data, '_fields'):  # namedtuple
        return type(data)(*(pin_memory(sample) for sample in data))
    elif isinstance(data, container_abcs.Sequence):
        return [pin_memory(sample) for sample in data]
    elif hasattr(data, "pin_memory"):
        return data.pin_memory()
    else:
        return data