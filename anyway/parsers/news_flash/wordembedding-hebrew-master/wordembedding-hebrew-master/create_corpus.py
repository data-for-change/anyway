# Download wiki corpus from https://dumps.wikimedia.org/hewiki/latest/
from gensim.corpora import WikiCorpus

inp = "hewiki-latest-pages-articles.xml.bz2"
outp = "wiki.he.text"
i = 0

print("Starting to create wiki corpus")
output = open(outp, 'w')
space = " "
wiki = WikiCorpus(inp, lemmatize=False, dictionary={})
for text in wiki.get_texts():
    article = space.join([t.decode("utf-8") for t in text])

    output.write("{}\n".format(article.encode("utf-8")))
    i += 1
    if (i % 1000 == 0):
        print("Saved " + str(i) + " articles")

output.close()
print("Finished - Saved " + str(i) + " articles")

