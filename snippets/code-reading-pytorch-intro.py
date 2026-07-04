https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.md#codebase-structure

## Codebase structure

* [c10](c10) - Core library files that work everywhere, both server
  and mobile. We are slowly moving pieces from [ATen/core](aten/src/ATen/core)
  here. This library is intended only to contain essential functionality,
  and appropriate to use in settings where binary size matters. (But
  you'll have a lot of missing functionality if you try to use it
  directly.)
  -- caffe2 and aten
* [aten](aten) - C++ tensor library for PyTorch (no autograd support)
  * [src](aten/src) - [README](aten/src/README.md)
    * [ATen](aten/src/ATen)
      * [core](aten/src/ATen/core) - Core functionality of ATen. This
        is migrating to top-level c10 folder.
      * [native](aten/src/ATen/native) - Modern implementations of
        operators. If you want to write a new operator, here is where
        it should go. Most CPU operators go in the top level directory,
        except for operators which need to be compiled specially; see
        cpu below.
        * [cpu](aten/src/ATen/native/cpu) - Not actually CPU
          implementations of operators, but specifically implementations
          which are compiled with processor-specific instructions, like
          AVX. See the [README](aten/src/ATen/native/cpu/README.md) for more
          details.
        * [cuda](aten/src/ATen/native/cuda) - CUDA implementations of
          operators.
        * [sparse](aten/src/ATen/native/sparse) - CPU and CUDA
          implementations of COO sparse tensor operations
        * [mkl](aten/src/ATen/native/mkl) [mkldnn](aten/src/ATen/native/mkldnn)
          [miopen](aten/src/ATen/native/miopen) [cudnn](aten/src/ATen/native/cudnn)
          - implementations of operators which simply bind to some
            backend library.
        * [quantized](aten/src/ATen/native/quantized/) - Quantized tensor (i.e. QTensor) operation implementations. [README](aten/src/ATen/native/quantized/README.md) contains details including how to implement native quantized operations.
* [torch](torch) - The actual PyTorch library. Everything that is not
  in [csrc](torch/csrc) is a Python module, following the PyTorch Python
  frontend module structure.
  * [csrc](torch/csrc) - C++ files composing the PyTorch library. Files
    in this directory tree are a mix of Python binding code, and C++
    heavy lifting. Consult `setup.py` for the canonical list of Python
    binding files; conventionally, they are often prefixed with
    `python_`. [README](torch/csrc/README.md)
    * [jit](torch/csrc/jit) - Compiler and frontend for TorchScript JIT
      frontend. [README](torch/csrc/jit/README.md)
    * [autograd](torch/csrc/autograd) - Implementation of reverse-mode automatic differentiation. [README](torch/csrc/autograd/README.md)
    * [api](torch/csrc/api) - The PyTorch C++ frontend.
    * [distributed](torch/csrc/distributed) - Distributed training
      support for PyTorch.
* [tools](tools) - Code generation scripts for the PyTorch library.
  See [README](tools/README.md) of this directory for more details.
* [test](test) - Python unit tests for PyTorch Python frontend.
  * [test_torch.py](test/test_torch.py) - Basic tests for PyTorch
    functionality.
  * [test_autograd.py](test/test_autograd.py) - Tests for non-NN
    automatic differentiation support.
  * [test_nn.py](test/test_nn.py) - Tests for NN operators and
    their automatic differentiation.
  * [test_jit.py](test/test_jit.py) - Tests for the JIT compiler
    and TorchScript.
  * ...
  * [cpp](test/cpp) - C++ unit tests for PyTorch C++ frontend.
    * [api](test/cpp/api) - [README](test/cpp/api/README.md)
    * [jit](test/cpp/jit) - [README](test/cpp/jit/README.md)
    * [tensorexpr](test/cpp/tensorexpr) - [README](test/cpp/tensorexpr/README.md)
  * [expect](test/expect) - Automatically generated "expect" files
    which are used to compare against expected output.
  * [onnx](test/onnx) - Tests for ONNX export functionality,
    using both PyTorch and Caffe2.
* [caffe2](caffe2) - The Caffe2 library.
  * [core](caffe2/core) - Core files of Caffe2, e.g., tensor, workspace,
    blobs, etc.
  * [operators](caffe2/operators) - Operators of Caffe2.
  * [python](caffe2/python) - Python bindings to Caffe2.
  * ...
* [.circleci](.circleci) - CircleCI configuration management. [README](.circleci/README.md)


### Anatomy of an operator call
