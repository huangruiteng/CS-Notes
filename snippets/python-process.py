### 关于daemon

# TORCH dataloader
     You may ask, why can't we make the workers non-daemonic, and
     gracefully exit using the same logic as we have in `__del__` when the
     iterator gets deleted (see 1 above)?

     First of all, `__del__` is **not** guaranteed to be called when
     interpreter exits. Even if it is called, by the time it executes,
     many Python core library resources may already be freed, and even
     simple things like acquiring an internal lock of a queue may hang.
     Therefore, in this case, we actually need to prevent `__del__` from
     being executed, and rely on the automatic termination of daemonic
     children.

     Thus, we register an `atexit` hook that sets a global flag
     `_utils.python_exit_status`. Since `atexit` hooks are executed in the
     reverse order of registration, we are guaranteed that this flag is
     set before library resources we use are freed (which, at least in
     CPython, is done via an `atexit` handler defined in
     `multiprocessing/util.py`
     https://github.com/python/cpython/blob/c606624af8d4cb3b4a052fb263bb983b3f87585b/Lib/multiprocessing/util.py#L320-L362
     registered when an object requiring this mechanism is first
     created, e.g., `mp.Queue`
     https://github.com/python/cpython/blob/c606624af8d4cb3b4a052fb263bb983b3f87585b/Lib/multiprocessing/context.py#L100-L103
     https://github.com/python/cpython/blob/c606624af8d4cb3b4a052fb263bb983b3f87585b/Lib/multiprocessing/queues.py#L29
     )

     So in `__del__`, we check if `_utils.python_exit_status` is set or
     `None` (freed), and perform no-op if so.

     However, simply letting library clean-up codes run can also be bad,
     because such codes (i.e., `multiprocessing.util._exit_function()`)
     include join putting threads for `mp.Queue`, which can be blocking.
     Hence, the main process putting threads are called with
     `cancel_join_thread` at creation.  See later section
     [ 3b. A process won't hang when putting into a queue; ]
     for more details.

#      As shown above, the workers are set as daemonic children of the main
    #      process. However, automatic cleaning-up of such child processes only
    #      happens if the parent process exits gracefully (e.g., not via fatal
    #      signals like SIGKILL). So we must ensure that each process will exit
    #      even the process that should send/receive data to/from it were
    #      killed, i.e.,