import fasttext
import time

def train(inp = "wiki.he.text",out_model = "wiki.he.fasttext.model",
          alg = "cbow"):
    start = time.time()
    ft_model = fasttext.train_unsupervised(inp, alg)
    print(ft_model.words) # list of words in dictionary
    print(time.time()-start)
    ft_model.save_model(out_model)



def getModel(model = "wiki.he.fasttext.model.bin"):

    model = fasttext.load_model(model)

    return model
