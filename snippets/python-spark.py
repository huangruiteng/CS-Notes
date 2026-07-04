*** basic

from pyspark.sql import SparkSession

# 初始化 SparkSession
spark = SparkSession.builder \
    .appName("Read HDFS JSON") \
    .getOrCreate()

# 读取 HDFS 上的 JSON 文件
# 注意：这里的路径 'hdfs://tt/...' 必须是您的集群可以访问的有效路径
df = spark.read.json('hdfs://xxx.ztsd')

# 打印 Schema 和显示数据
df.printSchema()
df.show()

# 停止 SparkSession
spark.stop()


*** example

import sys
from pyspark.sql import SparkSession
from typing import List

def initialize_spark_session() -> SparkSession:
    """
    初始化并配置 SparkSession，使其能够处理特定的压缩文件（例如 .zstd）。
    """
    # 1. 指定自定义压缩格式所需的 JAR 包路径
    #    【请替换为您自己的 JAR 文件路径】
    custom_codec_jars = ",".join([
        "/path/to/your/custom-codec.jar",
        "/path/to/your/jni-library.jar"
    ])

    print("Initializing SparkSession...")
    spark = SparkSession.builder \
        .appName("Spark HDFS Snippet") \
        .config("spark.jars", custom_codec_jars) \
        .config("spark.sql.io.compression.codecs", "com.yourcompany.YourCustomCodec") \
        .config("spark.driver.memory", "4g") \
        .getOrCreate()
    print("SparkSession initialized successfully.")
    return spark

def list_hdfs_files(spark: SparkSession, base_path: str, limit: int = 5) -> List[str]:
    """
    使用 Spark 的 Hadoop FileSystem API 列出 HDFS 上的文件。
    """
    print(f"Listing files under: {base_path}")
    # 2. 获取底层的 Hadoop FileSystem 对象
    fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())
    
    # 构造一个能匹配所有子目录中文件的路径模式
    glob_path = spark._jvm.org.apache.hadoop.fs.Path(base_path, "*/*.zstd")
    
    file_statuses = fs.globStatus(glob_path)
    
    file_paths = [status.getPath().toString() for status in file_statuses]
    print(f"Found {len(file_paths)} files. Returning a limit of {limit}.")
    
    return file_paths[:limit]

def process_data_in_batches(spark: SparkSession, file_paths: List[str]):
    """
    读取文件并使用 toLocalIterator() 进行高效的流式处理。
    """
    if not file_paths:
        print("No files to process.")
        return

    print(f"\nReading {len(file_paths)} files into DataFrame...")
    df = spark.read.json(file_paths)
    print("DataFrame schema:")
    df.printSchema()

    # 3. 使用 toLocalIterator() 进行内存安全的迭代处理
    #    这是处理大规模数据的核心技巧，可有效防止 Driver 节点 OOM。
    print("\nProcessing data with toLocalIterator()...")
    # 假设我们只关心 'id' 和 'embedding' 字段
    iterator = df.select("id", "embedding").toLocalIterator()

    processed_count = 0
    for row in iterator:
        item_id = row.id
        embedding = row.embedding
        
        if processed_count < 3: # 只打印前3个作为示例
            print(f"  - Processed item ID: {item_id}, Embedding dim: {len(embedding) if embedding else 'N/A'}")
        
        processed_count += 1
    
    print(f"\nFinished processing a total of {processed_count} items.")


if __name__ == "__main__":
    # --- 使用示例 ---
    
    # 【请替换为您的 HDFS 路径】
    HDFS_BASE_PATH = 'hdfs://your-namenode/path/to/your/data'
    
    spark_session = None
    try:
        spark_session = initialize_spark_session()
        files_to_process = list_hdfs_files(spark_session, HDFS_BASE_PATH, limit=10)
        process_data_in_batches(spark_session, files_to_process)
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        
    finally:
        if spark_session:
            print("\nStopping SparkSession.")
            spark_session.stop()