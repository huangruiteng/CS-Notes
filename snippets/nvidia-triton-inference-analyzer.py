
https://github.com/triton-inference-server/perf_analyzer/blob/main/docs/README.md

perf_analyzer -m single_gpu_1_ins -b 1 --concurrency-range 64 --max-threads 32 - u localhost:8001 -i gRPC [--input-data]