import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

# Allineamento dei percorsi (la solita protezione che abbiamo messo nel main)
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
percorso_progetto = os.path.dirname(cartella_corrente)
if percorso_progetto not in sys.path:
    sys.path.insert(0, percorso_progetto)

# Importiamo la tua pipeline che funziona già a meraviglia
from mainGemini import esegui_pipeline_completa

app = Flask(__name__)
# CORS permette alla pagina web su localhost (XAMPP) di parlare con Flask (Python) senza blocchi
CORS(app)


@app.route('/traduci', methods=['POST'])
def traduci_frase():
    try:
        # Recupera i dati inviati dalla pagina HTML
        dati_ricevuti = request.get_json()
        frase_italiano = dati_ricevuti.get('frase', '')
        attore_scelto = dati_ricevuti.get('attore', 'attore1')

        print(f"\n[SERVER] Ricevuta frase da tradurre: '{frase_italiano}' per {attore_scelto}")

        # Facciamo girare la tua pipeline NLP LIS!
        # Questa funzione genera già il file 'output_traduzione_lis.json' su disco
        esegui_pipeline_completa(frase_italiano, attore_scelto)

        # Rileggiamo il file JSON appena generato per spedirlo indietro alla pagina web
        nome_file_json = "output_traduzione_lis.json"
        with open(nome_file_json, "r", encoding="utf-8") as f:
            json_generato = f.read()

        # Rispondiamo al browser con il JSON LIS perfetto
        return json_generato, 200, {'Content-Type': 'application/json'}

    except Exception as e:
        print(f"[ERRORE SERVER] {e}")
        return jsonify({"status": "errore", "messaggio": str(e)}), 500


if __name__ == '__main__':
    print("=== SERVER TRADUTTORE LIS CLOUD ATTIVO ===")
    # Legge la porta assegnata dal Cloud (Render/Aruba), se non esiste usa la 5000 di backup
    porta = int(os.environ.get("PORT", 5000))
    # host='0.0.0.0' è fondamentale: dice a Flask di accettare connessioni da TUTTO internet
    app.run(host='0.0.0.0', port=porta, debug=False)