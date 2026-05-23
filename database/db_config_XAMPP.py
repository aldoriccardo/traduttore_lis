import mysql.connector
from mysql.connector import Error

def get_connection():
    """Configurazione centralizzata per il database XAMPP."""
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="dizionario_lis_gemini",
            port=3306,
            # Assicura che la connessione usi l'encoding corretto per i caratteri LIS
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Errore durante la connessione a MariaDB/MySQL: {e}")
        return None

