一文读懂cuda ctx by 游凯超 https://zhuanlan.zhihu.com/p/694214348


我们使用的cuda driver API始终在0号GPU上初始化，然而通过改变CUDA_VISIBLE_DEVICES，我们可以改变0号GPU对应的具体物理设备。
如果我们把os.environ['CUDA_VISIBLE_DEVICES'] = f'{target_index}'这一行代码放在libcuda.cuInit(0)之后，
我们就会发现，CUDA_VISIBLE_DEVICES环境变量不再奏效。由此我们可以确定，在cuda driver API中，cuInit负责读取CUDA_VISIBLE_DEVICES环境变量，
并负责维护GPU编号、总GPU数等状态。因此，所有的cuda driver API都必须发生在cuInit之后，否则将直接返回错误码。

driver API与runtime API完全共享状态，只是在API使用方法上有所不同

import ctypes
import pynvml

# Load the libcuda.so library
libcuda = ctypes.CDLL("libcuda.so")

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

# Step 2: Call cuInit to initialize CUDA
result = libcuda.cuInit(0)
if result != 0:
    raise Exception(f"cuInit failed with error code {result}")

# Create a context on device 0
cuDevice = ctypes.c_int()
libcuda.cuDeviceGet(ctypes.byref(cuDevice), 0)
cuContext = ctypes.c_void_p()
libcuda.cuCtxCreate(ctypes.byref(cuContext), 0, cuDevice)

# Step 3: Get bus ID using libcuda
pciBusId = ctypes.create_string_buffer(64)
libcuda.cuDeviceGetPCIBusId(pciBusId, 64, cuDevice)
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
libcuda.cuCtxDestroy(cuContext)
pynvml.nvmlShutdown()