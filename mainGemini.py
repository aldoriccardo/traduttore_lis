import json
import os
import sys

# --- IDENTIFICAZIONE AUTOMATICA E SICURA DELLA RADICE ---
# Trova la cartella in cui risiede fisicamente questo file (G:\Python\NLP\gemini)
cartella_corrente = os.path.dirname(os.path.abspath(__file__))

# Sali di un livello per beccare la cartella madre del progetto (G:\Python\NLP)
percorso_progetto = os.path.dirname(cartella_corrente)

# Aggiungiamo questo percorso in cima a sys.path prima di caricare qualsiasi altra cosa
if percorso_progetto not in sys.path:
    sys.path.insert(0, percorso_progetto)

# Aggiorna anche la variabile d'ambiente per i sottomoduli
os.environ["PYTHONPATH"] = percorso_progetto + os.pathsep + os.environ.get("PYTHONPATH", "")
# ---------------------------------------------------------------------

# ORA GLI IMPORT CARICHERANNO AL 100% SU QUALSIASI TERMINALE O IDE
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

            # =========================================================================
            # DATTILOLOGIA NELLA STESSA CARTELLA DEI VOCABOLI
            # =========================================================================
            if tipo_nodo == "DATTILOLOGIA" and "sequenza" in token:
                print(f"  [DATTILOLOGIA] Esplodo la parola '{parola_orig}' nelle sue lettere...")

                for lettera in token["sequenza"]:
                    # Ora punta direttamente alla cartella dei vocaboli dell'attore, senza sottocartelle
                    percorso_lettera_video = f"vocabolario/{attore_scelto}/{lettera.lower()}.mp4"

                    nodo_lettera = {
                        "parola_originale": parola_orig,
                        "lemma_lis": f"LETTERA_{lettera.upper()}",  # <--- Corretto in Python .upper()
                        "tipo": "LETTERA_DATTILOLOGIA",
                        "percorso_video": percorso_lettera_video
                    }
                    playlist_finale_lis.append(nodo_lettera)

                continue  # Passa al token successivo

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

    # --- FASE 4: STRUTTURAZIONE OUTPUT JSON ---
    output_strutturato = {
        "testo_lavagna": frase_italiano,
        "attore": attore_scelto,
        "tipo_frase": "INTERROGATIVA" if rilevata_interrogativa_globale else "AFFERMATIVA",
        "playlist_lis": playlist_finale_lis
    }

    nome_file_json = "output_traduzione_lis.json"
    with open(nome_file_json, "w", encoding="utf-8") as f:
        json.dump(output_strutturato, f, indent=4, ensure_ascii=False)

    print("\n--- FASE 5: ESPORTAZIONE COMPLETATA ---")
    print(json.dumps(output_strutturato, indent=2, ensure_ascii=False))


# --- ESECUZIONE TEST ---
if __name__ == "__main__":
    # Cambia questa stringa inserendo o togliendo il punto interrogativo per testare lo switch facciale!
    frase_test = "Marco non mangiava la mia mela"
    attore = "attore1"

    esegui_pipeline_completa(frase_test, attore)