*** tensor

** to方法

TensorBase TensorBase::to(
    at::TensorOptions options,
    bool non_blocking,
    bool copy,
    std::optional<at::MemoryFormat> memory_format) const {
  Tensor self(*this);
  return at::_ops::to_dtype_layout::call(
      self, optTypeMetaToScalarType(options.dtype_opt()),
      options.layout_opt(), options.device_opt(),
      options.pinned_memory_opt(), non_blocking, copy, memory_format);
}