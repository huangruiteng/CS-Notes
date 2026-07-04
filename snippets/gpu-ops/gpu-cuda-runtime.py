https://zhuanlan.zhihu.com/p/694214348

import ctypes
import pynvml

# Load the libcudart.so library
libcudart = ctypes.CDLL("libcudart.so")

# Function prototypes from libcudart
libcudart.cudaSetDevice.restype = ctypes.c_int
libcudart.cudaSetDevice.argtypes = [ctypes.c_int]
libcudart.cudaGetDevice.restype = ctypes.c_int
libcudart.cudaGetDevice.argtypes = [ctypes.POINTER(ctypes.c_int)]
libcudart.cudaDeviceGetPCIBusId.restype = ctypes.c_int
libcudart.cudaDeviceGetPCIBusId.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int]

# Step 1: Initialize NVML and list all devices, store their bus IDs
pynvml.nvmlInit()
device_count = pynvml.nvmlDeviceGetCount()
bus_ids = []
for i in range(device_count):
    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
    bus_ids.append(pynvml.nvmlDeviceGetPciInfo(handle).busId)

target_index = 3
import os
os.environ['CUDA_VISIBLE_DEVICES'] = f'{target_index}'

# Step 2: Set device using CUDA Runtime API
result = libcudart.cudaSetDevice(0)
if result != 0:
    raise Exception(f"cudaSetDevice failed with error code {result}")

# Step 3: Get bus ID using CUDA Runtime API
pciBusId = ctypes.create_string_buffer(64)
result = libcudart.cudaDeviceGetPCIBusId(pciBusId, 64, 0)
if result != 0:
    raise Exception(f"cudaDeviceGetPCIBusId failed with error code {result}")
cuda_bus_id = pciBusId.value.decode("utf-8")

# Step 4: Compare and confirm the bus ID with the one got from pynvml
pynvml_bus_id = bus_ids[target_index]  # Device bus ID from pynvml
print(f"CUDA Bus ID: {cuda_bus_id}")
print(f"PyNVML Bus ID: {pynvml_bus_id}")
if cuda_bus_id.lstrip("0") == pynvml_bus_id.lstrip("0"):
    print("Bus IDs match.")
else:
    print("Bus IDs do not match.")

# Clean up
pynvml.nvmlShutdown()