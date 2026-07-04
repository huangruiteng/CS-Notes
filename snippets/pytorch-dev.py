### 安装 - pip

pip3 install torch torchvision torchaudio
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

https://download.pytorch.org/whl/torch_stable.html
https://download.pytorch.org/whl/cu118/
https://download.pytorch.org/whl/cu121/


### 安装 - build from source

https://pytorch.org/get-started/locally/ 查看torch和cuda稳定版本

# https://github.com/pytorch/pytorch#from-source

# anaconda
# https://www.anaconda.com/download
wget https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Linux-x86_64.sh
chmod +x Anaconda3-2024.10-1-Linux-x86_64.sh 
./Anaconda3-2024.10-1-Linux-x86_64.sh

source $HOME/anaconda3/bin/activate 
# conda create -n pytorch-debug
conda activate pytorch-debug

# cudnn
cat /usr/include/cudnn_version.h 

https://developer.nvidia.com/cudnn-downloads

wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cudnn
sudo apt-get -y install cudnn-cuda-12 # 11 or 12

# cuda compiler
https://gist.github.com/ax3l/9489132

# pytorch
https://github.com/pytorch/pytorch?tab=readme-ov-file#from-source

git clone --recursive https://github.com/pytorch/pytorch --depth 1
cd pytorch
git submodule sync
git submodule update --init --recursive

conda install cmake ninja
pip install -r requirements.txt

pip install mkl-static mkl-include
# CUDA only: Add LAPACK support for the GPU if needed
conda install -c pytorch magma-cuda121  # or the magma-cuda* that matches your CUDA version from https://anaconda.org/pytorch/repo

# (optional) If using torch.compile with inductor/triton, install the matching version of triton
# Run from the pytorch directory after cloning
# For Intel GPU support, please explicitly `export USE_XPU=1` before running command.
make triton



./tools/nightly.py checkout -b my-nightly-branch -p my-env

export CMAKE_PREFIX_PATH="${CONDA_PREFIX:-'$(dirname $(which conda))/../'}:${CMAKE_PREFIX_PATH}"
CUDA_DEVICE_DEBUG=1 DEBUG=1 USE_SYSTEM_NCCL=1 python setup.py develop

# 需要use system nccl，否则会报错。system nccl具备find能力 https://github.com/pytorch/pytorch/pull/2853


### run

Clion：新增conda python解释器

### debug

一些讨论：https://news.ycombinator.com/item?id=35706687

- 方法是：
  - python程序的debug，使用Clion IDE
  - c++ extension的debug，使用shell内的gdb
  - 核心是clion python debugger和gdb debugger，二者保持其中一个在断点状态


pytorch-gdb: 
https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.md#gdb-integration
https://github.com/pytorch/pytorch/blob/main/tools/gdb/pytorch-gdb.py

#### Rebuild few files with debug information

https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.md#rebuild-few-files-with-debug-information


`cuda-gdb` and `cuda-memcheck`


### 部分构件相关

#### 增量build
python setup.py develop

# 如果需要清理后重新构建（完全重建）
python setup.py clean && python setup.py develop

For subsequent builds (i.e., when build/CMakeCache.txt exists), the build options passed for the first time will persist; 
please run ccmake build/, run cmake-gui build/, or directly edit build/CMakeCache.txt to adapt build options.

#### 只构建test

Working on a test binary?
Run (cd build && ninja bin/test_binary_name) to rebuild only that test binary (without rerunning cmake). 
(Replace ninja with make if you don't have ninja installed)

#### ccache

sudo apt install ccache
# config: cache dir is ~/.ccache, conf file ~/.ccache/ccache.conf
# max size of cache
ccache -M 25Gi  # -M 0 for unlimited
# unlimited number of files
ccache -F 0

To check this is working, do two clean builds of pytorch in a row. The second build should be substantially and noticeably faster than the first build. 
If this doesnt seem to be the case, check the CMAKE_<LANG>_COMPILER_LAUNCHER rules in build/CMakeCache.txt, where <LANG> is C, CXX and CUDA. E
ach of these 3 variables should contain ccache, e.g.

//CXX compiler launcher
CMAKE_CXX_COMPILER_LAUNCHER:STRING=/usr/bin/ccache

If not, you can define these variables on the command line before invoking setup.py.

export CMAKE_C_COMPILER_LAUNCHER=ccache
export CMAKE_CXX_COMPILER_LAUNCHER=ccache
export CMAKE_CUDA_COMPILER_LAUNCHER=ccache
python setup.py develop







### write op

二次开发autograd
* non-tensor在backward时一定返回None



### cuda kernel

https://github.com/pytorch/pytorch/blob/main/CONTRIBUTING.md#cuda-development-tips

https://github.com/pytorch/pytorch/wiki/CUDA-basics


### load_inline

#include <torch/extension.h>
torch::Tensor square_matrix(torch::Tensor matrix);
PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
m.def("square_matrix", torch::wrap_pybind_function(square_matrix), "square_matrix");
}


# setup.py

from setuptools import setup
from torch.utils.cpp_extension import BuildExtension, CppExtension

setup(
    name='square_matrix',
    ext_modules=[
        CppExtension('square_matrix', ['square_matrix.cpp']),
    ],
    cmdclass={
        'build_ext': BuildExtension
    })



### gradient hook

https://www.digitalocean.com/community/tutorials/pytorch-hooks-gradient-clipping-debugging


### build info

--
-- ******** Summary ********
-- General:
--   CMake version         : 4.0.0
--   CMake command         : /root/anaconda3/envs/pytorch-debug/lib/python3.13/site-packages/cmake/data/bin/cmake
--   System                : Linux
--   C++ compiler          : /usr/bin/c++
--   C++ compiler id       : GNU
--   C++ compiler version  : 11.4.0
--   Using ccache if found : ON
--   Found ccache          : /usr/bin/ccache
--   CXX flags             :  -fvisibility-inlines-hidden -DUSE_PTHREADPOOL -DUSE_KINETO -DLIBKINETO_NOROCTRACER -DLIBKINETO_NOXPUPTI=ON -DUSE_FBGEMM -DUSE_PYTORCH_QNNPACK -DUSE_XNNPACK -DSYMBOLICATE_MOBILE_DEBUG_HANDLE -O2 -fPIC -Wall -Wextra -Werror=return-type -Werror=non-virtual-dtor -Werror=range-loop-construct -Werror=bool-operation -Wnarrowing -Wno-missing-field-initializers -Wno-unknown-pragmas -Wno-unused-parameter -Wno-strict-overflow -Wno-strict-aliasing -Wno-stringop-overflow -Wsuggest-override -Wno-psabi -Wno-error=old-style-cast -fdiagnostics-color=always -faligned-new -Wno-maybe-uninitialized -fno-math-errno -fno-trapping-math -Werror=format -Wno-stringop-overflow
--   Shared LD flags       :  -Wl,--no-as-needed -rdynamic
--   Static LD flags       :
--   Module LD flags       :
--   Build type            : Debug
--   Compile definitions   : ONNX_ML=1;ONNXIFI_ENABLE_EXT=1;ONNX_NAMESPACE=onnx_torch;IDEEP_USE_MKL;HAVE_MMAP=1;_FILE_OFFSET_BITS=64;HAVE_SHM_OPEN=1;HAVE_SHM_UNLINK=1;HAVE_MALLOC_USABLE_SIZE=1;USE_EXTERNAL_MZCRC;MINIZ_DISABLE_ZIP_READER_CRC32_CHECKS
--   CMAKE_PREFIX_PATH     : /root/anaconda3/envs/pytorch-debug/lib/python3.13/site-packages;/root/anaconda3/envs/pytorch-debug:;/usr/local/cuda;/usr/local/cuda;/usr/local/cuda
--   CMAKE_INSTALL_PREFIX  : /root/newrec/huangruiteng/pytorch/torch
--   USE_GOLD_LINKER       : OFF
--
--   TORCH_VERSION         : 2.8.0
--   BUILD_STATIC_RUNTIME_BENCHMARK: OFF
--   BUILD_BINARY          : OFF
--   BUILD_CUSTOM_PROTOBUF : ON
--     Link local protobuf : ON
--   BUILD_PYTHON          : True
--     Python version      : 3.13.2
--     Python executable   : /root/anaconda3/envs/pytorch-debug/bin/python
--     Python library      :
--     Python includes     : /root/anaconda3/envs/pytorch-debug/include/python3.13
--     Python site-package : /root/anaconda3/envs/pytorch-debug/lib/python3.13/site-packages
--   BUILD_SHARED_LIBS     : ON
--   CAFFE2_USE_MSVC_STATIC_RUNTIME     : OFF
--   BUILD_TEST            : True
--   BUILD_JNI             : OFF
--   BUILD_MOBILE_AUTOGRAD : OFF
--   BUILD_LITE_INTERPRETER: OFF
--   INTERN_BUILD_MOBILE   :
--   TRACING_BASED         : OFF
--   USE_BLAS              : 1
--     BLAS                : mkl
--     BLAS_HAS_SBGEMM     :
--   USE_LAPACK            : 1
--     LAPACK              : mkl
--   USE_ASAN              : OFF
--   USE_TSAN              : OFF
--   USE_CPP_CODE_COVERAGE : OFF
--   USE_CUDA              : ON
--     Split CUDA          :
--     CUDA static link    : OFF
--     USE_CUDNN           : ON
--     USE_CUSPARSELT      : OFF
--     USE_CUDSS           : OFF
--     USE_CUFILE          : ON
--     CUDA version        : 12.4
--     USE_FLASH_ATTENTION : ON
--     USE_MEM_EFF_ATTENTION : ON
--     cuDNN version       : 9.8.0
--     cufile library    : /usr/local/cuda/lib64/libcufile.so
--     CUDA root directory : /usr/local/cuda
--     CUDA library        : /usr/local/cuda/lib64/stubs/libcuda.so
--     cudart library      : /usr/local/cuda/lib64/libcudart.so
--     cublas library      : /usr/local/cuda/lib64/libcublas.so
--     cufft library       : /usr/local/cuda/lib64/libcufft.so
--     curand library      : /usr/local/cuda/lib64/libcurand.so
--     cusparse library    : /usr/local/cuda/lib64/libcusparse.so
--     cuDNN library       : /usr/lib/x86_64-linux-gnu/libcudnn.so
--     nvrtc               : /usr/local/cuda/lib64/libnvrtc.so
--     CUDA include path   : /usr/local/cuda/include
--     NVCC executable     : /usr/local/cuda/bin/nvcc
--     CUDA compiler       : /usr/local/cuda/bin/nvcc
--     CUDA flags          :  -DLIBCUDACXX_ENABLE_SIMPLIFIED_COMPLEX_OPERATIONS -Xfatbin -compress-all -DONNX_NAMESPACE=onnx_torch -gencode arch=compute_90,code=sm_90 -Xcudafe --diag_suppress=cc_clobber_ignored,--diag_suppress=field_without_dll_interface,--diag_suppress=base_class_has_different_dll_interface,--diag_suppress=dll_interface_conflict_none_assumed,--diag_suppress=dll_interface_conflict_dllexport_assumed,--diag_suppress=bad_friend_decl --expt-relaxed-constexpr --expt-extended-lambda  -Wno-deprecated-gpu-targets --expt-extended-lambda -DCUB_WRAPPED_NAMESPACE=at_cuda_detail -DCUDA_HAS_FP16=1 -D__CUDA_NO_HALF_OPERATORS__ -D__CUDA_NO_HALF_CONVERSIONS__ -D__CUDA_NO_HALF2_OPERATORS__ -D__CUDA_NO_BFLOAT16_CONVERSIONS__
--     CUDA host compiler  :
--     CUDA --device-c     : OFF
--     USE_TENSORRT        :
--   USE_XPU               : OFF
--   USE_ROCM              : OFF
--   BUILD_NVFUSER         :
--   USE_EIGEN_FOR_BLAS    :
--   USE_FBGEMM            : ON
--     USE_FAKELOWP          : OFF
--   USE_KINETO            : ON
--   USE_GFLAGS            : OFF
--   USE_GLOG              : OFF
--   USE_LITE_PROTO        : OFF
--   USE_PYTORCH_METAL     : OFF
--   USE_PYTORCH_METAL_EXPORT     : OFF
--   USE_MPS               : OFF
--   CAN_COMPILE_METAL     :
--   USE_MKL               : ON
--     USE_STATIC_MKL      : OFF
--   USE_MKLDNN            : ON
--   USE_MKLDNN_ACL        : OFF
--   USE_MKLDNN_CBLAS      : OFF
--   USE_UCC               : OFF
--   USE_ITT               : ON
--   USE_NCCL              : ON
--     USE_SYSTEM_NCCL     : 1
--   USE_NNPACK            : ON
--   USE_NUMPY             : ON
--   USE_OBSERVERS         : ON
--   USE_OPENCL            : OFF
--   USE_OPENMP            : ON
--   USE_MIMALLOC          : OFF
--   USE_VULKAN            : OFF
--   USE_PROF              : OFF
--   USE_PYTORCH_QNNPACK   : ON
--   USE_XNNPACK           : ON
--   USE_DISTRIBUTED       : ON
--     USE_MPI               : OFF
--     USE_GLOO              : ON
--     USE_GLOO_WITH_OPENSSL : OFF
--     USE_TENSORPIPE        : ON
--   Public Dependencies  : caffe2::mkl
--   Private Dependencies : Threads::Threads;pthreadpool;cpuinfo;pytorch_qnnpack;nnpack;XNNPACK;microkernels-prod;fbgemm;ittnotify;fp16;caffe2::openmp;tensorpipe;nlohmann;gloo;rt;fmt::fmt-header-only;kineto;gcc_s;gcc;dl
--   Public CUDA Deps.    :
--   Private CUDA Deps.   : caffe2::curand;caffe2::cufft;caffe2::cublas;torch::cudnn;torch::cufile;__caffe2_nccl;tensorpipe_cuda;gloo_cuda;fmt::fmt-header-only;/usr/local/cuda/lib64/libcudart.so;CUDA::cusparse;CUDA::cufft;ATEN_CUDA_FILES_GEN_LIB
--   USE_COREML_DELEGATE     : OFF
--   BUILD_LAZY_TS_BACKEND   : ON
--   USE_ROCM_KERNEL_ASSERT : OFF









