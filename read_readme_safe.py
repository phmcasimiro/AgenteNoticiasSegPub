import codecs
try:
    with codecs.open('README.md', 'r', 'utf-16') as f:
        print(f.read())
except:
    with open('README.md', 'r', encoding='utf-8') as f:
        print(f.read())
