[toc]

### ansible

```
ansible $host -u tiger -f 100 -T 60 -mshell -a 'bash -x /path/test.sh' -e "ansible_shell_executable=/bin/bash""
```

* Ansible 是一种自动化工具，它基于 SSH（Secure Shell）协议来实现系统配置和管理。下面是关于 Ansible 基于 SSH 协议的解释和理解：
  * 远程执行：Ansible 使用 SSH 协议与远程主机进行通信，通过在远程主机上执行命令和任务来实现自动化配置和管理。SSH 是一种安全的远程登录协议，它提供了加密的通信通道，确保数据的机密性和完整性。
  * 无需代理：与其他自动化工具不同，Ansible 不需要在远程主机上安装和配置任何额外的代理程序或客户端。它利用 SSH 协议本身的功能，直接与目标主机进行通信，并执行所需的操作。这简化了部署和管理过程，减少了对目标主机的依赖性和配置要求。
  * 无需持久连接：Ansible 采用基于 SSH 的无需持久连接的模型。这意味着 Ansible 在执行任务时，会建立一个临时的 SSH 连接到远程主机上，执行任务后立即断开连接。这种模型避免了长时间保持连接的开销和管理复杂性，并提供了更好的灵活性和可伸缩性。
  * 身份验证和授权：SSH 协议提供了多种身份验证方法，包括密码、公钥和证书等。Ansible 可以利用这些身份验证方法来连接和认证远程主机。此外，Ansible 还支持使用 SSH Agent 来管理和传递身份验证凭据，以提供更便捷和安全的身份验证方式。
  * 并行执行：Ansible 基于 SSH 协议实现了高度并行的任务执行。它可以同时与多个远程主机建立 SSH 连接，并在这些主机上并行执行任务，从而提高执行效率和速度。

* 总结起来，Ansible 基于 SSH 协议使得远程主机之间的自动化配置和管理变得简单、安全和高效。它利用 SSH 的加密通信和身份验证机制，无需额外的代理程序，实现了远程主机的批量操作和任务执行。

* jinja2(j2)语法
  * https://ansible.leops.cn/basic/Jinja2/
* Issue
  * “In **non** docker environment, these "left behind" processes are picked up by init process, which is capable of reaping zombies. In docker setup the solution is to add `init: true` into docker-compose, to enable init process inside docker.”
    * https://github.com/ansible/ansible/issues/49270
  


### log4j

```properties
# 业务日志
log4j.rootLogger=INFO,R

log4j.appender.stdout=org.apache.log4j.ConsoleAppender
log4j.appender.stdout.layout=org.apache.log4j.PatternLayout
log4j.appender.stdout.layout.ConversionPattern=%d %5p %m (%F:%L)%n

log4j.appender.R=org.apache.log4j.DailyRollingFileAppender
log4j.appender.R.File=/folder/service.log
log4j.appender.R.DatePattern=.yyyy-MM-dd_HH
log4j.appender.R.BufferedIO=false
log4j.appender.R.MaxBackupIndex=36
log4j.appender.R.Threshold=INFO
log4j.appender.R.layout=org.apache.log4j.PatternLayout
log4j.appender.R.layout.ConversionPattern=%d %5p %m%n

# 服务化平台日志
log4j.logger.RpcCall=TRACE,Call

log4j.appender.Call=org.apache.log4j.DailyRollingFileAppender
log4j.appender.Call.File=/folder/service.call.log
log4j.appender.Call.DatePattern=.yyyy-MM-dd_HH
log4j.appender.Call.BufferedIO=false
log4j.appender.Call.MaxBackupIndex=36
log4j.appender.Call.layout=org.apache.log4j.PatternLayout
log4j.appender.Call.layout.ConversionPattern=%p %d{yyyy-MM-dd HH:mm:ss} %F:%L %m%n

log4j.logger.RpcAccess=TRACE,Access

log4j.appender.Access=org.apache.log4j.DailyRollingFileAppender
log4j.appender.Access.File=/folder/service.access.log
log4j.appender.Access.DatePattern=.yyyy-MM-dd_HH
log4j.appender.Access.BufferedIO=false
log4j.appender.Access.MaxBackupIndex=36
log4j.appender.Access.layout=org.apache.log4j.PatternLayout
log4j.appender.Access.layout.ConversionPattern=%p %d{yyyy-MM-dd HH:mm:ss} %F:%L %m%n
```

### protobuf

见【code-reading笔记】

#### ProtoJSON 的 64 位整数

- 当业务对象的 `to_json()` 先用 `MessageToDict()` 把 Protobuf message 转成
  `dict` 时，输出遵循 ProtoJSON 映射，而不是普通 Python `dict` 的直觉。
- 关键坑：`int64`、`uint64`、`fixed64` 等 64 位整数在 ProtoJSON 中会转成
  十进制字符串，例如 `"123"`。这是为了避免 JSON number 在 JavaScript 等环境里
  丢失整数精度。
- 排查配置 / 特征导出问题时，不要先假设类型被业务代码改坏；先确认这是不是
  Protobuf JSON 规范导致的类型变化。需要数值计算时，在消费端显式转回整数。
- 来源：Protocol Buffers 官方 ProtoJSON mapping：
  https://protobuf.dev/programming-guides/json/

### grafana

* 如何在同一个panel中使用不同的纵轴
  * 设置 Left Y 和 Right Y
    *  `Percent (0.0-1.0)`
    * `time: YYYY-MM-DD HH`
  * 设置 Series overrides
    * Alias or regex: `/MyMetric.*/`
      * `Y-axis: 2`

### glog

https://github.com/google/glog



### grpc

* debug

```python
os.environ['GRPC_VERBOSITY'] = 'DEBUG'
os.environ['GRPC_TRACE'] = 'all'
```

* 坑
  * failed to pick subchannel
    * https://github.com/grpc/grpc/issues/23340
    * https://stackoverflow.com/questions/69444526/python-grpc-failed-to-pick-subchannel

### Hadoop

Hadoop Shell 命令：https://hadoop.apache.org/docs/r1.0.4/cn/hdfs_shell.html

```shell
hadoop fs -test -e filename

hadoop fs -ls -h
hadoop fs -ls hdfs://abc/def/*/*/models/*/model.pb # 可匹配

hadoop fs -du -h
hadoop fs -get ... .
-mkdir
-cp

hadoop fs -copyToLocal <HDFS文件路径> <本地文件路径>
```

* 设置 JVM 的最大堆内存限制

```
LIBHDFS_OPTS = [
        os.environ.get('HADOOP_ROOT_LOGGER',
                       '-Dhadoop.root.logger=WARN,console'), "-Xmx4096m"
    ]
os.environ["LIBHDFS_OPTS"] = ' '.join(LIBHDFS_OPTS)
```

### Redis

* [redis.clients.jedis.exceptions.JedisClusterException: CLUSTERDOWN The cluster is down](https://github.com/redis/jedis/issues/2144#top)

### thrift

```shell
brew install thirft@0.9
thrift -version

If you need to have thrift@0.9 first in your PATH, run:
  echo 'export PATH="/usr/local/opt/thrift@0.9/bin:$PATH"' >> ~/.zshrc

For compilers to find thrift@0.9 you may need to set:
  export LDFLAGS="-L/usr/local/opt/thrift@0.9/lib"
  export CPPFLAGS="-I/usr/local/opt/thrift@0.9/include"

For pkg-config to find thrift@0.9 you may need to set:
  export PKG_CONFIG_PATH="/usr/local/opt/thrift@0.9/lib/pkgconfig"
```



```python
# easy thrift client
def _retry(self, func, req, times=5):
  for _ in range(times):
    try:
      resp = getattr(self._client, func)(req)
      if resp.BaseResp.StatusCode == 0:
        return resp
      err = resp.BaseResp.StatusMessage
    except Exception as e:
      err = repr(e)
    logging.warning('%s errored with %s', func, err)
    time.sleep(random.random() * 3)
    self.reset_client()
  raise RuntimeError(err)
```

```c++
if (!info.fromJsonString(str)) {
  if (!info.fromBinaryString(str)) {
    ...
  }
}
```



### YAML

* 基础语法

```yaml
# - 表示数组
series:
	- target:
		actions:
  - target:
  	actions:
```



* multiple documents in the same stream
  * https://stackoverflow.com/questions/50788277/why-3-dashes-hyphen-in-yaml-file

```yaml
doc 1
...
%TAG !bar! !bar-types/
---
doc 2
```

```python
# conf读取
import yaml
confs = list(yaml.safe_load_all(f))
custom_conf = confs[0]

# merge conf
def _merge_conf(custom_conf: dict, default_conf: dict):
    new_conf = copy.deepcopy(default_conf)
    for k, custom_v in custom_conf.items():
        if isinstance(custom_v, dict):
            new_conf[k] = _merge_conf(custom_v, default_conf.get(k, {}))
        elif k not in new_conf or new_conf[k] is None or isinstance(custom_v, list):
            new_conf[k] = custom_v
        elif isinstance(new_conf[k], bool):
            new_conf[k] = custom_v in (True, 'True', 'true', 'TRUE', 't', '1')
        else:
            new_conf[k] = type(new_conf[k])(custom_v)
    return new_conf
```


