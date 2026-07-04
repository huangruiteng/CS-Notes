# Python && LibTorch
set(ANACONDA_PYTHON_DIR "/home/$ENV{USER}/anaconda3/envs/pytorch")
if (EXISTS ${ANACONDA_PYTHON_DIR})
    message("----- ANACONDA_PYTHON_DIR: ${ANACONDA_PYTHON_DIR}")
    SET(Python3_ROOT_DIR "${ANACONDA_PYTHON_DIR}/bin/")
endif ()
find_package(Python3 3.7...3.12 COMPONENTS Interpreter Development)
include_directories(${Python3_INCLUDE_DIRS})
message("----- Python3: ${Python3_EXECUTABLE}")
message("----- Python3_INCLUDE_DIRS: ${Python3_INCLUDE_DIRS}")
execute_process(
        COMMAND ${Python3_EXECUTABLE} -c "import torch.utils; print(torch.utils.cmake_prefix_path)"
        OUTPUT_VARIABLE LIBTORCH_CMAKE_PATH
        ERROR_VARIABLE ERROR_MESSAGE OUTPUT_STRIP_TRAILING_WHITESPACE
)

if ("${LIBTORCH_CMAKE_PATH}" STREQUAL "")
    # CLion cannot find the current Python environment correctly
    # when load/reload CMake project.
    set(LIBTORCH_CMAKE_PATH "${ANACONDA_PYTHON_DIR}/lib/python3.8/site-packages/torch/share/cmake")
    message("----- We hard code LIBTORCH_CMAKE_PATH=${LIBTORCH_CMAKE_PATH}")
endif ()
set(Torch_DIR "${LIBTORCH_CMAKE_PATH}/Torch")
message("----- LibTorch CMake path: ${LIBTORCH_CMAKE_PATH}")
message("----- Torch_DIR: ${Torch_DIR}")

find_package(Torch CONFIG REQUIRED HINTS)
message("----- torch cxx flags: ${TORCH_CXX_FLAGS}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${TORCH_CXX_FLAGS}")