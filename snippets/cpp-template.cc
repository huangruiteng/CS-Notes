*** 模版特化 template specialization

//template for changing MAX_NUM_THREADS based on op dtype
template <typename T>
struct mnt_wrapper {
  static constexpr int MAX_NUM_THREADS = 512;
};

template <>
struct mnt_wrapper <c10::complex<double>>{
  static constexpr int MAX_NUM_THREADS = 256;
};