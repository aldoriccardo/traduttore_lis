-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Creato il: Mag 15, 2026 alle 11:51
-- Versione del server: 10.4.32-MariaDB
-- Versione PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `dizionario_lis_gemini`
--

-- --------------------------------------------------------

--
-- Struttura della tabella `disambiguazione`
--

CREATE TABLE `disambiguazione` (
  `id_disamb` int(11) NOT NULL,
  `parola_ambigua` varchar(255) NOT NULL,
  `parola_chiave_contesto` varchar(255) NOT NULL,
  `id_segno_corretto` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Indici per le tabelle scaricate
--

--
-- Indici per le tabelle `disambiguazione`
--
ALTER TABLE `disambiguazione`
  ADD PRIMARY KEY (`id_disamb`),
  ADD KEY `idx_ambigua` (`parola_ambigua`),
  ADD KEY `fk_segno_disamb` (`id_segno_corretto`);

--
-- AUTO_INCREMENT per le tabelle scaricate
--

--
-- AUTO_INCREMENT per la tabella `disambiguazione`
--
ALTER TABLE `disambiguazione`
  MODIFY `id_disamb` int(11) NOT NULL AUTO_INCREMENT;

--
-- Limiti per le tabelle scaricate
--

--
-- Limiti per la tabella `disambiguazione`
--
ALTER TABLE `disambiguazione`
  ADD CONSTRAINT `fk_segno_disamb` FOREIGN KEY (`id_segno_corretto`) REFERENCES `segni_lis` (`id_segno`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
