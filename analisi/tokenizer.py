import os
import sys
import spacy
import psycopg2  # Assicurati che sia importato psycopg2
from psycopg2.extras import RealDictCursor  # FONDAMENTALE PER LEGGERE I DIZIONARI DA POSTGRES

# Paracadute per i percorsi: dice a Python di guardare nella cartella superiore se non trova 'database'
radice_progetto = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if radice_progetto not in sys.path:
    sys.path.insert(0, radice_progetto)

# --- IMPORT CONFIGURAZIONE DATABASE CHIAMANDO IL FILE CORRETTO ---
from database.db_config import get_connection

# Carica il modello spaCy (Large o Fallback su Small)
try:
    nlp = spacy.load("it_core_news_lg")
except OSError:
    nlp = spacy.load("it_core_news_sm")


def cerca_parola_nel_db(vocabolo, tipo_atteso=None):
    """Cerca il vocabolo nel DB filtrando per tipo e recupera il file video da segni_lis."""
    conn = get_connection()
    if not conn:
        return None

    # MODIFICA CLOUD: Usiamo RealDictCursor specifico per PostgreSQL
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    parola_pulita = vocabolo.lower().strip()

    # Nuova query con la JOIN relazionale creata su Render
    if tipo_atteso:
        tipo_pulito = tipo_atteso.lower().strip()
        query = """
            SELECT l.id_lemma, l.vocabolo, l.tipo, l.id_segno, s.file_video 
            FROM lemmi_it l
            LEFT JOIN segni_lis s ON l.id_segno = s.id_segno
            WHERE LOWER(TRIM(l.vocabolo)) = %s 
              AND LOWER(TRIM(l.tipo)) LIKE %s 
            ORDER BY s.file_video DESC LIMIT 1
        """
        cursor.execute(query, (parola_pulita, f"%{tipo_pulito}%"))
    else:
        query = """
            SELECT l.id_lemma, l.vocabolo, l.tipo, l.id_segno, s.file_video 
            FROM lemmi_it l
            LEFT JOIN segni_lis s ON l.id_segno = s.id_segno
            WHERE LOWER(TRIM(l.vocabolo)) = %s 
            ORDER BY s.file_video DESC LIMIT 1
        """
        cursor.execute(query, (parola_pulita,))

    risultato = cursor.fetchone()

    # Debug specifico per tracciare il numero sei durante la query
    if parola_pulita == "sei":
        print(f"  [DEBUG QUERY SEI] tipo_atteso cercato: '{tipo_atteso}' -> Risultato DB: {risultato}")

    # Fallback automatico per la gestione elementare dei plurali (es. rose -> rosa)
    if not risultato:
        parola_singolo = None
        if parola_pulita.endswith('e') and len(parola_pulita) > 3:
            parola_singolo = parola_pulita[:-1] + 'a'
        elif parola_pulita.endswith('i') and len(parola_pulita) > 3:
            parola_singolo = parola_pulita[:-1] + 'o'

        if parola_singolo:
            if tipo_atteso:
                tipo_pulito = tipo_atteso.lower().strip()
                cursor.execute(query, (parola_singolo, f"%{tipo_pulito}%"))
            else:
                cursor.execute(query, (parola_singolo,))
            risultato = cursor.fetchone()

    cursor.close()
    conn.close()
    return risultato


def segnala_lacuna_db(parola, lemma, tipo, contesto):
    """Registra automaticamente nel DB una parola non trovata per futura correzione manuale."""
    try:
        conn = get_connection()
        if not conn:
            return
        cursor = conn.cursor()
        query = """
            INSERT INTO segnalazioni_morfologiche (parola_originale, lemma_spacy, tipo_spacy, frase_contesto)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (parola, lemma, tipo, contesto))
        conn.commit()
        cursor.close()
        conn.close()
        print(f"  [ALERT DB] Registrata segnalazione per '{parola}' ({tipo}) nella tabella segnalazioni_morfologiche.")
    except Exception as e:
        print(f"  [ERRORE SEGNALAZIONE] Impossibile scrivere nel DB delle lacune: {e}")


def tokenizza_proposizione_lis(proposizione_testo, attore_scelto):
    """Analizza la frase con spaCy, mappa i tipi morfologici e interroga il DB per costruire la playlist LIS."""
    doc = nlp(proposizione_testo)
    sequenza_segni = []
    attore = attore_scelto
    marca_interrogativa = False

    # --- PRIMA PASSATA VELOCE: RILEVAMENTO PUNTO INTERROGATIVO ---
    for token in doc:
        if token.text == "?":
            print(f"  [GRAMMATICA LIS] Rilevato punto interrogativo. La frase verrà marcata come INTERROGATIVA.")
            marca_interrogativa = True
            break

    # --- SECONDA PASSATA: TOKENIZZAZIONE E COSTRUZIONE PLAYLIST ---
    for token in doc:
        parola = token.text
        lemma = token.lemma_
        pos = token.pos_

        t_info = {
            "text": parola,
            "lemma": lemma,
            "pos": pos,
            "dep_": token.dep_,
            "morph": str(token.morph)
        }

        # Debug specifico per monitorare il comportamento della parola "sei"
        if parola.lower() == "sei":
            print(
                f"  [DEBUG TOKEN SEI] Parola: '{parola}', POS spaCy: '{pos}', tipo_db assegnato: 'numero' se NUM altrimenti 'verbo' se AUX/VERB")

        # --- 1. FILTRO ELEMENTI GRAMMATICALI DA SCARTARE ---
        # CONTROLLO SALVAVITA: Se è un possessivo (es. mia, tuo), NON dobbiamo scartarlo
        # anche se spaCy lo confonde con un determinante (DET)!
        is_possessivo_salva = "Poss=Yes" in str(token.morph) or lemma.lower() in ["mio", "tuo", "suo", "nostro",
                                                                                  "vostro", "loro", "mia", "tua",
                                                                                  "sua"]

        if pos in ["PUNCT", "DET", "CCONJ", "SCONJ", "ADP"]:
            if is_possessivo_salva:
                # Forza il POS a PRON così lo strutturatore sa cosa fare
                pos = "PRON"
                t_info["pos"] = "PRON"
            else:
                print(f"  X Scartato elemento grammaticale: '{parola}' ({pos})")
                continue

        # --- 2. TRADUZIONE TIPI DI SPACY PER IL DATABASE ---
        tipo_db = None
        if pos in ["VERB", "AUX"]:
            tipo_db = "verbo"
        elif pos == "NOUN":
            tipo_db = "sostantivo"
        elif pos == "ADJ":
            tipo_db = "aggettivo"
        elif pos == "NUM":
            tipo_db = "numero"

        # --- GESTIONE NOMI PROPRI (DATTILOLOGIA AUTOMATICA INTELLIGENTE) ---
        if pos == "PROPN":
            # CONTROLLO SALVAVITA: Prima di fare lo spelling, verifichiamo se la parola esiste nel DB
            # (evita che parole maiuscole a inizio frase tipo 'Buongiorno' o 'Domani' facciano la dattilologia)
            segno_db_test = cerca_parola_nel_db(lemma)
            if not segno_db_test:
                segno_db_test = cerca_parola_nel_db(parola)

            if segno_db_test:
                # La parola esiste nel DB! Allora NON è un vero nome proprio di persona.
                # Lo declassiamo a sostantivo così verrà gestito normalmente sotto dalla ricerca standard
                pos = "NOUN"
                tipo_db = "sostantivo"
            else:
                # La parola NON esiste nel DB (è un vero nome proprio come Marco, Silvio, ecc.) -> Dattilologia
                sequenza_lettere = [lettera.lower() for lettera in parola if lettera.isalpha()]
                print(f"  [DATTILOLOGIA] Attivato spelling automatico per il nome proprio: '{parola}' -> {sequenza_lettere}")

                nodo_dattilo = {
                    "parola_originale": parola,
                    "lemma_lis": parola.upper(),
                    "tipo": "DATTILOLOGIA",
                    "percorso_video": "dattilologia/",
                    "sequenza": sequenza_lettere,
                    "pos_spacy": pos,
                    "dep_spacy": t_info["dep_"]
                }
                if marca_interrogativa:
                    nodo_dattilo["frase_interrogativa"] = True

                sequenza_segni.append(nodo_dattilo)
                continue  # Passa subito alla parola successiva

        # --- 3. GESTIONE PRONOMI ---
        if pos == "PRON":
            tipo_nodo = "PRONOME"

        # --- 4. GESTIONE PAROLE NORMALI (E CERCATE NEL DB) ---
        # Primo tentativo: cerca usando il lemma estratto da spaCy e il tipo morfologico
        segno_db = cerca_parola_nel_db(lemma, tipo_db)

        # Secondo tentativo: se il lemma fallisce, prova con la parola testuale
        if not segno_db and parola.lower() != lemma.lower():
            segno_db = cerca_parola_nel_db(parola, tipo_db)

        # Terzo tentativo (disperato): cerca la parola a tutto campo senza filtri sul tipo
        if not segno_db:
            segno_db = cerca_parola_nel_db(parola)

        # --- 5. COSTRUZIONE DEI NODI DELLA PLAYLIST ---
        if segno_db:
            vocabolo_db = segno_db['vocabolo']
            video_reale = segno_db.get('file_video')

            # Gestione del nome del file video
            if video_reale and str(video_reale).strip() != "" and str(video_reale).strip() != "None":
                video_finale = video_reale
            else:
                video_finale = f"{vocabolo_db}.mp4"

            nodo_standard = {
                "parola_originale": parola,
                "lemma_lis": vocabolo_db,
                "tipo": "STANDARD",
                "percorso_video": f"vocabolario/{attore}/{video_finale}",
                "pos_spacy": pos,
                "dep_spacy": t_info["dep_"],
                "morph": t_info["morph"]
            }
            if marca_interrogativa:
                nodo_standard["frase_interrogativa"] = True

            sequenza_segni.append(nodo_standard)
        else:
            # SE LA PAROLA FALLISCE TUTTI I TENTATIVI DI RICERCA:
            tipo_nodo = "PRONOME" if pos == "PRON" else "NON_TROVATO"

            # AUTOMATISMO RADAR: Se è un vero NON_TROVATO, lo scrive nel database delle segnalazioni
            if tipo_nodo == "NON_TROVATO":
                segnala_lacuna_db(parola, lemma, tipo_db if tipo_db else pos, proposizione_testo)

            # Aggiunge comunque l'elemento alla playlist marcandolo come "Non disponibile"
            nodo_fallito = {
                "parola_originale": parola,
                "lemma_lis": "Sconosciuto",
                "tipo": tipo_nodo,
                "percorso_video": "Non disponibile",
                "pos_spacy": pos,
                "dep_spacy": t_info["dep_"],
                "morph": t_info["morph"]
            }
            if marca_interrogativa:
                nodo_fallito["frase_interrogativa"] = True

            sequenza_segni.append(nodo_fallito)

    return sequenza_segni