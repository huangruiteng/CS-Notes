import time

import tensorflow as tf
fast_dataset = tf.data.Dataset.range(10000)


def fast_benchmark(dataset, name, num_epochs=2):
    start_time = time.perf_counter()
    for _ in tf.data.Dataset.range(num_epochs):
        for _ in dataset:
            pass
    tf.print("Test", name, "Execution time(ms):", 1000 * (time.perf_counter() - start_time))


def increment(x):
    return x+1


def filter_fn(x):
  return tf.math.equal(tf.math.mod(x, 2), 1)


if __name__ == '__main__':
  fast_benchmark(
    fast_dataset
    .map(increment)
    .batch(256)
    ,
    "map+batch"
  )
  fast_benchmark(
    fast_dataset
    .batch(256)
    .map(increment)
    ,
    "batch+map"
  )
  fast_benchmark(
    fast_dataset
    .map(increment)
    .batch(256)
    .prefetch(tf.data.AUTOTUNE)
    ,
    "map+batch+prefetch"
  )
  fast_benchmark(
    fast_dataset
    .map(increment)
    .prefetch(tf.data.AUTOTUNE)
    .batch(256)
    ,
    "map+prefetch+batch"
  )
  fast_benchmark(
    fast_dataset
    .batch(256)
    .map(increment)
    .prefetch(tf.data.AUTOTUNE)
    ,
    "batch+map+prefetch"
  )
  fast_benchmark(
    fast_dataset
    .prefetch(tf.data.AUTOTUNE)
    .batch(256)
    .map(increment)
    ,
    "prefetch+batch+map"
  )
  fast_benchmark(
    fast_dataset
    .batch(256)
    .prefetch(tf.data.AUTOTUNE)
    .map(increment)
    ,
    "batch+prefetch+map"
  )
  fast_benchmark(
    fast_dataset
    .filter(filter_fn)
    .batch(256)
    ,
    "filter+batch"
  )
  fast_benchmark(
    fast_dataset
    .batch(256)
    .filter(filter_fn)
    ,
    "batch+filter"
  )
