
*** op debug

* 命名
attn_mask = tf.concat(..., name="concat_attention_mask")

* print shape
abc = tf.Print(abc_ph, 
             [abc_ph, tf.shape(abc_ph)], 
             message='RuitengShape of abc_ph,: ', 
             summarize=100)

* print tensor
def print_tensor(name, tensor):
    with tf.device("/cpu:0"):
        print_op = tf.print(name, tensor, summarize=-1)
    with tf.control_dependencies([print_op]):
        tensor = tf.identity(tensor)
    return tensor



*** diff tensor/grad

t = tf.get_default_graph().get_tensor_by_name("model_1/debug_tensor:0")
grad_seq = tf.gradients(dummy_loss, t)



*** 详细diff

def diff_tensor(tensor1, tensor2, name, atol=1e-3, rtol=1e-3):
    # 处理框架张量（如TensorFlow/PyTorch），转换为numpy数组
    if hasattr(tensor1, 'numpy'):
        tensor1 = tensor1.numpy()
    if hasattr(tensor2, 'numpy'):
        tensor2 = tensor2.numpy()

    # 'ml_dtypes.bfloat16' abs计算有bug
    tensor1 = tensor1.astype(np.float32)
    tensor2 = tensor2.astype(np.float32)

    avg_abs_t1 = np.mean(np.abs(tensor1))
    avg_abs_t2 = np.mean(np.abs(tensor2))
    print(f"--- 量级分析 for '{name}' ---")
    print(avg_abs_t1)
    print(avg_abs_t2)
    print(f"  tensor1 平均绝对值: {float(avg_abs_t1):.6f}")
    print(f"  tensor2 平均绝对值: {float(avg_abs_t2):.6f}")
    print(f"--------------------------")
    
    # 确保两个张量形状一致
    if tensor1.shape != tensor2.shape:
        raise ValueError(f"{name}张量形状不匹配: {tensor1.shape} vs {tensor2.shape}")
    
    # 展平张量以便计算
    out1 = tensor1.flatten()
    out2 = tensor2.flatten()
    original_shape = tensor1.shape
    
    # 计算绝对误差
    abs_diff = np.abs(out1 - out2)
    
    # 核心逻辑：实现 torch.assert_close 的判断标准
    # 差异被认为是大的 (不通过)，如果它不满足: abs(a-b) <= atol + rtol * abs(b)
    large_diff_mask = abs_diff > (atol + rtol * np.abs(out2))
    large_diff_indices = np.where(large_diff_mask)[0]  # 返回所有不满足条件的展平索引
    
    # 转换为原始形状的坐标（支持任意维度）
    large_diff_coords = [np.unravel_index(idx, original_shape) for idx in large_diff_indices]
    
    # --- 以下为报告和调试信息 ---

    # 为了报告，我们仍然可以计算相对差异
    denom = np.maximum(np.abs(out1), np.abs(out2))
    relative_diff = abs_diff / np.maximum(denom, 1e-12)

    # 计算最大差异和平均差异（用于整体信息）
    if len(abs_diff) > 0:
        max_abs_diff = np.max(abs_diff)
        max_abs_diff_idx = np.argmax(abs_diff)
        relative_diff_at_max = relative_diff[max_abs_diff_idx]
        mean_relative_diff = np.mean(relative_diff)  # 计算平均相对差异

        diff_sum = np.sum(abs_diff)
        x_sum = np.sum(np.abs(out1))
        norm_diff_percent = diff_sum / (x_sum + 1e-10)
    else:
        max_abs_diff = 0
        relative_diff_at_max = 0
        mean_relative_diff = 0
        norm_diff_percent = 0
    
    # 构建调试信息
    debug_str = f"张量 {name} (atol={atol}, rtol={rtol}), 对称判断标准: abs(a-b) > atol + rtol * max(abs(a), abs(b))\n"
    debug_str += f"  整体最大元素绝对差: {float(max_abs_diff):.6f}, 对应元素相对差: {float(relative_diff_at_max):.6f}, 平均相对差: {float(mean_relative_diff):.6f}, 归一化差异: {float(norm_diff_percent):.6f}\n"
    
    # 按样本（batch index）跟踪不满足条件的元素
    sample_max_diffs = {}
    sample_max_rel_diffs = {}
    
    for coords in large_diff_coords:
        batch_idx = coords[0]
        flat_idx = np.ravel_multi_index(coords, original_shape)
        ad = abs_diff[flat_idx]
        rd = relative_diff[flat_idx]
        
        if batch_idx not in sample_max_diffs or ad > sample_max_diffs[batch_idx]:
            sample_max_diffs[batch_idx] = ad
            sample_max_rel_diffs[batch_idx] = rd
    
    # 添加样本级最大差异信息
    if sample_max_diffs:
        debug_str += f"  共 {len(sample_max_diffs)} 个样本存在差异超标的元素:\n"
        for batch_idx in sorted(sample_max_diffs.keys()):
            max_ad = sample_max_diffs[batch_idx]
            rel_at_max_ad = sample_max_rel_diffs[batch_idx]

            # 计算该样本的平均相对差异
            sample_out1 = tensor1[batch_idx].flatten()
            sample_out2 = tensor2[batch_idx].flatten()
            sample_abs_diff = np.abs(sample_out1 - sample_out2)
            sample_denom = np.maximum(np.abs(sample_out1), np.abs(sample_out2))
            sample_relative_diff = sample_abs_diff / np.maximum(sample_denom, 1e-12)
            mean_sample_rel_diff = np.mean(sample_relative_diff)

            sample_diff_sum = np.sum(sample_abs_diff)
            sample_x_sum = np.sum(np.abs(sample_out1))
            sample_norm_diff_percent = sample_diff_sum / (sample_x_sum + 1e-10)

            debug_str += f"    样本 {batch_idx}: 最大元素绝对差={float(max_ad):.6f}, 对应元素相对差={float(rel_at_max_ad):.6f}, 样本平均相对差={float(mean_sample_rel_diff):.6f}, 样本归一化差异: {float(sample_norm_diff_percent):.6f}\n"
            with np.printoptions(threshold=np.inf, linewidth=10000):
                debug_str += f"--- 样本 {batch_idx} 详细对比 (存在超标差异) ---\n"
                debug_str += f"  tensor1[{batch_idx}]:\n{tensor1[batch_idx]}\n"
                debug_str += f"  tensor2[{batch_idx}]:\n{tensor2[batch_idx]}\n"
                debug_str += f"  差异 (abs(tensor1 - tensor2))[{batch_idx}]:\n{np.abs(tensor1[batch_idx] - tensor2[batch_idx])}\n"
                debug_str += f"--- 样本 {batch_idx} 详细对比结束 ---\n"
    else:
        debug_str += "  所有元素均满足容忍度要求，无差异超标。\n"
    
    # 打印汇总信息
    print(f"输出[{name}] diff 检查完成。")
    print(debug_str)