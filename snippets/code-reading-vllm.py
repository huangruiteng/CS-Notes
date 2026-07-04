https://docs.vllm.ai/en/stable/getting_started/installation.html

支持distributed serving


*** 主流程

** vllm/v1/worker/gpu_worker.py

determine_available_memory, for KV cache大小预估


*** 优化

pad_for_cudagraph



*** spec_decode

vllm/v1/spec_decode/metrics.py

draft_acceptance_rate = (num_accepted_tokens / num_draft_tokens *
                                 100 if num_draft_tokens > 0 else float("nan"))

- Spec decode framework is complete with correctness tests
- Supports draft model, ngram, Medusa (soon), IBM’s MLPSpeculator (soon)
- Other features like skipping speculation for some sequences, dynamic speculative decoding
- Missing performance optimizations to achieve Anyscale’s internal fork performance
- https://github.com/vllm-project/vllm/issues/4630 
- Llama2 70B 50% ITL reduction on BS=1..8 with temperature 1.0


** main procedure

vllm/v1/worker/gpu_model_runner.py

self.speculative_config相关逻辑


执行顺序可以理解为一个持续的循环：
1. （上一步的） rejection_sampler ：根据目标模型的验证结果，确定上一批起草的词元中哪些被接受，从而更新当前的“已确认序列”。
2. （当前步的） drafter.propose ：基于这个更新后的“已确认序列”，起草模型生成新的一批候选词元。
3. （当前步的）目标模型验证：目标模型评估这些新的候选词元。
4. （下一步开始时） rejection_sampler ：处理当前步的验证结果... 如此循环往复

def execute_model
	# rejection sampler

	if spec_decode_metadata is None:
        sampler_output = self.sampler(
            logits=logits,
            sampling_metadata=sampling_metadata,
        )
    else:
        # When indexing with a tensor (bonus_logits_indices), PyTorch
        # creates a new tensor with separate storage from the original
        # logits tensor. This means any in-place operations on bonus_logits
        # won't affect the original logits tensor.
        assert logits is not None
        bonus_logits = logits[spec_decode_metadata.bonus_logits_indices]
        sampler_output = self.sampler(
            logits=bonus_logits,
            sampling_metadata=sampling_metadata,
        )
        bonus_token_ids = sampler_output.sampled_token_ids

        # Just like `bonus_logits`, `target_logits` is a new tensor with
        # separate storage from the original `logits` tensor. Therefore,
        # it is safe to update `target_logits` in place.
        target_logits = logits[spec_decode_metadata.target_logits_indices]
        output_token_ids = self.rejection_sampler(
            spec_decode_metadata,
            None,  # draft_probs
            target_logits,
            bonus_token_ids,
            sampling_metadata,
        )
        sampler_output.sampled_token_ids = output_token_ids


     # draft model
     drafter.propose(...
     spec_token_ids = ...


# NOTE(Jiayi): currently we put the entire draft model on
# the last PP rank. This is not ideal if there are many
# layers in the draft model.
if self.speculative_config and get_pp_group().is_last_rank:
    if self.speculative_config.method == "ngram":
        self.drafter = NgramProposer(self.vllm_config)
    elif self.speculative_config.use_eagle():
        self.drafter = EagleProposer(self.vllm_config, self.device,
                                     self)  # type: ignore
        if self.speculative_config.method == "eagle3":
            self.use_aux_hidden_state_outputs = True
    elif self.speculative_config.method == "medusa":
        self.drafter = MedusaProposer(
            vllm_config=self.vllm_config,
            device=self.device)  # type: ignore
    else:
        raise ValueError("Unknown speculative decoding method: "
                         f"{self.speculative_config.method}")
    self.rejection_sampler = RejectionSampler()

** drafter

* ngram

vllm/v1/spec_decode/ngram_proposer.py
- kmp算法，根据上下文进行基础推测

* eagle

class EagleProposer:

	for _ in range(self.num_speculative_tokens - 1):

deepseek_mtp

* medusa

https://github.com/vllm-project/vllm/issues/5015

** rejection sampling

https://github.com/vllm-project/vllm/pull/2336

vllm/v1/sample/rejection_sampler.py

- Accepted tokens (接受的词元) : 基于“原始”草稿概率和目标概率之间的关系而被接受的词元。
- Recovered tokens (恢复的词元) : 基于调整后的概率分布（源自草稿和目标概率）采样的词元。当草稿词元被拒绝时，会尝试从这个调整后的分布中采样一个新词元。
	- 核心思想是从一个调整后的概率分布 P_recovery = (P_target - P_draft)+ 中采样。
	- 其中 P_target 是目标模型的概率分布， P_draft 是提议模型的概率分布。 + 下标表示取正部分（即 max(0, value) ），然后进行归一化。
- Bonus tokens (奖励词元) : 如果所有提出的草稿词元都被接受，则在序列末尾添加奖励词元。奖励词元仅从目标概率中采样。代码中，奖励词元是外部传入的，而不是在拒绝采样器内部采样，这为奖励词元的采样策略（如 top-p, top-k）提供了更大的灵活性。
- Output tokens (输出词元) : 最终由拒绝采样器生成的词元，是接受词元、恢复词元和奖励词元的组合。
- PLACEHOLDER_TOKEN_ID : 一个特殊值（-1），用于标记被拒绝或无效的词元位置。
- MAX_SPEC_LEN : 单个步骤中每个请求允许的最大推测草稿词元数。

sample_recovered_tokens_kernel
	如何理解Gumbel-Max trick？ - SleepyBag的回答 - 知乎
	https://www.zhihu.com/question/62631725/answer/507940806

** batch expansion

vllm/spec_decode/batch_expansion.py

** tests

tests/spec_decode/e2e/test_multistep_correctness.py

Problem: How can we validate correctness of spec decode?

E2E: When temperature==0, we expect equality with and without spec decode
Rejection sampler unit tests (output distribution does not change regardless of draft/target probabilities))

https://github.com/vllm-project/vllm/tree/main/tests/spec_decode 
https://github.com/vllm-project/vllm/tree/main/tests/spec_decode/e2e 

