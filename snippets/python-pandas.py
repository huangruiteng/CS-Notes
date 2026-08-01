### Pandas简介

https://pandas.pydata.org/pandas-docs/stable/index.html

Pandas是一个提供高效数据结构和数据分析工具的Python库。它主要基于两个数据结构：Series 和 DataFrame，分别用于处理一维和二维数据。Pandas在数据清洗、预处理、分析和可视化方面广泛应用。其主要功能包括：

- DataFrame：类似于Excel表格的数据结构，支持列名、行索引和丰富的数据操作功能。
- Series：一维标签化数组，类似于Python的列表或字典。
- 数据操作：包括数据选择、过滤、分组、合并、连接、聚合、缺失值处理等。
- 文件处理：支持读取和写入CSV、Excel、SQL、JSON等多种格式的数据文件。

import pandas as pd
flags_df = pd.read_csv('national_flags.csv')  
print(flags_df)
flags_df.to_csv('output.csv')


series = pd.Series([1, 2, 3, 4])
print(series)

data = {'Name': ['Alice', 'Bob', 'Charlie'], 'Age': [24, 27, 22]}
df = pd.DataFrame(data)
print(df)


`crosstab` 统计分组频率

`drop`

`get_dummies` convert categorical variables to sets of indicator

# 过滤

df = pd.DataFrame({'Age': [24, 27, 22], 'Name': ['Alice', 'Bob', 'Charlie']})
filtered_df = df[df['Age'] > 24]
print(filtered_df)

# 缺失值处理

df = pd.DataFrame({'Age': [24, None, 22], 'Name': ['Alice', 'Bob', 'Charlie']})
df.fillna(25, inplace=True)
print(df)

### example

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

data = {'Year': [2015, 2016, 2017, 2018, 2019],
        'Sales': [150, 250, 550, 800, 1350],
        'Profit': [30, 45, 50, 60, 430]}

df = pd.DataFrame(data)

# 绘制第一条折线（销售额）
plt.plot(df['Year'], df['Sales'], marker='o', label='Sales')

# 绘制第二条折线（利润）
plt.plot(df['Year'], df['Profit'], marker='x', label='Profit')

plt.title('Sales Over Years')
plt.xlabel('Year')
plt.ylabel('Sales')
plt.show()