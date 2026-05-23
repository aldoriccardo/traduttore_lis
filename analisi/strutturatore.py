def riordina_proposizione_lis(lista_token):
    """
    Prende in input la lista dei token generata dal tokenizer,
    applica le inversioni sintattiche (genitivo, possessivi) e riordina secondo la macro-struttura LIS:
    TEMPO -> SOGGETTO/OGGETTO -> VERBO -> NEGAZIONE -> INTERROGATIVO.
    """
    # --- FASE 0: INVERSIONE DEI PRONOMI POSSESSIVI (es. "mia casa" -> "casa mia") ---
    lista_lavorazione = list(lista_token)
    i = 0
    while i < len(lista_lavorazione) - 1:
        t_corrente = lista_lavorazione[i]
        t_successivo = lista_lavorazione[i + 1]

        is_possessivo = "Poss=Yes" in t_corrente.get('morph', '') or t_corrente.get('lemma_lis', '').lower() in ["mio",
                                                                                                                 "tuo",
                                                                                                                 "suo",
                                                                                                                 "nostro",
                                                                                                                 "vostro",
                                                                                                                 "loro",
                                                                                                                 "mia",
                                                                                                                 "tua",
                                                                                                                 "sua"]
        is_sostantivo = t_successivo.get('pos_spacy', '') == "NOUN"

        if is_possessivo and is_sostantivo:
            print(
                f"  [GRAMMATICA LIS] Rilevato possessivo precedente. Inverto: '{t_successivo['parola_originale']}' precede '{t_corrente['parola_originale']}'")
            lista_lavorazione[i], lista_lavorazione[i + 1] = lista_lavorazione[i + 1], lista_lavorazione[i]
            i += 2
            continue
        i += 1

    elementi_tempo = []
    elementi_centrali = []
    elementi_verbo = []
    elementi_negazione = []
    elementi_interrogativi = []

    # Lista ampliata di parole chiave interrogative
    lemmi_interrogativi = ["chi", "cosa", "che", "dove", "quando", "perché", "quanto", "quale"]

    # --- REGOLE DI TEMPO LIS ---
    # Dizionario esteso di lemmi temporali espliciti in italiano
    lemmi_tempo_espliciti = [
        "oggi", "ieri", "domani", "poi", "quando", "prima", "dopo", "futuro",
        "passato", "adesso", "ora", "stasera", "mattina", "pomeriggio", "notte",
        "anno", "mese", "settimana", "scorso", "prossimo", "allora", "già"
    ]

    # Flag per capire se l'italiano ha già espresso il tempo con un avverbio (es: "Ieri ho mangiato")
    ha_marcatore_tempo_esplicito = False

    # Primo passaggio rapido: verifichiamo se c'è già una parola temporale esplicita nella frase
    for token in lista_lavorazione:
        if token.get('lemma_lis', '').lower().strip() in lemmi_tempo_espliciti:
            ha_marcatore_tempo_esplicito = True
            break

    # --- FASE 1: APPLICAZIONE REGOLE SINTATTICHE INTERNE (Genitivo Sassone LIS) ---
    i = 0
    while i < len(lista_lavorazione):
        token_corrente = lista_lavorazione[i]
        dep = token_corrente.get('dep_spacy', '')
        pos = token_corrente.get('pos_spacy', '')
        morph = token_corrente.get('morph', '')

        parola_or = token_corrente.get('parola_originale', '').lower().strip()
        lemma_lis = token_corrente.get('lemma_lis', '').lower().strip()

        # Rilevamento del complemento di specificazione (nmod)
        if dep == 'nmod' and i > 0:
            testa_precedente = elementi_centrali.pop() if elementi_centrali else None
            if testa_precedente:
                print(
                    f"  [GRAMMATICA LIS] Rilevato nmod. Inverto l'ordine: '{token_corrente['parola_originale']}' precede '{testa_precedente['parola_originale']}'")
                elementi_centrali.append(token_corrente)
                elementi_centrali.append(testa_precedente)
                i += 1
                continue

        # --- FASE 2: SMISTAMENTO NEI MACRO-BLOCCHI LIS ---

        # 1. PRIORITÀ ASSOLUTA: Identificazione degli Interrogativi
        if parola_or in lemmi_interrogativi or lemma_lis in lemmi_interrogativi or dep in ["pronint", "advint"]:
            print(
                f"  [GRAMMATICA LIS] Rilevato interrogativo '{token_corrente['parola_originale']}'. Spostato in fondo alla frase.")
            elementi_interrogativi.append(token_corrente)

        # 2. Identificazione della Negazione
        elif lemma_lis == "non" or parola_or == "non" or "Neg" in morph:
            print(
                f"  [GRAMMATICA LIS] Rilevata negazione '{token_corrente['parola_originale']}'. Spostata dopo il verbo.")
            elementi_negazione.append(token_corrente)

        # 3. Identificazione del Tempo (Avverbi temporali espliciti)
        elif lemma_lis in lemmi_tempo_espliciti or parola_or in lemmi_tempo_espliciti:
            print(f"  [GRAMMATICA LIS] Rilevato indicatore di tempo esplicito: '{token_corrente['parola_originale']}'")
            elementi_tempo.append(token_corrente)

        # 4. Identificazione dei Verbi (e analisi morfologica del tempo se manca l'avverbio)
        elif pos in ["VERB", "AUX"]:
            elementi_verbo.append(token_corrente)

            # Se l'italiano NON ha un avverbio di tempo (es: "Mangerò una mela"),
            # leggiamo il tempo del verbo dal morph di SpaCy per generare il marcatore LIS artificiale.
            if not ha_marcatore_tempo_esplicito:
                # Caso FUTURO (Tense=Fut)
                if "Tense=Fut" in morph:
                    marcatore_futuro = {
                        'parola_originale': 'FUTURO', 'lemma_lis': 'FUTURO',
                        'pos_spacy': 'ADV', 'dep_spacy': 'advmod', 'morph': ''
                    }
                    if marcatore_futuro not in elementi_tempo:
                        print("  [GRAMMATICA LIS] Verbo al Futuro senza avverbio. Genero marcatore 'FUTURO' in testa.")
                        elementi_tempo.append(marcatore_futuro)
                        ha_marcatore_tempo_esplicito = True  # Evita di duplicarlo se ci sono ausiliari

                # Caso PASSATO (Imperfetto, Passato Prossimo, Passato Remoto -> Tense=Imp o Tense=Past)
                elif "Tense=Past" in morph or "Tense=Imp" in morph:
                    marcatore_passato = {
                        'parola_originale': 'PRIMA', 'lemma_lis': 'PRIMA',
                        'pos_spacy': 'ADV', 'dep_spacy': 'advmod', 'morph': ''
                    }
                    if marcatore_passato not in elementi_tempo:
                        print(
                            "  [GRAMMATICA LIS] Verbo al Passato (Imperfetto/Passato Prossimo) senza avverbio. Genero marcatore 'PRIMA' in testa.")
                        elementi_tempo.append(marcatore_passato)
                        ha_marcatore_tempo_esplicito = True

        # 5. Tutto il resto (Soggetti, Oggetti, Aggettivi, ecc.) nel mezzo
        else:
            elementi_centrali.append(token_corrente)

        i += 1

    # Componiamo la sequenza geometrica LIS perfetta
    sequenza_riordinata = (
            elementi_tempo +
            elementi_centrali +
            elementi_verbo +
            elementi_negazione +
            elementi_interrogativi
    )
    return sequenza_riordinata


def applica_grammatica_lis(lista_token):
    """
    Funzione interfaccia chiamata dal mainGemini.py.
    """
    return riordina_proposizione_lis(lista_token)