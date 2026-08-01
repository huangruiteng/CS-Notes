Same code gen
Cross-platform (works on Windows)
Reduced compiler dependencies
Less error-prone (warns about missing CUDA arch)
Setup-free dependency management

### usage

mkdir build && cd build
cmake ..
make -j
cd ..

### basic

cmake_minimum_required(VERSION 3.16)
project(LearnCppProject)

set(CMAKE_CXX_STANDARD 17)


# 查找 Boost 库，要求找到 system 和 thread 组件
# find_package(<PackageName> [version] [EXACT] [QUIET] [MODULE]
             # [REQUIRED] [[COMPONENTS] [components...]]
             # [OPTIONAL_COMPONENTS components...]
             # [NO_POLICY_SCOPE])
find_package(Boost 1.65.0 REQUIRED COMPONENTS system thread)

# 如果找到 Boost 库，则输出信息
if(Boost_FOUND)
    message(STATUS "Boost found: ${Boost_VERSION}")
    include_directories(${Boost_INCLUDE_DIRS})
    link_directories(${Boost_LIBRARY_DIRS})
    add_executable(MyExecutable main.cpp)
    target_link_libraries(MyExecutable ${Boost_LIBRARIES})
else()
    message(FATAL_ERROR "Boost not found")
endif()

include_directories(include)

add_executable(welcome main.cpp
        lessons/buffered_reader.cpp
        lessons/comment.cpp
        lessons/context_actions.cpp
        lessons/duplicate.cpp
        lessons/file_structure.cpp
        lessons/find_in_files.cpp
        lessons/multiple_selection.cpp
        lessons/quadratic_equations_solver.cpp
        lessons/selection.cpp
        lessons/unwrap.cpp
        BasicEditing.cpp
        CodeAssistance.cpp
        Refactorings.cpp
        Navigation.cpp
)

### CPM
拉最新的branch
> llm.cccl
include(cmake/CPM.cmake)
CPMAddPackage("gh:NVIDIA/cccl#main")
CPMAddPackage("gh:NVIDIA/nvbench#main")


### PyTorch

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