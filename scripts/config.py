import spacy

# Caricamento modello italiano
NLP = spacy.load("it_core_news_lg")

MODALI = {"dovere", "potere", "volere", "sapere", "solere"}
AUSILIARI = {"essere", "avere"}
