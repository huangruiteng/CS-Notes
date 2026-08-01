
__refs/__init__.py

def flatten(a: TensorLikeType, start_dim: int = 0, end_dim: int = -1) -> TensorLikeType:
    start_dim = utils.canonicalize_dim(a.ndim, start_dim)
    end_dim = utils.canonicalize_dim(a.ndim, end_dim)

    # Short-circuits on no-op
    if start_dim == end_dim and a.ndim != 0:
        return a

    # Tries to take a view
    # TODO: we could look at directing collapse_view to skip its meta function here (unsafe_collapse_view)
    new_shape, _new_strides = prims._collapse_view_helper(a, start_dim, end_dim)
    if new_shape is not None:
        return prims.collapse_view(a, start_dim, end_dim)

    # Makes a copy if it can't make a view
    return prims.collapse(a, start_dim, end_dim)