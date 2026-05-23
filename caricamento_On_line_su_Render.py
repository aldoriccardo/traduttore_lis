# pip install psycopg2-binary

import re
import psycopg2

# Dati di connessione al database PostgreSQL su Render (External URL params)
DB_HOST = "dpg-d861fh99rddc73etmev0-a.oregon-postgres.render.com"
DB_NAME = "dizionario_lis_gemini"
DB_USER = "dizionario_lis_gemini_user"
DB_PASS = "IJ5dnQEkmyQlse2hZDkfh1MgowAjlxDp"
DB_PORT = "5432"

SQL_FILE_PATH = "my_dizionario.sql"


def main():
    print("Connessione al database di Render in corso...")
    try:
        conn = psycopg2.connect(
            host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=DB_PORT
        )
        cursor = conn.cursor()
        print("Connessione stabilita con successo!")
    except Exception as e:
        print(f"Errore di connessione al database: {e}")
        return

    print(f"Lettura del file {SQL_FILE_PATH}...")
    with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex per estrarre le tuple dei dati dal dump phpMyAdmin
    pattern = re.compile(
        r"\('([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)"
    )
    rows = pattern.findall(content)
    total_rows = len(rows)
    print(f"Trovate {total_rows} righe da elaborare nel file SQL.")

    print("Inizio migrazione dei dati (separazione in segni_lis e lemmi_it)...")

    # Dizionario di supporto per evitare di duplicare i video in segni_lis
    # Chiave: file_video, Valore: id_segno inserito
    video_to_id = {}

    inseriti_segni = 0
    inseriti_lemmi = 0

    for idx, riga in enumerate(rows, 1):
        tipo = riga[0]
        tempo_verbo = riga[1]
        vocabolo = riga[3]
        file_video = riga[9]  # Corrisponde a vocabolo_lis_mp4
        aggiunte = riga[12]

        # Se il campo del file video è vuoto, saltiamo la riga per evitare dati corrotti
        if not file_video or file_video.strip() == "":
            continue

        file_video = file_video.strip()
        nome_segno_logico = file_video.replace(".mp4", "").upper()

        try:
            # 1. Se il video non è ancora stato inserito in segni_lis, lo inseriamo adesso
            if file_video not in video_to_id:
                cursor.execute(
                    """
                    INSERT INTO segni_lis (nome_segno, file_video, aggiunte)
                    VALUES (%s, %s, %s) RETURNING id_segno;
                    """,
                    (nome_segno_logico, file_video, aggiunte if aggiunte else None)
                )
                id_segno = cursor.fetchone()[0]
                video_to_id[file_video] = id_segno
                inseriti_segni += 1
            else:
                # Se esiste già, recuperiamo il suo ID salvato in memoria
                id_segno = video_to_id[file_video]

            # 2. Inseriamo la parola nella tabella lemmi_it associandola al id_segno corretto
            # Mappatura genere/numero base se presenti
            genere = riga[1] if riga[1] in ['M', 'F'] else None
            numero = riga[2] if riga[2] in ['S', 'P'] else 'S'

            cursor.execute(
                """
                INSERT INTO lemmi_it (vocabolo, tipo, genere, numero, tempo_verbo, id_segno)
                VALUES (%s, %s, %s, %s, %s, %s);
                """,
                (vocabolo.strip(), tipo.strip(), genere, numero, tempo_verbo.strip() if tempo_verbo else None, id_segno)
            )
            inseriti_lemmi += 1

            # Mostra il progresso ogni 500 righe
            if idx % 500 == 0 or idx == total_rows:
                print(f"Progresso: {idx}/{total_rows} righe elaborate...")
                conn.commit()  # Salviamo i dati parziali sul cloud

        except Exception as e:
            print(f"Errore alla riga {idx} ({vocabolo}): {e}")
            conn.rollback()
            continue

    # Commit finale per salvare tutto il lavoro rimasto
    conn.commit()
    cursor.close()
    conn.close()

    print("\n========================================================")
    print(" MIGRAZIONE COMPLETATA CON SUCCESSO IN CLOUD!")
    print(f" Video unici inseriti in 'segni_lis': {inseriti_segni}")
    print(f" Parole totali mappate in 'lemmi_it': {inseriti_lemmi}")
    print("========================================================")


if __name__ == "__main__":
    main()