// core/TensorImpl.*

struct C10_API TensorImpl : public c10::intrusive_ptr_target {


 protected:
  Storage storage_;

 private:
  // This pointer points to an AutogradMeta struct that stores autograd-specific
  // fields (such as grad_ / grad_fn_ / grad_accumulator_). This pointer always
  // has unique ownership (meaning only one TensorImpl can own it at a time).
  //
  // autograd_meta_ can be nullptr, as an optimization.  When this occurs, it is
  // equivalent to having an autograd_meta_ pointing to a default constructed
  // AutogradMeta; intuitively, tensors which don't require grad will have this
  // field set to null.
  //
  // This means accessors on autograd_meta_ have to be careful to test if they
  // got a nullptr, and handle default behavior appropriately in that case.
  //
  // Note that we don't enforce the invariant that if the AutogradMeta is
  // default constructed, it is nullptr (to do this, we'd have to continuously
  // check if an AutogradMeta became, by mutation, equal to the default
  // constructed form.  (This might be useful, but it seems rare enough that
  // a requires_grad=True variable will turn back into the requires_grad=False
  // version.)  So there are three representable states:
  //
  //    1. autograd_meta_ == nullptr
  //    2. autograd_meta_ is default constructed (semantically, same as (1))
  //    3. autograd_meta_ has nontrivial information content
  //
  std::unique_ptr<c10::AutogradMetaInterface> autograd_meta_ = nullptr;
};



# variable/tensor merge: https://github.com/pytorch/pytorch/issues/13638


# autograd_meta_

AutogradMetaInterface -> 

namespace impl {

namespace {
AutogradMetaFactory* meta_factory = nullptr;
} // namespace

void SetAutogradMetaFactory(AutogradMetaFactory* factory) {
  meta_factory = factory;
}
AutogradMetaFactory* GetAutogradMetaFactory() {
  TORCH_CHECK(
      meta_factory,
      "Support for autograd has not been loaded; have you linked against libtorch.so?")
  return meta_factory;
}

} // namespace impl


--> 

csrc/autograd/variable.cpp

namespace {

at::Tensor singleton_undefined_tensor;

struct ConcreteAutogradMetaFactory : public c10::impl::AutogradMetaFactory {
  std::unique_ptr<c10::AutogradMetaInterface> make() const override {
    return std::make_unique<AutogradMeta>();
  }
  const at::Tensor& undefined_tensor() const override {
    return singleton_undefined_tensor;
  }
};

ConcreteAutogradMetaFactory meta_factory;

static c10::impl::AutogradMetaFactoryRegisterer meta_factory_registerer(
    &meta_factory);

} // namespace


csrc/autograd/autograd_meta.*