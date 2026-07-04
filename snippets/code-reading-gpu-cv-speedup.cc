Generic Vertical Fusion (GVF)
Divergent Horizontal Fusion (DHF)
Backwards Generic Vertical Fusion (BGVF)
Automatic Thread Coarsening (ATC)


cvGS::CircularTensor<InputCVType, CircularTensorCVType, NUM_CHANNELS, BATCH,
					cvGS::CircularTensorOrder::NewestFirst> myTensor(WIDTH, HEIGHT);
myTensor.update(cv_stream,
				cvGS::resize<…>(newImage, …),
				cvGS::convertTo<…>(…),
				cvGS::split<…>(myTensor.ptr().data)); // We may look for a way to avoid this
// Now you can send the raw data to inference
network.forward(myTensor.ptr().data, cv_stream);


using HowToReadAPixel = Binary<ReadYUV<NV12>, ConvertYUVToRGB<NV12, Full, bt709, AddAlpha, float4>, ImageProcA<float4>>;
HowToReadAPixel readDF;
get_params<0>(readDF) = d_nv12Image; // Source 8K image (ReadYUV Device Function)
get_params<2>(readDF) = imgProcAParams; // Parameters required by the ImageProcA Device Function.
// Applying Backwards Generic Vertical Fussion (BGVF)
auto howToInterpolateAPixelDF = resize<HowToReadAPixel, INTER_LINEAR>(readDF.params,
																		Size(d_nv12Image.dims().width, d_nv12Image.dims().height),
																		Size(targetWidth, targeHeight));


// Not present in the OpenSource library, approximated code, more BGVF
auto howToTransformAPixelDF = geometryFuntionBuilder(howToInterpolateAPixelDF, stitchParams);
auto generateOutputImageWithScoreBoardDF = scoreBoardFunctionBuilder(howToTransformAPixelDF, scoreBoardParams);
// Launch a single CUDA kernel, that does everything
executeOperations(stream, generateOutputImageWithScoreBoardDF, // Generic Vertical Fusion after the BGVF
					Binary<ConvertRGBAToYUV<…>>{},
					Write<ChromaSubSampling<NV12>,…>>{d_outputImage});