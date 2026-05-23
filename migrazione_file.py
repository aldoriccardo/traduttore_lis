import re
import psycopg2

# Dati di connessione al database PostgreSQL su Render
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
    try:
        with open(SQL_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Errore: Il file '{SQL_FILE_PATH}' nao è stato trovato in questa cartella!")
        return

    # Regex per estrarre le tuple dei dati dal dump phpMyAdmin
    pattern = re.compile(
        r"\('([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)',\s*'([^']*)'\)"
    )
    rows = pattern.findall(content)
    total_rows = len(rows)
    print(f"Trovate {total_rows} righe da elaborare nel file SQL.")

    print("Inizio migrazione dei dati (separazione in segni_lis e lemmi_it)...")

    video_to_id = {}
    inseriti_segni = 0
    inseriti_lemmi = 0

    for idx, riga in enumerate(rows, 1):
        tipo = riga[0]
        tempo_verbo = riga[1]
        vocabolo = riga[3]
        file_video = riga[9]  # Corrisponde a vocabolo_lis_mp4
        aggiunte = riga[12]

        if not file_video or file_video.strip() == "":
            continue

        file_video = file_video.strip()
        nome_segno_logico = file_video.replace(".mp4", "").upper()

        try:
            # 1. Gestione tabella segni_lis
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
                id_segno = video_to_id[file_video]

            # 2. Gestione tabella lemmi_it
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

            # Salva i dati parziali sul cloud ogni 500 righe per sicurezza
            if idx % 500 == 0 or idx == total_rows:
                print(f"Progresso: {idx}/{total_rows} righe elaborate...")
                conn.commit()

        except Exception as e:
            print(f"Errore alla riga {idx} ({vocabolo}): {e}")
            conn.rollback()
            continue

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