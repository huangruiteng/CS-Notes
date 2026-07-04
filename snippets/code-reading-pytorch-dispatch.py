https://blog.ezyang.com/2019/05/pytorch-internals/

torch.add(x, y)
Python 参数解析：THPVariable_add，位于 python_torch_functions.cpp
变量类型：VariableType::add
类型：TypeDefault::add（或 CPUFloatType）
原生函数：at::native::add，位于 BinaryOps.cpp
TH 函数：THTensor_(add)，位于 generic/THTensorMath.cpp

* aten/src/ATen/native/cpu/README.md

1. Declare your dispatch in a header file using
  `DECLARE_DISPATCH(fn_type, fnNameImpl)`
   where `fn_type` is the function pointer type of the kernel (e.g.,
   defined as `using fn_type = void(*)(Tensor&, const Tensor&)`
   and `fnNameImpl` is the name of your dispatch registry.
   (It doesn't really matter where you  put this declaration.)

2. Define your dispatch in a C++ file that is NOT in the cpu
   directory (dispatch must be defined exactly once) using
   `DEFINE_DISPATCH(fnNameImpl)` (matching the name of your declaration.)
   Include the header file that declares the dispatch in this C++
   file.  Conventionally, we define the dispatch in the same file
   we will define our native function in.

3. Define a native function which calls into the dispatch using
   `fnNameImpl(kCPU, arguments...)`, where the arguments are
   the arguments according to the `fn_type` you defined in the
   declaration.

4. Write your actual kernel (e.g., `your_kernel`) in the
   cpu directory, and register it to
   the dispatch using `REGISTER_DISPATCH(fnNameImpl, &your_kernel)`, if
   it does not perform as well with AVX512, as it does with AVX2.
   Otherwise, if it performs well with AVX512, register it with `ALSO_REGISTER_AVX512_DISPATCH(fnNameImpl, &your_kernel)`.
   Compute-intensive kernels tend to perform better with AVX512, than with AVX2.
   Comparing AVX2 & AVX512 variants of a kernel can be done by registering a kernel with `ALSO_REGISTER_AVX512_DISPATCH(fnNameImpl, &your_kernel)`, building from source, and then benchmarking the kernel's performance by running a benchmarking script with the environment variables `ATEN_CPU_CAPABILITY=avx2` and `ATEN_CPU_CAPABILITY=avx512`, respectively.
   tcmalloc/jemalloc can be preloaded for minimal run-to-run variation.


* tools/autograd/gen_python_functions.py

生成的方法：

static PyObject * THPVariable_add(PyObject* self_, PyObject* args, PyObject* kwargs)
{
    HANDLE_TH_ERRORS
    // 自动生成！大致浏览即可
    static PythonArgParser parser({
        "add(Tensor input, Scalar alpha, Tensor other, *, Tensor out=None)|deprecated",
        "add(Tensor input, Tensor other, *, Scalar alpha=1, Tensor out=None)",
    }, /*traceable=*/true);

    // 参数解析器
    ParsedArgs<4> parsed_args;
    auto r = parser.parse(args, kwargs, parsed_args);

    if (r.idx == 0) {
        if (r.isNone(3)) {
            return wrap(dispatch_add(r.tensor(0), r.scalar(1), r.tensor(2)));
        } else {
            return wrap(dispatch_add(r.tensor(0), r.scalar(1), r.tensor(2), r.tensor(3)));
        }
    } else if (r.idx == 1) {
        // 释放全局解释器锁（GIL）
        if (r.isNone(3)) {
        	# AutoNoGIL no_gil; 
            # return self.add(other, alpha); 
            return wrap(dispatch_add(r.tensor(0), r.tensor(1), r.scalar(2)));
        } else {
            return wrap(dispatch_add(r.tensor(0), r.tensor(1), r.scalar(2), r.tensor(3)));
        }
    }
    Py_RETURN_NONE;
    // 重新包装成PyObject
    END_HANDLE_TH_ERRORS
}

static PyMethodDef torch_functions[] = {
    // 实际绑定在torch._C.VariableFunctions上
    {"add", (PyCFunction)THPVariable_add, METH_VARARGS | METH_KEYWORDS | METH_STATIC, N
   ...
};

// 文件：torch/csrc/autograd/generated/python_torch_functions_dispatch.h


### dispatch

DECLARE_DISPATCH(structured_binary_fn_alpha, add_stub)

build/aten/src/ATen/ops/add_ops.h

*aten/src/ATen/Dispatch.h

The AT_DISPATCH_* family of macros provides the ability to
conveniently generate specializations of a kernel over all of the
dtypes we care about in PyTorch.  We call it "dispatch" because
we are "dispatching" to the correct, dtype-specific kernel.

A standard usage looks like:

     AT_DISPATCH_ALL_TYPES(self.scalar_type(), "op_name", [&] {
         // Your code here, with 'scalar_t' now defined to
         // be the dtype in question
     });

There are many variations of this macro, so it's important to
understand exactly /which/ dtypes you want to get instantiated, as
well as what the "default" set is.

The default set of dtypes that are instantiated (e.g., by
AT_DISPATCH_ALL_TYPES) are floating point types (float, double),
and integral types (int32_t, int64_t, int16_t, int8_t, uint8_t),
but NOT booleans (bool), half-precision floats (Half) or
complex number (c10::complex<float>, c10::complex<double>).
This "cut" is somewhat historical (the default types are the
ones that TH historically supported), but it also reflects the
fact that the non-default types are "poorly" behaved (booleans
are NOT integers mod 2, half precision operations ~essentially
don't exist on CPU, complex numbers are an experimental application).

Here are the questions you should generally ask to decide which
dispatch you want:

1. Is this an integral or floating point specific operation?
   (If so, you'll want one of the FLOATING or INTEGRAL macros.)

2. Should half be supported?  (If you're on CPU, the answer is almost
   definitely no.  If you do want support, use one of the AND_HALF
   macros)

Much rarer situations:

3. Should bool be supported?  (You often have to write your kernel
   differently if arithmetic operations are involved.)  If so,
   Use AT_DISPATCH_ALL_TYPES_AND along with ScalarType::Bool

4. Should complex be supported?  The answer is almost always no,
   unless you are working on "generic" code that should work on
   all dtypes.

Parameters:
-----------

1. The NAME argument is a "tag" that is used to trace and then
   conditionally compile fragments of the case statements such
   that the kernel functions are specialized only for the dtypes
   that are needed. The NAME parameter *must* be a build time
   const char* (can't be std::string, etc...)

Please ensure that the NAME is unique for every implementation
or you run the risk of over-including code for the kernel
functions. There is no risk of missing out on any code, so
it's mostly a risk of a Type-2 error, and not a Type-1 error.

Switch-like syntax:
-------------------
There is also a switch-case like syntax which is useful if a kernel
needs to be specialized for particular scalar types

     AT_DISPATCH_SWITCH(self.scalar_type(), "op_name",
         AT_DISPATCH_CASE_INTEGRAL_TYPES([&] {
           op_integral<scalar_t>(iter);
         })
         AT_DISPATCH_CASE_FLOATING_TYPES([&] {
           op_floating<scalar_t>(iter);
         })
         AT_DISPATCH_CASE(kBool, [&] {
           op_bool(iter);
         })
     );

For each AT_DISPATCH_FOO macro, there is a corresponding
AT_DISPATCH_CASE_FOO macro which can be used inside of an
AT_DISPATCH_SWITCH block.

NB: the the_type variable is not used, but we have kept it for
backwards compatibility.  It's probably not used by anyone though;
but we're just being safe (and it doesn't hurt.)  Note we must
use it to shut up warnings about unused store.


e.g.
#define AT_DISPATCH_FLOATING_TYPES(TYPE, NAME, ...) \
  AT_DISPATCH_SWITCH(TYPE, NAME, AT_DISPATCH_CASE_FLOATING_TYPES(__VA_ARGS__))



### register a func

aten/src/ATen/native/README.md

- func: add.Tensor(Tensor self, Tensor other, *, Scalar alpha=1) -> Tensor
  device_check: NoCheck   # TensorIterator
  structured_delegate: add.out
  variants: function, method
  dispatch:
    SparseCPU, SparseCUDA, SparseMeta: add_sparse
    SparseCsrCPU, SparseCsrCUDA, SparseCsrMeta: add_sparse_csr
    MkldnnCPU: mkldnn_add
    ZeroTensor: add_zerotensor
    NestedTensorCPU, NestedTensorCUDA: NestedTensor_add_Tensor
  tags: [core, pointwise]

- func: add_.Tensor(Tensor(a!) self, Tensor other, *, Scalar alpha=1) -> Tensor(a!)
  device_check: NoCheck   # TensorIterator
  variants: method
  structured_delegate: add.out
  dispatch:
    SparseCPU, SparseCUDA, SparseMeta: add_sparse_
    SparseCsrCPU, SparseCsrCUDA, SparseCsrMeta: add_sparse_csr_
    MkldnnCPU: mkldnn_add_
    NestedTensorCPU, NestedTensorCUDA: NestedTensor_add__Tensor
  tags: pointwise

- func: add.out(Tensor self, Tensor other, *, Scalar alpha=1, Tensor(a!) out) -> Tensor(a!)
  device_check: NoCheck   # TensorIterator
  structured: True
  structured_inherits: TensorIteratorBase
  ufunc_inner_loop:
    Generic: add (AllAndComplex, BFloat16, Half, ComplexHalf)
    ScalarOnly: add (Bool)
  dispatch:
    SparseCPU, SparseMeta: add_out_sparse_cpu
    SparseCUDA: add_out_sparse_cuda
    SparseCsrCPU, SparseCsrMeta: add_out_sparse_compressed_cpu
    SparseCsrCUDA: add_out_sparse_compressed_cuda
    MkldnnCPU: mkldnn_add_out
    MPS: add_out_mps
  tags: pointwise

 ### register derivative

 https://github.com/pytorch/pytorch/blob/main/tools/autograd/derivatives.yaml
