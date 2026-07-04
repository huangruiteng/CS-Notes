*** 容器

https://catalog.ngc.nvidia.com/orgs/nvidia/containers/tritonserver/tags



*** launch tritonserver

$ docker run --gpus all -it --rm --name triton_server_hrt --net host --shm-size=1g -p8001:8001 -p8002:8002 -p8000:8000 \
-v <host_model_repo>:<container_model_repo> \
 nvcr.io/nvidia/tritonserver:21.07-py3

--gpus '"device=0"'


tritonserver --model-repository=/path [--strict-model-config=false] --repository-poll-secs=15
tritonserver --help

- 检查健康状态
  curl -v <Server IP>:8000/v2/health/ready 



--pinned-memory-pool-byte-size <integer>
total byte size that can be allocated as pinned system memory whiich is used for accelerating data transfer between host and devices 
Default is 256M.

--cuda-memory-pool-byte-size <<integer>:<integer>>
total byte size that can be allocated as CUDA memory for theGPU device. Default is 64M.

--backend-directory <string>
The global directory searched for backend shared libraries.
Default is '/opt/tritonserver/backends'.

--repoagent-directory <string>
The global directory searched for repository agent sharedlibraries
Default is '/opt/tritonserver/repoagents'.


*** config.pbtxt

name: "resnet50_trt"
platform: "tensorrt_plan"
max_batch_size : 8
input [
	{
		name: "input"
		data_type: TYPE_FP32
		format: FORMAT_NCHW
		dims: [ 3, 256, 256 ]
	}
]
output [
	{
		name: "output"
		data_type: TYPE_FP32
		dims: [ 1000 ]
		label_filename: "labels.txt"
	}
]
 
Necessary Parameters
- platform / backend: to define which backend to use
- max_batch_size
- input and output

TensorRT, TensorFlow saved-model, and ONNX models do nnot require config.pbtxt when --strict-model-config=false

- dims不包括batch size维
- max_batch_size可以为0
- libtorch -1可变长
- torch script: INPUT__0
- dims后面可以配置 reshape { shape: [1, 3, 224, 224] }


dynamic_batching {
	preferred_batch_size: [ 2, 4 ]
	max_queue_delay_microseconds: 100
}

- preserve_ordering
- priority_levels
- Queue Policy


version_policy:{ all{}}
version_policy:{latest {num_versions: 1}}
version_policy:{specific { versions:1,2}}

instance_group [
count:2
kind: KIND_CPU

count:1
kind: KIND_GPU
gpus: [ 0 ]

count:2
kind: KIND_GPU
gpus: [ 1, 2 ]

]

- 不指定GPU号，默认在每个GPU上一个instance


optimization { execution_accelerators
gpu_execution_accelerator : [ {
name : "tensorrt"
parameters { key: "precision_mode" value: "FP16"
}}]
}

model_warmup [{
batch_size: 64
name: "warmup_requests"
inputs {
	key: "input"
	value:{
	random_data: true
	dims: [ 299, 299,3]
	data_type: TYPE_FP32
}
}]



* 显式加载
--model-control-mode explicit
curl -X POST http://localhost:8000/v2/repository//models/cpu_1_ins/load  (unload)



*** Send Requests to Triton Server

pip3 install tritonclient[all]

sync/async/streaming 三种模式

import tritonclient.grpc as grpcclient

# 1. 创建推理服务器客户端
# FLAGS.url 应该是 "localhost:8001" 或服务器的实际地址
# FLAGS.verbose 用于打印详细的通信日志
triton_client = grpcclient.InferenceServerClient(url=FLAGS.url, verbose=FLAGS.verbose)

# 2. 获取模型的元数据和配置信息
# 这是可选的，但有助于动态地构建请求
model_metadata = triton_client.get_model_metadata(
    model_name=FLAGS.model_name, model_version=FLAGS.model_version
)
model_config = triton_client.get_model_config(
    model_name=FLAGS.model_name, model_version=FLAGS.model_version
)

# 3. 解析模型信息 (这是一个自定义函数，非tritonclient库内容)
# 从元数据和配置中提取输入/输出名称、形状、数据类型等
max_batch_size, input_name, output_name, c, h, w, format, dtype = parse_model(
    model_metadata, model_config
)

# 4. 准备输入数据
# 假设这是一个读取并预处理图片的自定义函数
batched_image_data = read_image_data_from_files(filenames)

# 5. 构造请求的输入和输出对象
# 创建输入张量对象
inputs = [
    grpcclient.InferInput(input_name, batched_image_data.shape, dtype)
]
# 将Numpy数组形式的数据填充到输入张量中
inputs[0].set_data_from_numpy(batched_image_data)

# 创建输出张量请求对象
outputs = [
    grpcclient.InferRequestedOutput(output_name, class_count=FLAGS.classes)     # 分类模型，根据label将概率转化为类别
]

# (可选) 准备异步请求列表
requests = []
responses = []

# 6. 发送推理请求 (同步方式)
# 这是一个阻塞调用，会一直等待直到收到服务器的响应
response = triton_client.infer(
    model_name=FLAGS.model_name,
    inputs=inputs,
    request_id=str(sent_count),  # sent_count 似乎是一个循环计数器
    model_version=FLAGS.model_version,
    outputs=outputs
)

# 7. 处理响应
# 从响应中以Numpy数组的形式获取指定的输出张量
output_array = response.as_numpy(output_name)

# 8. 对推理结果进行后处理
# 这是一个自定义函数，例如解析分类结果、绘制边界框等
post_processing(output_array)


** async client

class UserData:
	def __init__(self):
		self._completed_requests=queue.Queue()

# Callback function used for async_stream_infer()
def completion_callback(user_data, result,error):
	# passing error raise and handling out
	user_data._completed_requests.put((result,error))

inputs = [client.Inferinput(input_name, batched_image_data.shape, dtype)]
inputs[0].set_data_from_numpy(batched_image_data)
outputs = [client.InferRequestedOutput(output_name, class_count=FLAGS.classes)]
triton_client.async_infer(FLAGS.model_name, inputs,
	partial(completion_callback, user_data),
	request_id=str(sent_count),
	model_version=FLAGS.model_version,
	outputs=outputs)
(response, error)=user_data._completed_requests.gget()
output_array = response.as_numpy(output_name)
post_processing(output_array)


if FLAGS.protocol.lower() == "grpc":
    processed_count = 0
    while processed_count < sent_count:
        (results, error) = user_data._completed_requests.get()
        processed_count += 1
        if error is not None:
            print("inference failed: " + str(error))
            sys.exit(1)
        responses.append(results)
else:
    # Collect results from the ongoing async requests for HTTP Async requests.
    for async_request in async_requests:
        responses.append(async_request.get_result())

# Process each response
for response in responses:
    if FLAGS.protocol.lower() == "grpc":
        this_id = response.get_response().id
    else:
        this_id = response.get_response()["id"]
    print("Request {}, batch size {}".format(this_id, FLAGS.batch_size))
    postprocess(response, output_name, FLAGS.batch_size, max_batch_size > 0)


*** send through shared memory

- register_cuda_shared_memory (要额外传入参数，设置gpu0)

import tritonclient.grpc as grpcclient
import tritonclient.utils.shared_memory as shm
import tritonclient.utils.cuda_shared_memory as cudashm
import numpy as np
from your_module import read_image_data_from_files  # 需自行实现读取图像数据的函数

# 初始化Triton gRPC客户端
triton_client = grpcclient.InferenceServerClient(url="localhost:8001")

# 取消注册已有共享内存（若存在）
triton_client.unregister_system_shared_memory()
triton_client.unregister_cuda_shared_memory()

# 读取并预处理图像数据
filenames = ["image1.jpg", "image2.jpg"]  # 示例输入图像文件列表
batched_image_data = read_image_data_from_files(filenames)  # 返回形状如 [batch, 3, 256, 256] 的numpy数组
input_byte_size = batched_image_data.size * batched_image_data.itemsize
input_dtype = np.float32  # 假设输入数据类型为float32
input_name = "input"
output_name = "output"
model_name = "resnet50_trt"  # 模型名称
FLAGS = type("FLAGS", (object,), {"classes": 1000})()  # 假设类别数为1000


# 计算输出共享内存大小（以ResNet50输出1000类为例）
batch_size = batched_image_data.shape[0]
output_shape = [batch_size, FLAGS.classes]
output_byte_size = np.prod(output_shape) * np.dtype(np.float32).itemsize


# 创建并注册**输出系统共享内存**
shm_op_handle = shm.create_shared_memory_region(
    "output_data", "/output_simple", output_byte_size
)
triton_client.register_system_shared_memory(
    "output_data", "/output_simple", output_byte_size
)


# 创建并注册**输入CUDA共享内存**
shm_ip_handle = cudashm.create_shared_memory_region(
    "input_data", "/input_simple", input_byte_size
)
shm.set_shared_memory_region(shm_ip_handle, [batched_image_data])
triton_client.register_cuda_shared_memory(
    "input_data", "/input_simple", input_byte_size
)


# 构建推理输入输出
inputs = []
inputs.append(
    grpcclient.InferInput(
        input_name,
        batched_image_data.shape,
        grpcclient.utils.triton_to_np_dtype(input_dtype)
    )
)
inputs[-1].set_shared_memory("input_data", input_byte_size)

outputs = []
outputs.append(
    grpcclient.InferRequestedOutput(
        output_name,
        class_count=FLAGS.classes
    )
)
outputs[-1].set_shared_memory("output_data", output_byte_size)


# 发送推理请求
results = triton_client.infer(
    model_name=model_name,
    inputs=inputs,
    outputs=outputs
)


# 读取输出并后处理
output = results.get_output(output_name)
output_data = shm.get_contents_as_numpy(
    shm_op_handle,
    grpcclient.utils.triton_to_np_dtype(output.datatype),
    output.shape
)

def post_processing(data):
    # 示例后处理：获取每批数据的Top1类别
    top1_classes = np.argmax(data, axis=1)
    print("Top 1 Classes:", top1_classes)

post_processing(output_data)

