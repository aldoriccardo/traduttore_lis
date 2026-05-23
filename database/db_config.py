# -----   Per db online  -------
import psycopg2

def get_connection():
    """Stabilisce una connessione sicura con il PostgreSQL di Render."""
    try:
        conn = psycopg2.connect(
            host="dpg-d861fh99rddc73etmev0-a.oregon-postgres.render.com",
            database="dizionario_lis_gemini",
            user="dizionario_lis_gemini_user",
            password="IJ5dnQEkmyQlse2hZDkfh1MgowAjlxDp",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"  [ERRORE SUL SERVER RENDER] Impossibile connettersi al database Cloud: {e}")
        return None

