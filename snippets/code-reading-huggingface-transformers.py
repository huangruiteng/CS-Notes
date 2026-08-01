
** 模型细节

*** kv cache

use_cache: True
max_position_embeddings: 4096  控制max len



** 模型

*** llama3

https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py


** template
- Jinja2：Python模板引擎


  {% for message in messages %}
    {{'<|im_start|>' + message['role'] + '\n' + message['content']
    + '<|im_end|>' + '\n' }}
  {% endfor %}
  {% if add_generation_prompt %}
    {{ '<|im_start|>assistant\n' }}
  {% endif %}
  ```
  <|im_start|>system
  {system_message}<|im_end|>
  <|im_start|>user
  {user_message1}<|im_end|>
  <|im_start|>assistant
  {ai_message1}<|im_end|>


模板信息存储于tokenizer_config.json中