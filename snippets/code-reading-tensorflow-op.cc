

* Tf中的许多常用Kernel（比如Variable Op、Reshape Op等）不支持int32类型，考虑到int32常作为meta信息，不应该做h2d和d2h的操作
- https://stackoverflow.com/questions/37439299/no-gpu-kernel-for-an-int32-variable-op/37452938#37452938

REGISTER_KERNEL_BUILDER(Name("Reshape")
                            .Device(DEVICE_GPU)
                            .HostMemory("tensor")
                            .HostMemory("shape")
                            .HostMemory("output")
                            .TypeConstraint<int32>("T")
                            .TypeConstraint<int64_t>("Tshape"),
                        ReshapeOp);