import exifread
t = exifread.process_file(open('img.jpg', 'rb'))
geo = {i:t[i] for i in t.keys() if i.startswith('GPS')}
for tag, value in geo.items():
    print(str(tag) + ":" + str(value))
