*** Intro

* PyTorch uses the operator overloading approach, which builds up a representation of the computed function every
  time it is executed.
* In its current implementation [30], PyTorch performs **reverse-mode automatic differentiation**, which computes the gradient of a scalar output with respect to a multivariate input.
  Differentiating functions with more outputs than inputs is more efﬁciently executed using forward-mode automatic differentiation, 
  but this use case is less common for machine learning applications.
  PyTorch can be easily extended to perform forward-mode differentiation using array-level dual
  numbers [31, 32].

* 细节：
- 修改tensor，有tensor version
-- Only check version counter in the case without hooks If user provides hooks, we cant track versions through the hooks
-- saved_version_ = variable._version();
-- Note [Inference tensor cannot be saved for backward]


*** Autograd Engine

csrc/autograd/python_engine.cpp
-> no python GIL

csrc/autograd/engine.*
提前scan graph决定每个task的依赖


WorkerThread

ReadyQueue
1. Evaluate function on InputBuffer (prehooks + function + posthooks)
2. Release saved variables
3. with graph lock, accumulate grad into InputBuffers of next functions, and add newly ready tasks to ReadyQueue