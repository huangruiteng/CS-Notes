*** cuda stream

src/backend_model_instance.cc

if (kind_ == TRITONSERVER_INSTANCEGROUPKIND_GPU) {
	THROW_IF_BACKEND_INSTANCE_ERROR(
    	CreateCudaStream(device_id_, 0 /* cuda_stream_priority */, &stream_));
}