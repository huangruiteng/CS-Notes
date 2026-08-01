def get_completion(messages, model="gpt-3.5-turbo"):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0,
        tools=[{
            "type": "function",
            "function": {
                "name": "sum",
                "description": "计算一组数的加和",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "numbers": {
                            "type": "array",
                            "items": {
                                "type": "number"
                            }
                        }
                    }
                }
            }
        }],
        stream=True,    # 启动流式输出
    )
    return response


prompt = "1+2+3"
# prompt = "你是谁"

messages = [
    {"role": "system", "content": "你是一个小学数学老师，你要教学生加法"},
    {"role": "user", "content": prompt}
]
response = get_completion(messages)

function_name, args, text = "", "", ""

print("====Streaming====")

# 需要把 stream 里的 token 拼起来，才能得到完整的 call
for msg in response:
    delta = msg.choices[0].delta
    if delta.tool_calls:
        if not function_name:
            function_name = delta.tool_calls[0].function.name
            print(function_name)
        args_delta = delta.tool_calls[0].function.arguments
        print(args_delta)  # 打印每次得到的数据
        args = args + args_delta
    elif delta.content:
        text_delta = delta.content
        print(text_delta)
        text = text + text_delta

print("====done!====")

if function_name or args:
    print(function_name)
    print_json(args)
if text:
    print(text)