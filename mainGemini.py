import json
import os
import sys

# --- IDENTIFICAZIONE AUTOMATICA E SICURA DELLA RADICE ---
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
percorso_progetto = os.path.dirname(cartella_corrente)

if percorso_progetto not in sys.path:
    sys.path.insert(0, percorso_progetto)

os.environ["PYTHONPATH"] = percorso_progetto + os.pathsep + os.environ.get("PYTHONPATH", "")
# ---------------------------------------------------------------------

from analisi.chunker import dividi_in_proposizioni_con_db
from analisi.tokenizer import tokenizza_proposizione_lis
from analisi.strutturatore import applica_grammatica_lis


def esegui_pipeline_completa(frase_italiano, attore_scelto):
    print("--- FASE 1: INIZIO PIPELINE ---")
    print(f"Attore selezionato: '{attore_scelto}'\n")

    proposizioni = dividi_in_proposizioni_con_db(frase_italiano)
    playlist_finale_lis = []
    rilevata_interrogativa_globale = False

    print("\n--- FASE 2: ELABORAZIONE DELLE PROPOSIZIONI ---")
    for prop in proposizioni:
        token_estratti = tokenizza_proposizione_lis(prop, attore_scelto)
        token_riordinati = applica_grammatica_lis(token_estratti)

        for token in token_riordinati:
            if token.get("frase_interrogativa", False):
                rilevata_interrogativa_globale = True

            tipo_nodo = token.get("tipo", "STANDARD")
            parola_orig = token.get("parola_originale", token.get("parola", ""))
            lemma_lis = token.get("lemma_lis", token.get("lemma", ""))

            # DATTILOLOGIA
            if tipo_nodo == "DATTILOLOGIA" and "sequenza" in token:
                print(f"  [DATTILOLOGIA] Esplodo la parola '{parola_orig}' nelle sue lettere...")
                for lettera in token["sequenza"]:
                    percorso_lettera_video = f"vocabolario/{attore_scelto}/{lettera.lower()}.mp4"
                    nodo_lettera = {
                        "parola_originale": parola_orig,
                        "lemma_lis": f"LETTERA_{lettera.upper()}",
                        "tipo": "LETTERA_DATTILOLOGIA",
                        "percorso_video": percorso_lettera_video
                    }
                    playlist_finale_lis.append(nodo_lettera)
                continue

            # Gestione nodi Standard e Non Trovati
            percorso_vid = token.get("percorso_video", token.get("video", "Non disponibile"))
            if percorso_vid == "Non disponibile" or tipo_nodo == "NON_TROVATO":
                percorso_vid = f"vocabolario/{attore_scelto}/parola-non-trovata.mp4"

            dati_nodo = {
                "parola_originale": parola_orig,
                "lemma_lis": lemma_lis,
                "tipo": tipo_nodo,
                "percorso_video": percorso_vid
            }
            playlist_finale_lis.append(dati_nodo)

    # --- FASE 4: STRUTTURAZIONE OUTPUT DIZIONARIO ---
    output_strutturato = {
        "testo_lavagna": frase_italiano,
        "attore": attore_scelto,
        "tipo_frase": "INTERROGATIVA" if rilevata_interrogativa_globale else "AFFERMATIVA",
        "playlist_lis": playlist_finale_lis
    }

    # Salva comunque una copia locale per i test da terminale senza bloccare il Cloud
    try:
        nome_file_json = "output_traduzione_lis.json"
        with open(nome_file_json, "w", encoding="utf-8") as f:
            json.dump(output_strutturato, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"  [AVVISO DIZIONARIO] Scrittura file locale saltata (ambiente Cloud): {e}")

    print("\n--- FASE 5: ESPORTAZIONE COMPLETATA ---")

    # FONDAMENTALE PER IL SERVER: Restituisce l'oggetto pronto per la memoria
    return output_strutturato


# --- ESECUZIONE TEST ---
if __name__ == "__main__":
    frase_test = "Marco non mangiava la mia mela"
    attore = "attore1"
    risultato = esegui_pipeline_completa(frase_test, attore)
    print(json.dumps(risultato, indent=2, ensure_ascii=False))