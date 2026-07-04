import numpy as np

cache = {}

@observe()
def get_embeddings(text):
    '''封装 OpenAI 的 Embedding 模型接口'''
    if text in cache: 
        # 如果已经在缓存中，不再重复调用（节省时间、费用）
        return cache[text]
    data = openai.embeddings.create(
        input=[text], 
        model="text-embedding-3-small",
        dimensions=256
    ).data
    cache[text] = data[0].embedding
    return data[0].embedding

@observe()
def cos_sim(v, m):
    '''计算cosine相似度'''
    score = np.dot(m, v)/(np.linalg.norm(m, axis=1)*np.linalg.norm(v))
    return score.tolist()

@observe()
def check_duplicated(query, existing, threshold=0.825):
    '''通过cosine相似度阈值判断是否重复'''
    query_vec = np.array(get_embeddings(query))
    mat = np.array([item[1] for item in existing])
    cos = cos_sim(query_vec, mat)
    return max(cos) >= threshold

@observe()
def need_answer(question, outlints):
    '''判断是否需要回答'''
    langfuse_handler = langfuse_context.get_current_langchain_handler()
    return need_answer_chain.invoke(
        {"user_input": question, "outlines": outlines},
        config={"callbacks": [langfuse_handler]}
    ) == 'Y'

# 假设 已有问题
question_list = [
    ("LangChain可以商用吗", get_embeddings("LangChain可以商用吗")),
    ("LangChain开源吗", get_embeddings("LangChain开源吗")),
]


@observe()
def verify_question(
    question: str,
    outlines: str,
    question_list: list,
    user_id,
) -> bool:
    
    langfuse_context.update_current_trace(
        name="AGIClassAssistant2",
        user_id=user_id,
    )
    
    # 判断是否需要回答
    if need_answer(question,outlines):
        # 判断是否重复
        if not check_duplicated(question, question_list):
            vec = cache[question]
            question_list.append((question,vec))
            return True
    return False

ret = verify_question(
    "LangChain支持Java吗",
    # "LangChain有商用许可吗",
    outlines,
    question_list,
    user_id="wzr"
)
print(ret)

### LLamaIndex
LlamaIndexCallbackHandler