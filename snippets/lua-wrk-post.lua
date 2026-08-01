-- 本地压测脚本 lua-wrk-post.lua
-- 使用方法: wrk -c <并发数> -d <持续时间> -t <线程数> -s lua-wrk-post.lua <URL>
-- 例如: wrk -c 10 -d 30s -t 4 -s lua-wrk-post.lua http://localhost:8080/api/v1/chat

-- 初始化随机数种子
math.randomseed(os.time())

-- 定义请求方法
wrk.method = "POST"

-- 定义 Header
wrk.headers["Content-Type"] = "application/json"
-- 示例 Header
wrk.headers["X-Account-Id"] = "123456789" 
wrk.headers["User-Agent"] = "wrk/benchmark"

-- 鉴权 Token (Bearer Token)
-- 如果需要通过环境变量传入，可改为 os.getenv("AUTH_TOKEN")
local auth_token = "Bearer <YOUR_TOKEN>"
wrk.headers["Authorization"] = auth_token

-- 随机 UserID 池
local user_id_pool = {
    "1001", "1002", "1003", "1004", "1005"
}

-- 请求生成函数
request = function()
    -- 构造请求体
    -- 从池子中随机选择一个 UserID
    local user_id = user_id_pool[math.random(#user_id_pool)]

    -- 模拟通用 JSON Body
    -- 示例: {"user": {"id": "1001"}, "context": {"trace_id": "trace_123456"}, "query": "benchmark_test"}
    local body_template = '{"user": {"id": "%s"}, "context": {"trace_id": "trace_%s"}, "query": "benchmark_test"}'
    
    -- 生成随机 trace_id 后缀
    local trace_suffix = tostring(math.random(100000, 999999))
    local json_body = string.format(body_template, user_id, trace_suffix)

    return wrk.format(nil, nil, nil, json_body)
end

-- 增加延时函数，强制限制发送速率 (单位: 毫秒)
-- 每次请求后暂停 50ms，限制单连接 QPS 最大为 20 (1000ms / 50ms = 20)
-- 如果不需要限速，请注释掉此函数
function delay()
    return 50
end

-- 响应处理函数
response = function(status, headers, body)
    if status ~= 200 then
        print("Error Status: " .. status)
        -- print("Error Body: " .. body) -- 调试时可打开
    end
end
