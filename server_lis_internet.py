import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

# Allineamento dei percorsi
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
percorso_progetto = os.path.dirname(cartella_corrente)
if percorso_progetto not in sys.path:
    sys.path.insert(0, percorso_progetto)

from mainGemini import esegui_pipeline_completa

app = Flask(__name__)
# Abilita il CORS per qualsiasi origine (Aruba inclusa)
CORS(app)


@app.route('/traduci', methods=['POST'])
def traduci_frase():
    try:
        dati_ricevuti = request.get_json()
        if not dati_ricevuti:
            return jsonify({"status": "errore", "messaggio": "Dati JSON mancanti"}), 400

        frase_italiano = dati_ricevuti.get('frase', '')
        attore_scelto = dati_ricevuti.get('attore', 'Angela') # Default sicuro

        print(f"\n[SERVER] Ricevuta frase da tradurre: '{frase_italiano}' per {attore_scelto}")

        # Otteniamo il dizionario dei dati DIRETTAMENTE in memoria, senza toccare il disco!
        output_strutturato = esegui_pipeline_completa(frase_italiano, attore_scelto)

        # Rispondiamo ad Aruba usando il jsonify nativo di Flask (che imposta automaticamente i corretti header)
        return jsonify(output_strutturato), 200

    except Exception as e:
        print(f"[ERRORE SERVER] {e}")
        return jsonify({"status": "errore", "messaggio": str(e)}), 500


if __name__ == '__main__':
    print("=== SERVER TRADUTTORE LIS CLOUD ATTIVO ===")
    porta = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=porta, debug=False)