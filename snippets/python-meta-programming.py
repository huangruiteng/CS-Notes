
func.__get__(opt, opt.__class__)(*args, **kwargs)


### Monkey Patch

可以修改类和模块
math.sqrt = new_sqrt


### 动态导入

import importlib

# 模块名
module_name = 'test_framework.model_store.toy_model'
# 类名或函数名
definition_name = 'ToyModel'

# 动态导入模块
module = importlib.import_module(module_name)
# 从模块中获取具体的类或函数
model_def = getattr(module, definition_name)

# 使用获取到的类创建实例
model = model_def()

# 如何获取module_name和definition_name
module = dataset.__class__.__module__
def_name = dataset.__class__.__name__
