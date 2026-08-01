
def remove_non_chinese_english(text):
  return re.sub(r'[^\w\u4e00-\u9fff]', '', text)


left, seg, right = str.rpartition(".")