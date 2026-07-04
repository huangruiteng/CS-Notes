import re
import tensorflow as tf
from tensorflow.core.protobuf import saved_model_pb2
from tensorflow.python.util import compat
import argparse
from collections import defaultdict

def process_file(file_name):
    try:
        with tf.io.gfile.GFile(file_name, 'rb') as f:
            sm = saved_model_pb2.SavedModel()
            sm.ParseFromString(compat.as_bytes(f.read()))
            ops = [
                node.op
                for node in sm.meta_graphs[0].graph_def.node
                if node.op.startswith('ShardingSparseFids')
            ]
            assert len(ops) <= 1, f"len > 1, ops: {ops}"
            result = '-1'
            if len(ops) == 0:
                return result
            match = re.search(r'\d+', ops[0])
            if match:
                result = match.group()
            else:
                result = '1'
            return result
    except tf.errors.NotFoundError as e:
        return '-2'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--file', type=str, default='', help='file name')
    parser.add_argument('--file_list', type=str, default='', help='file name')
    args = parser.parse_args()
    counts = defaultdict(int)
    old_version_models = []
    read_error_models = []
    if args.file:
        print(process_file(args.file))
    if args.file_list:
        with tf.io.gfile.GFile(args.file_list, 'r') as file:
            for line in file:
                file_name = line.strip()
                result = process_file(file_name)
                counts[result] += 1
                if result not in {'-1', '5'}:
                    old_version_models.append((result, file_name))
                    print(f"counts: {counts}")
                    print(f"old_version_models: {old_version_models}")

        print(f"counts: {counts}")
        print(f"old_version_models: {old_version_models}")


main()