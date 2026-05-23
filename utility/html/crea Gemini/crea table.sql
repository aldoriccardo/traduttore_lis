
-- 1. Tabella dei SEGNI LIS (Contenitore dei file video e dati LIS puri)

DROP TABLE IF EXISTS `segni_lis`;
CREATE TABLE IF NOT EXISTS `segni_lis` (
  `id_segno` int(11) NOT NULL AUTO_INCREMENT,
  `nome_segno` varchar(255) NOT NULL,    -- Nome logico (es. 'MANGIARE')
  `file_video` varchar(255) NOT NULL,    -- Solo il nome del file (es. 'mangiare.mp4')
  `aggiunte` varchar(255) DEFAULT NULL,   -- Marcatori grammaticali (es. 'fatto', 'domani')
  `descrizione` text DEFAULT NULL,
  PRIMARY KEY (`id_segno`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- 2. Tabella dei LEMMI ITALIANI (Mappatura della lingua italiana verso la LIS)

DROP TABLE IF EXISTS `lemmi_it`;
CREATE TABLE IF NOT EXISTS `lemmi_it` (
  `id_lemma` int(11) NOT NULL AUTO_INCREMENT,
  `vocabolo` varchar(255) NOT NULL, -- La parola italiana (es. "mangiato", "case")
  `tipo` enum('sostantivo','verbo','aggettivo','preposizione','lettera','avverbio','pronome') DEFAULT 'sostantivo',
  `genere` enum('M','F','N') DEFAULT NULL,
  `numero` enum('S','P') DEFAULT 'S',
  `tempo_verbo` varchar(100) DEFAULT NULL,
  `id_segno` int(11) NOT NULL, -- FK verso segni_lis
  PRIMARY KEY (`id_lemma`),
  KEY `idx_vocabolo` (`vocabolo`),
  CONSTRAINT `fk_segno` FOREIGN KEY (`id_segno`) REFERENCES `segni_lis` (`id_segno`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Tabella DISAMBIGUAZIONE (Logica di contesto)

DROP TABLE IF EXISTS `disambiguazione`;
CREATE TABLE IF NOT EXISTS `disambiguazione` (
  `id_disamb` int(11) NOT NULL AUTO_INCREMENT,
  `parola_ambigua` varchar(255) NOT NULL,
  `parola_chiave_contesto` varchar(255) NOT NULL, -- Parola che deve apparire vicina
  `id_segno_corretto` int(11) NOT NULL, -- Il segno da usare in questo contesto
  PRIMARY KEY (`id_disamb`),
  KEY `idx_ambigua` (`parola_ambigua`),
  CONSTRAINT `fk_segno_disamb` FOREIGN KEY (`id_segno_corretto`) REFERENCES `segni_lis` (`id_segno`)