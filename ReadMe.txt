gemini/
   |
   main.py
   database/
       |-- db_config.py
   analisi/
       |-- chunker.py        <-- (Punto 3: Divide in proposizioni)
       |-- tokenizer.py      <-- (Punto 4: Converte in lemmi e interroga il DB)
       |-- strutturatore.py  <-- Organizza la proposizione con S-O-V