*** llm.cccl

train_gpt2cu: train_gpt2.cu
	nvcc -O3 --use_fast_math $< -lcublas -lcublasLt -o $@

如果 train_gpt2cu 这个目标文件不存在，或者其依赖文件 train_gpt2.cu 比它更新，那么就执行以下命令： nvcc -O3 --use_fast_math train_gpt2.cu -lcublas -lcublasLt -o train_gpt2cu
$< : 这是一个 Makefile 中的自动变量，它代表规则中的 第一个依赖项 。在这个例子中，它会被替换为 train_gpt2.cu
$@: 是 Makefile 中的另一个自动变量，它代表规则的 目标名称 。在这个例子中，它会被替换为 train_gpt2cu


*** PyTorch

# This makefile does nothing but delegating the actual building to cmake.
PYTHON = python3
PIP = $(PYTHON) -m pip
NIGHTLY_TOOL_OPTS := pull

all:
	@mkdir -p build && cd build && cmake .. $(shell $(PYTHON) ./scripts/get_python_cmake_flags.py) && $(MAKE)

local:
	@./scripts/build_local.sh

android:
	@./scripts/build_android.sh

ios:
	@./scripts/build_ios.sh

clean: # This will remove ALL build folders.
	@rm -r build*/

linecount:
	@cloc --read-lang-def=caffe.cloc caffe2 || \
		echo "Cloc is not available on the machine. You can install cloc with " && \
		echo "    sudo apt-get install cloc"

ensure-branch-clean:
	@if [ -n "$(shell git status --porcelain)" ]; then \
		echo "Please commit or stash all changes before running this script"; \
		exit 1; \
	fi

setup-env: ensure-branch-clean
	$(PYTHON) tools/nightly.py $(NIGHTLY_TOOL_OPTS)

setup-env-cuda:
	$(MAKE) setup-env PYTHON="$(PYTHON)" NIGHTLY_TOOL_OPTS="$(NIGHTLY_TOOL_OPTS) --cuda"

setup-env-rocm:
	$(MAKE) setup-env PYTHON="$(PYTHON)" NIGHTLY_TOOL_OPTS="$(NIGHTLY_TOOL_OPTS) --rocm"

setup_env: setup-env
setup_env_cuda: setup-env-cuda
setup_env_rocm: setup-env-rocm

setup-lint:
	$(PIP) install lintrunner
	lintrunner init

setup_lint: setup-lint

lint:
	lintrunner

quicklint:
	lintrunner

triton:
	$(PIP) uninstall -y triton
	@./scripts/install_triton_wheel.sh
