docker container run -itd \
--gpus all \
--network=host \
--userns=host \
--security-opt seccomp=unconfined \
--mount type=bind,source=$(pwd),target=$(pwd) \
--mount type=bind,source=$HOME/.ssh,target=$HOME/.ssh \
--mount type=bind,source=/opt/tiger,target=/opt/tiger \
--mount type=bind,source=$HOME/.cache/bazel,target=$HOME/.cache/bazel \
-v ~/.cache/huggingface:/root/.cache/huggingface \
-v ~/.cache/pip:/root/.cache/pip \
--mount type=bind,source=/usr/local/bin/doas,target=/usr/local/bin/doas \
--mount type=bind,source=/tmp,target=/tmp \
--name $(whoami)_myproject_dev \
hub.xxx.org:xxxyyy /bin/bash


  --shm-size 32g \
  -p 30000:30000 \

# python3 -m sglang.launch_server --model-path meta-llama/llama-3.1-8b-instruct --host 0.0.0.0 --port 30000



docker ps -a

docker run -it -u `id -u`:`id -g` -v /home/$(whoami):/home/$(whoami) my_image /bin/bash
# -i 以交互模式运行容器，通常与 -t 同时使用
# -d detach模式，可稍后exec进入
# -t 为容器重新分配一个伪输入终端，通常与 -i 同时使用
# -u 表示映射账户
# -w 指定工作目录
# -v /宿主机目录:/容器目录   表示映射磁盘目录，映射的目录才会共享（将宿主机目录挂载到容器里），这里选择把user账户所有内容都映射
# --network=host/none/bridge

docker container run --name $(whoami)_workspace_xxx ...

docker container ls -a
# exec进入容器
sudo docker exec -it [-w $(pwd)] 34d2b0644938 /bin/bash
# 如果容器已经停止，需要先启动再进入
sudo docker start 34d2b0644938
# Docker 里没有 sudo组，如果需要在 docker 里安装程序，可以先使用 root 账户进入容器
sudo docker exec -it [-w $(pwd)] 34d2b0644938 /bin/bash -u root

docker logs 34d2b0
docker inspect 34d2b0



* gpu相关选项

--gpus all
--env CUDA_HOME=/opt/tiger/cuda --env NVIDIA_VISIBLE_DEVICES="all" --env NVIDIA_DRIVER_CAPABILITIES="compute,utility" --env NVIDIA_REQUIRE_CUDA="cuda>=10.1 brand=tesla,driver>=384,driver<385 brand=tesla,driver>=396,driver<397 brand=tesla,driver>=410,driver<411"




* rm docker

docker stop XXX
docker rm XXX


* 添加 docker 权限给当前用户 ，使 docker 命令免 sudo
  * [Ref](https://docs.docker.com/engine/install/linux-postinstall/)

# setup non-root docker
sudo groupadd docker
sudo usermod -aG docker $USER # add your own username, or others for them.

# activate the changes to user group
newgrp docker
# verify you can run docker without root
docker run hello-world



* Change docker's data-root into a bigger disk partition

sudo su # switch to root
vi /etc/docker/daemon.json

# copy
{
    "insecure-registries": ["$url", "$url:$port"],
    "live-restore": true,
    "data-root": "/opt/docker" // in most cases /opt is mounted at something like /data00 which is a much bigger partition
}

mkdir -p /opt/docker # in most cases /opt is mounted at something like /data00 which is a much bigger partition
systemctl restart docker


* mount
  * `--mount type=bind,source=$HOME/.cache,target=/home/$(whoami)/.cache`