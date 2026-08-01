# csv.reader、csv.DictReader

vid_info_dict = {}
with open('vid_info.csv', 'r', encoding='utf-8') as vid_file:
  vid_reader = csv.reader(vid_file)
  next(vid_reader)  # 跳过标题行
  for row in vid_reader:
    code = row[0].split('_')[0]  # 提取 CODE
    url_code = row[3]
    vid_info_dict[code] = url_code

movies = []
with open('movie_v4.csv', 'r', encoding='utf-8') as movie_file:
  movie_reader = csv.DictReader(movie_file)
  for movie in movie_reader:
    code = movie['CODE']
    if code in vid_info_dict:
      movie['url'] = vid_info_dict[code]
    else:
      movie['url'] = None  # 如果未找到对应的 URL 代码，设置为 None
    movies.append(movie)