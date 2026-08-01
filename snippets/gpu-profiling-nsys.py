https://developer.nvidia.com/nsight-systems/get-started

options解释：https://docs.nvidia.com/nsight-systems/UserGuide/index.html#gms-introduction


nsys profile --delay=60 --duration=30 --stats=true --force-overwrite=true --export=json --output=~/profile_results/nsight_report-$(date +"%s") \
--trace=cuda,nvtx,osrt,cudnn,cublas ./output

# --gpu-metrics-device=all