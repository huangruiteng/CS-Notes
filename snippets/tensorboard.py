
# -*- coding: utf-8 -*-

# ==============================================================================
# 1. PyTorch 中 TensorBoard 的基础用法
# ==============================================================================
import os
from datetime import datetime
import numpy as np
from torch.utils.tensorboard import SummaryWriter


def pytorch_basic_usage():
    """演示在 PyTorch 中使用 TensorBoard 的基本流程。"""
    # --- 1. 初始化 SummaryWriter ---
    # 日志会保存在类似 'runs/my_experiment/20231107-123456' 的目录中
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_dir = os.path.join("runs", "my_experiment", timestamp)
    writer = SummaryWriter(log_dir=log_dir)
    print(f"TensorBoard 日志将保存在: {log_dir}")

    # --- 2. 记录超参数 (使用 add_text) ---
    hparams = {
        'lr': 1e-4,
        'batch_size': 64,
        'epochs': 10
    }
    # 将超参数格式化为 Markdown 文本
    hparams_str = "## Hyperparameters\n" + "\n".join([f"- **{k}**: {v}" for k, v in hparams.items()])
    writer.add_text('Hyperparameters', hparams_str, 0)

    # --- 3. 在训练循环中记录指标 (如 loss) ---
    print("开始模拟训练并记录指标...")
    loss = 0.0
    for epoch in range(hparams['epochs']):
        for step in range(100):  # 模拟数据加载
            global_step = epoch * 100 + step
            # 模拟损失计算
            loss = 0.1 + (0.9 - 0.1) * np.exp(-global_step / 200)
            
            # 使用 add_scalar 记录标量值
            writer.add_scalar('Loss/train', loss, global_step)
            writer.add_scalar('LearningRate', hparams['lr'], global_step)

    # --- 4. (可选) 记录最终指标和超参数的对应关系 (使用 add_hparams) ---
    # 这对于在 TensorBoard 中比较不同实验非常有用
    final_accuracy = 0.95  # 假设的最终准确率
    writer.add_hparams(
        hparam_dict=hparams,
        metric_dict={'hparam/accuracy': final_accuracy, 'hparam/final_loss': loss}
    )

    # --- 5. 关闭 writer ---
    writer.close()
    print("训练完成，日志已保存。")
    print(f"在终端中运行 'tensorboard --logdir=runs' 来启动 TensorBoard。")


# ==============================================================================
# 2. 命令行用法
# ==============================================================================
"""
# 启动 TensorBoard 服务
# --logdir 指向包含所有实验日志的父目录 (例如 'runs')
# --bind_all 使其可以被局域网内的其他机器访问
tensorboard --logdir runs --bind_all

# 检查单个事件文件的内容
tensorboard --inspect --event_file=path/to/your/events.out.tfevents.xxxxx
"""

# ==============================================================================
# 3. 使用 TensorFlow 读取事件文件中的 Tensor 数据
# ==============================================================================
import tensorflow as tf

def read_tensor_from_event_file(event_file_path, tensor_tag):
    """
    从 tfevents 文件中读取并打印指定 tag 的 tensor 数据。
    
    注意: 需要安装 tensorflow。`pip install tensorflow`
    """
    try:
        all_tensors = []
        # 使用 tf.data.TFRecordDataset 读取事件文件
        dataset = tf.data.TFRecordDataset(event_file_path)
        for record in dataset:
            event = tf.core.util.event_pb2.Event()
            event.ParseFromString(record.numpy())
            for value in event.summary.value:
                if value.tag == tensor_tag:
                    tensor_proto = value.tensor
                    # 从序列化的 tensor_content 中恢复 numpy 数组
                    fb = np.frombuffer(tensor_proto.tensor_content, dtype=np.float32)
                    all_tensors.append(fb)
        
        if not all_tensors:
            print(f"在文件 {event_file_path} 中未找到 tag='{tensor_tag}' 的数据。")
            return

        np.set_printoptions(threshold=np.inf)
        print(f"找到 {len(all_tensors)} 个 tag='{tensor_tag}' 的 Tensor。显示第一个:")
        print(all_tensors[0])

    except ImportError:
        print("此功能需要安装 TensorFlow。请运行 `pip install tensorflow`。")
    except Exception as e:
        print(f"读取文件时出错: {e}")


if __name__ == '__main__':
    # --- 演示 PyTorch 用法 ---
    pytorch_basic_usage()

    # --- 演示读取事件文件用法 ---
    # # 假设在 'runs/my_experiment/...' 目录下生成了事件文件
    # # 这里用一个假路径和tag作为示例
    # print("\n--- 演示读取事件文件 ---")
    # fake_event_file = "runs/my_experiment/20231107-123456/events.out.tfevents.xxxxx"
    # fake_tag = "some_tensor_tag"
    # # read_tensor_from_event_file(fake_event_file, fake_tag)