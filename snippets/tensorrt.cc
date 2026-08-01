*** TensorRT Network Definition API

IBuilder* builder = createInferBuilder(gLogger.getTRTLogger());
INetworkDefinition* network = builder->createNetwork();
ITensor* data = network->addInput(INPUT_BLOB_NAME, dt, Dims3{1, INPUT_H, INPUT_W});
IScaleLayer* scale_1 = network->addScale(*data, ScaleMode::kUNIFORM, shift, scale, power);
IConvolutionLayer* conv2 = network->addConvolution(*scale_1->getOutput(0), 50, DimsHW{5, 5}, weightMap["conv2filter"], weightMap["conv2bias"]);
conv2->setStride(DimsHW{1, 1});
ISoftMaxLayer* prob = network->addSoftMax(*conv2->getOutput(0));
prob->getOutput(0)->setName(OUTPUT_BLOB_NAME); // set output 
network->markOutput(*prob->getOutput(0)); // mark output

//序列化反序列化
IHostMemory* trtModelStream = engine->serialize(); //store model to disk
//<...>
IRuntime* runtime = createInferRuntime(gLogger.getTRTLogger());
ICudaEngine* engine = runtime->deserializeCudaEngine(trtModelStream->data(), trtModelStream->size(), nullptr);
IExecutionContext* context = engine->createExecutionContext();


*** 低精度推理

IBuilderConfig * config = builder->createBuilderConfig(); 
config->setFlag(BuilderFlag::kFP16); //INT8 and FP16 can be both set


*** TF-TRT

# Set Precision
conversion_params = trt.DEFAULT_TRT_CONVERSION_PARAMS._replace(
precision_mode=trt.TrtPrecisionMode.INT8)
# Convert to TF-TRT Graph
converter = trt.TrtGraphConverterV2(input_saved_model_dir=input_saved_model_dir, conversion_params=conversion_params)
# INT8 Calibration
converter.convert(calibration_input_fn=my_calibration_fn)
# Run Inference 
converter.save(output_saved_model_dir)