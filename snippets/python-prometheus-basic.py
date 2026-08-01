from prometheus_client import start_http_server, Counter, Gauge, Histogram
import time
import random

# 依赖: pip install prometheus-client

# 1. 定义指标 (Metrics)
# Counter: 只增不减的计数器 (e.g. 请求总数)
REQUEST_COUNT = Counter('app_request_total', 'Total application requests', ['method', 'endpoint'])
# Gauge: 可增可减的仪表盘 (e.g. 当前并发数、内存使用)
IN_PROGRESS = Gauge('app_requests_in_progress', 'Number of requests currently in progress')
# Histogram: 柱状图，用于统计分布 (e.g. 延迟、响应大小)
LATENCY = Histogram('app_request_latency_seconds', 'Request latency in seconds')

def process_request():
    """模拟业务请求处理"""
    # 记录并发数 +1
    IN_PROGRESS.inc()
    
    start_time = time.time()
    
    # 模拟处理耗时
    time.sleep(random.uniform(0.1, 0.5))
    
    # 记录业务指标
    REQUEST_COUNT.labels(method='GET', endpoint='/api/data').inc()
    
    # 记录延迟
    LATENCY.observe(time.time() - start_time)
    
    # 记录并发数 -1
    IN_PROGRESS.dec()

if __name__ == '__main__':
    # 2. 启动 HTTP Server 暴露 Metrics
    # Prometheus Server 会通过 Pull 模式访问此端口
    PORT = 2023
    start_http_server(PORT)
    
    print(f"Prometheus Metrics Server started at: http://localhost:{PORT}/metrics")
    print(f"Verify locally with command: curl localhost:{PORT}/metrics")
    print("Simulating traffic... (Press Ctrl+C to stop)")

    # 3. 模拟持续产生数据
    while True:
        process_request()
        time.sleep(1)
