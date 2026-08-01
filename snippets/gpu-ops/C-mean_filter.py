from pathlib import Path
import torch
from torchvision.io import read_image, write_png
from torch.utils.cpp_extension import load_inline
import time


def compile_extension():
    cuda_source = Path("mean_filter_kernel.cu").read_text()
    cpp_source = "torch::Tensor mean_filter(torch::Tensor image, int radius);"

    # Load the CUDA kernel as a PyTorch extension
    rgb_to_grayscale_extension = load_inline(
        name="mean_filter_extension",
        cpp_sources=cpp_source,
        cuda_sources=cuda_source,
        functions=["mean_filter"],
        with_cuda=True,
        extra_cuda_cflags=["-O2"],
        # build_directory='./cuda_build',
    )
    return rgb_to_grayscale_extension


def main():
    """
    Use torch cpp inline extension function to compile the kernel in mean_filter_kernel.cu.
    Read input image, convert apply mean filter custom cuda kernel and write result out into output.png.
    """
    ext = compile_extension()

    x = read_image("Grace_Hopper.jpg").contiguous().cuda()
    assert x.dtype == torch.uint8
    print("Input image:", x.shape, x.dtype)

    with torch.profiler.profile() as prof:
        y = ext.mean_filter(x, 8)


    print("Output image:", y.shape, y.dtype)
    write_png(y.cpu(), "output.png")
    print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=10))


if __name__ == "__main__":
    main()
