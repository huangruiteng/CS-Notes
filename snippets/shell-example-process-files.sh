#!/bin/bash

# 原始文件和新的文件列表
original_file="model_list"
unique_file="unique_list"
model_path_list="model_path_list"
rm $unique_file $model_path_list

# 用于记录已经出现过的 model_id
seen_model_ids=()

# 遍历原始文件的每一行
while IFS= read -r line; do
  model_id=$(echo "$line" | awk -F'/' '{print $(NF-4)}')
  
  # 检查 model_id 是否已经出现过
  if [[ ! "${seen_model_ids[@]}" =~ "${model_id}" ]]; then
    seen_model_ids+=("$model_id")
    echo "$line" >> "$new_file_list"
  fi
done < "$original_file"

echo "Total model_id count: ${#seen_model_ids[@]}"

while IFS= read -r line; do
  model_path=$(echo "$line" | awk -F'[ ]' '{print $(NF)}')
  echo "$model_path" >> "$model_path_list"
done < "$unique_file"