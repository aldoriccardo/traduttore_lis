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

'''  

-----   Per db online  -------
import os
import psycopg2
from psycopg2 import Error

def get_connection():
    “””Configurazione centralizzata per il database PostgreSQL su Render.”””
    try:
        # Usiamo l’Internal Database URL fornito da Render
        connection = psycopg2.connect(
            host=”dpg-d861fh99rddc73etmev0-a”,
            database=”dizionario_lis_gemini”,
            user=”dizionario_lis_gemini_user”,
            password=”IJ5dnQEkmyQlse2hZDkfh1MgowAjlxDp”,
            port=”5432”
        )
        return connection
    except Error as e:
        print(f”Errore durante la connessione a PostgreSQL su Render: {e}”)
        return None

'''