response = requests.get(url).content
obj = json.loads(response.decode('utf-8'))