# Minecraft Material Manager

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Minecraft Compatible](https://img.shields.io/badge/minecraft-1.16--1.21%2B-success.svg)](https://www.minecraft.net/)
[![UI Style](https://img.shields.io/badge/ui-Sun--Valley%20Dark-blurple.svg)](https://github.com/rinterdock/sv-ttk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Minecraft Material Manager e una applicazione desktop progettata per i giocatori tecnici, gli sviluppatori di mega-costruzioni e i creatori di progetti che necessitano di tracciare, organizzare e calcolare le risorse necessarie ai loro progetti in-game.

L'applicazione elimina la necessita di fogli di calcolo esterni, automatizzando il conteggio dei blocchi singoli e traducendo istantaneamente le unita di misura tipiche del gioco (Shulker Box e Stack) in valori numerici reali e viceversa.

---

## Funzionalita Principali

* **Compilatore Matematico Minecraft-Shorthand:** Permette l'inserimento di quantita complesse usando le abbreviazioni native del gioco. Espressioni come "1sb + 12stk + 32" vengono valutate ed elaborate in tempo reale fornendo il conteggio esatto dei singoli blocchi. Supporta i formati "sb" (Shulker Box) e "stk" / "stack".
* **Importazione Multiformato:** Sistema di parsing integrato in grado di elaborare stringhe di testo grezze, tabelle copiate dagli elenchi materiali di Litematica o file strutturati in formato JSON. Il filtro interno pulisce le stringhe ed esclude le intestazioni non rilevanti in automatico.
* **Tracciamento Avanzato Progresso:** Gestione dinamica dei materiali disponibili rispetto a quelli totali richiesti, con visualizzazione grafica dello stato di completamento tramite barre di avanzamento grafiche.
* **Interfaccia Grafica Moderna:** Interfaccia utente basata sul tema scuro Sun Valley con integrazione nativa degli stili di finestra Windows tramite libreria pywinstyles.
* **Installazione Automatizzata Dipendenze:** Script di avvio con controllo integrato dei pacchetti richiesti. Se librerie esterne come Pillow, tkinterdnd2 o litemapy mancano, il sistema provvede al loro download e configurazione al primo avvio.

---

## Esempi di Calcolo del Motore di Eval

Il sistema integra un parser matematico sicuro che converte la terminologia di gioco in interi e formatta i risultati finali per una lettura immediata:

| Stringa Input | Espressione Tradotta | Totale Blocchi | Formato Interfaccia |
| :--- | :--- | :--- | :--- |
| 1sb | 1 * 1728 | 1728 | 1SB |
| 2stk + 10 | 2 * 64 + 10 | 138 | 2stk + 10 |
| 1sb + 5stk | 1 * 1728 + 5 * 64 | 2048 | 1SB + 5^ |

---

## Architettura e Moduli del Progetto

Il codice e strutturato in modo modulare per garantire scalabilita e manutenzione:

* **core/config.py:** Gestione delle configurazioni utente, file JSON e palette cromatica dell'applicazione.
* **core/database.py:** Gestione dei dati dei progetti, calcolo dei materiali mancanti e logica di backup dei file di salvataggio.
* **core/scanner.py:** Parser per l'elaborazione dei file di input, delle stringhe di testo e delle formule matematiche.
* **core/utils.py:** Funzioni di utilita generale e formattazione intelligente dei blocchi.
* **ui/components.py:** Finestre di dialogo customizzate, messaggi di errore e barre di progresso grafiche.
* **ui/main_window.py:** Controller principale dell'interfaccia utente, gestione dei tab dei progetti e dei menu di sistema.

---

## Installazione e Requisiti

### Prerequisiti
L'applicazione richiede l'installazione di Python versione 3.8 o superiore.

### Procedura di avvio
1. Clonare la repository in locale:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
   cd YOUR_REPO_NAME
