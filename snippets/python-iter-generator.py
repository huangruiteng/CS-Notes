class Fibs:
    def __init__(self, n=20):
        self.a = 0
        self.b = 1
        self.n = n
    def __iter__(self):
        return self
    def __next__(self):
        self.a, self.b = self.b, self.a + self.b
        if self.a > self.n:
            raise StopIteration
        return self.a

fibs = Fibs()
for each in fibs:
    print(each)

# 输出 
# 1 1 2 3 5 8 13

Python 中， next() 内置函数调⽤的是对象的 next() ⽅法，iter() 内置函数调⽤的是对象的 iter() ⽅法

- 每次调用iter()，返回的是一个新的迭代器！




### itertools

 PARAM_COMBINATIONS = [(*t, mode) for t, mode in
                        itertools.product([(4, 2), (4, 7), (2, 4), (3, 9), (1, 3), (1, 10), (2, 1), (1, 2)],
                                          [FILE_DISPATCH_MODE, ALL_TO_ALL_MODE])]


###

def named_parameters(
        self, prefix: str = "", recurse: bool = True, remove_duplicate: bool = True
    ) -> Iterator[Tuple[str, Parameter]]:
        gen = self._named_members(
            lambda module: module._parameters.items(),
            prefix=prefix,
            recurse=recurse,
            remove_duplicate=remove_duplicate,
        )
        yield from gen


def _named_members(
        self, get_members_fn, prefix="", recurse=True, remove_duplicate: bool = True
    ):
        r"""Help yield various names + members of modules."""
        memo = set()
        modules = (
            self.named_modules(prefix=prefix, remove_duplicate=remove_duplicate)
            if recurse
            else [(prefix, self)]
        )
        for module_prefix, module in modules:
            members = get_members_fn(module)
            for k, v in members:
                if v is None or v in memo:
                    continue
                if remove_duplicate:
                    memo.add(v)
                name = module_prefix + ("." if module_prefix else "") + k
                yield name, v