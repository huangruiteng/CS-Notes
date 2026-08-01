### debugging


https://pythonspeed.com/articles/python-c-extension-crashes/

1. faulthandler

export PYTHONFAULTHANDLER=1、 Docker ENV PYTHONFAULTHANDLER=1

或

import faulthandler
faulthandler.enable()

或

https://github.com/pytest-dev/pytest-faulthandler

2. py.test -v

3. pip list
make sure to print out the packages you’ve installed at the start of each CI run

4. catchsegv py.test


### gdb

# https://stackoverflow.com/questions/1781935/get-stacktrace-from-stuck-python-process-that-does-not-accept-signals

set $gstate = ((int (*)())            PyGILState_Ensure ) ()
call          ((int (*)(const char*)) PyRun_SimpleString) ("import faulthandler; fh = open('/tmp/stacks.txt', 'w'); faulthandler.dump_traceback(file=fh); fh.close()")
call          ((void(*)(int))         PyGILState_Release) ($gstate)

### monitoring

import psutil
virtual_mem = psutil.virtual_memory()
print(f"RAM - Total: {virtual_mem.total / 1024**3:.2f} GB, "
              f"Available: {virtual_mem.available / 1024**3:.2f} GB, "
              f"Buffers: {virtual_mem.buffers / 1024**3:.2f} GB, "
              f"Cached: {virtual_mem.cached / 1024**3:.2f} GB")