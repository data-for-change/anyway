Word Embedding - Hebrew
============================

#### The Code for https://www.oreilly.com/learning/capturing-semantic-meanings-using-deep-learning

##### Note: This code works for Hebrew, but it should work on any other language.

1. Download hebrew dataset from wikipedia
   - Go to: https://dumps.wikimedia.org/hewiki/latest/
   - Download `hewiki-latest-pages-articles.xml.bz2`
   
   In linux this can be easily done using: 
   
   wget https://dumps.wikimedia.org/hewiki/latest/hewiki-latest-pages-articles.xml.bz2

2. `pip install --upgrade gensim` (https://radimrehurek.com/gensim/install.html)
3. Run create_corpus.py: `python create_corpus.py`
    - It will create `wiki.he.text`
    
4. train the model: 
   from python prompt: 
   - import word2vec
   - word2vec.train()
   
5. explore model using jupyter notebook. You can use the supplied playingWithHebModel.ipynb example as
   a starting point.


####  Word2Vec
- Train (inp = "wiki.he.text", out_model = "wiki.he.word2vec.model")

####  FastText
`pip install fasttext`

- Train (inp = "wiki.he.text", out_model = "wiki.he.fasttext.model", alg = "skipgram")

#### Test

Testing specific Hebrew analogies like:

> פריז + גרמניה - צרפת = ברלין

> גבר + מלכה - מלך = אישה

