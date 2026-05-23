from scripts.config import NLP


class NLPEngine:

    def __init__(self):
        self.nlp = NLP

    def analizza_frase(self, frase: str):

        doc = self.nlp(frase)

        tokens = []
        verbi = []

        for token in doc:

            token_info = {
                "testo": token.text,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "tag": token.tag_,
                "dep": token.dep_,
                "head": token.head.text,
                "morph": token.morph.to_dict()
            }

            tokens.append(token_info)

            if token.pos_ in ["VERB", "AUX"]:

                verbo = {
                    "testo": token.text,
                    "lemma": token.lemma_,
                    "dep": token.dep_,
                    "head": token.head.text,
                    "morph": token.morph.to_dict()
                }

                verbi.append(verbo)

        return {
            "frase": frase,
            "tokens": tokens,
            "verbi": verbi
        }
