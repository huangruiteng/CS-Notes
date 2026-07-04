import tensorflow as tf
reader = tf.train.load_checkpoint(".")
shape_from_key = reader.get_variable_to_shape_map()
sorted(shape_from_key.keys())
reader.get_tensor("deep_part/dense_0/kernel")