import spacy
import os
import sys

nlp = spacy.load("it_core_news_sm")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_config import get_connection

from psycopg2.extras import RealDictCursor  # FONDAMENTALE: aggiungi questo import in cima al file se manca


def is_verbo_nel_db(testo, lemma):
    """Verifica se una parola è registrata come verbo nel database Cloud di Render."""
    conn = get_connection()
    if not conn:
        return False

    # MODIFICA CLOUD: Usiamo RealDictCursor al posto di dictionary=True
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Nuova query ottimizzata per la tabella relazionale lemmi_it
    query = """
        SELECT id_lemma FROM lemmi_it 
        WHERE (LOWER(vocabolo) = %s OR LOWER(vocabolo) = %s) 
          AND LOWER(tipo) = 'verbo' 
        LIMIT 1
    """

    try:
        cursor.execute(query, (testo, lemma))
        risultato = cursor.fetchone()
        return risultato is not None
    except Exception as e:
        print(f"  [ERRORE CHUNKER] Errore di lettura: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def dividi_in_proposizioni_con_db(testo):
    doc = nlp(testo)
    verbi_effettivi = []

    # PASSO 1: Identifichiamo i veri nuclei verbali aiutandoci col DB
    for i, token in enumerate(doc):
        pos_token = token.pos_
        # Se spaCy dice che è NOUN ma il DB dice che è VERBO, lo correggiamo
        if pos_token == "NOUN" and is_verbo_nel_db(token.text.lower(), token.lemma_.lower()):
            pos_token = "VERB"

        if pos_token in ["VERB", "AUX"]:
            # Gestione Modali/Causativi (Unione)
            # Se è un modale/ausiliare legato a un infinito, non lo contiamo come nuovo inizio
            if token.dep_ in ["aux", "xcomp"] and i > 0 and doc[i - 1].pos_ in ["VERB", "AUX"]:
                continue
            verbi_effettivi.append(i)

    # PASSO 2: Creiamo le proposizioni basandoci sugli indici dei verbi trovati
    proposizioni = []
    inizio_chunk = 0

    # Se abbiamo trovato ad esempio 8 verbi, creeremo 8 tagli
    for idx in verbi_effettivi[1:]:  # Partiamo dal secondo verbo per trovare i punti di taglio
        # Cerchiamo un punto di rottura naturale (congiunzione o virgola) prima del verbo
        punto_taglio = idx
        for j in range(idx, inizio_chunk, -1):
            if doc[j - 1].text.lower() in ['che', 'perché', 'quando', 'e', 'per', 'di', 'cosa', ',']:
                punto_taglio = j - 1
                break

        segmento = doc[inizio_chunk: punto_taglio].text.strip(", ")
        if segmento:
            proposizioni.append(segmento)
        inizio_chunk = punto_taglio

    # Aggiungiamo l'ultima parte
    proposizioni.append(doc[inizio_chunk:].text.strip(", "))

    return proposizioni
