# Minecraft Material Manager

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/)
[![Minecraft Compatible](https://img.shields.io/badge/minecraft-1.16--1.21%2B-success.svg)](https://www.minecraft.net/)
[![Litematica Extension](https://img.shields.io/badge/litematica-supported-orange.svg)](https://www.curseforge.com/minecraft/mc-mods/litematica)
[![UI Style](https://img.shields.io/badge/ui-Sun--Valley%20Dark-blurple.svg)](https://github.com/rinterdock/sv-ttk)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Minecraft Material Manager e una applicazione desktop progettata specificamente per la comunita del technical Minecraft, per i creatori di mega-costruzioni e per chiunque utilizzi la mod Litematica per pianificare le proprie strutture in-game. 

Quando si affrontano progetti su larga scala, la gestione dei materiali richiesti diventa complessa. Litematica fornisce l'elenco dei blocchi totali, ma non offre uno strumento dinamico per tracciare cio che si e gia raccolto rispetto a cio che manca, ne permette di calcolare i blocchi usando le unita di misura reali del gioco (Shulker Box e Stack). Questa applicazione risolve esattamente questo problema, automatizzando il calcolo delle risorse necessarie e interfacciandosi direttamente con i dati di Litematica.

---

## Funzionalita Principali

* **Compilatore Matematico Minecraft-Shorthand:** Permette di inserire e sommare le quantita di blocchi usando la terminologia del gioco. Scrivendo stringhe come "1sb + 12stk + 32" il sistema calcola all'istante il totale di 2528 blocchi singoli. Il parser supporta i modificatori "sb" (Shulker Box da 1728 blocchi), "stk" o "stack" (da 64 blocchi) ed espressioni matematiche complesse.
* **Integrazione Nativa Litematica:** Include filtri di scansione regex dedicati per riconoscere la struttura delle tabelle generate da Litematica. Pulisce il testo formattato rimuovendo i separatori grafici e isolando istantaneamente i nomi dei blocchi e le quantita necessarie.
* **Scomposizione in Materie Prime:** Il motore interno e in grado di analizzare le ricette di crafting (shaped e shapeless). Se il progetto richiede un oggetto composto, l'applicazione puo scomporlo fino a calcolare il quantitativo esatto di materie prime fondamentali necessarie.
* **Tracciamento Avanzato e Differenziale:** Consente di inserire i materiali gia a disposizione e calcola in tempo reale la quantita esatta di risorse mancanti, mostrando lo stato di avanzamento complessivo tramite barre di progresso grafiche integrate nell'interfaccia.
* **Interfaccia Grafica Ottimizzata:** GUI basata sul tema scuro moderno Sun Valley con ottimizzazioni per l'ambiente desktop Windows tramite pywinstyles, garantendo una visualizzazione chiara e riposante durante le lunghe sessioni di gioco.
* **Gestione Automatica dei Pacchetti:** Non richiede configurazioni manuali del terminale. Lo script controlla la presenza dei moduli Python necessari (Pillow, tkinterdnd2, pywinstyles, sv-ttk, litemapy) e, se mancanti, avvia un'installazione automatica trasparente al primo avvio.

---

## Guida all'Uso con Litematica

L'applicazione e progettata per azzerare i tempi di trascrizione manuale. Di seguito viene spiegato come prelevare l'elenco dei blocchi da una costruzione e caricarlo nel programma.

### 1. Estrazione della Lista dei Materiali da Litematica
1. All'interno del tuo mondo Minecraft, apri l'interfaccia di Litematica premendo il tasto di configurazione (di default il tasto M).
2. Accedi alla sezione **Schematic Placements** (o dal Task Manager se stai tracciando una build attiva).
3. Individua lo schematic della tua costruzione e clicca sul pulsante **Material List**.
4. Nella schermata che mostra la tabella di tutti i blocchi richiesti, hai due opzioni:
   * Cliccare sul pulsante **Copy to Clipboard** in basso per copiare l'intera tabella formattata negli appunti di sistema.
   * Cliccare sul pulsante **Dump to File** per salvare l'elenco in un file di testo con estensione `.txt` all'interno della cartella dei file di configurazione di Minecraft.

### 2. Importazione ed Elaborazione nel Programma
* **Importazione da Appunti (Clipboard):** All'interno di Minecraft Material Manager, seleziona il tuo progetto attivo e usa la funzione di importazione rapida da appunti. L'applicazione analizzera il testo, ignorera le righe di intestazione della mod (come colonne Item, Total, Missing) e inserira nel database solo i blocchi effettivi della costruzione.
* **Importazione da File (Drag and Drop):** Prendi il file `.txt` generato dal comando "Dump to File" di Litematica e trascinalo direttamente all'interno della finestra dell'applicazione. Il modulo core/scanner.py applichera l'espressione regolare dedicata per estrarre i dati in meno di un secondo.

---

## Esempi di Calcolo del Motore di Eval

Il parser traduce in modo sicuro le stringhe matematiche ed esegue la formattazione intelligente inversa nell'interfaccia utente:

| Stringa di Input | Espressione Tradotta | Totale Blocchi | Formato Visualizzato |
| :--- | :--- | :--- | :--- |
| 1sb | 1 * 1728 | 1728 | 1SB |
| 2stk + 10 | 2 * 64 + 10 | 138 | 2stk + 10 |
| 1sb + 5stk | 1 * 1728 + 5 * 64 | 2048 | 1SB + 5^ |

---

## Architettura del Codice

Il software e suddiviso in moduli indipendenti per facilitare lo sviluppo e l'estensione delle funzionalita:

* **core/config.py:** Gestione dei file di configurazione generali in formato JSON e definizione della palette cromatica scura dell'interfaccia.
* **core/database.py:** Gestione del database interno dei progetti, tracciamento dello stato dei materiali (richiesti, disponibili, mancanti) e scomposizione delle ricette di crafting.
* **core/scanner.py:** Motore di parsing testuale ottimizzato per l'elaborazione dei file TXT, JSON e delle stringhe tabellari di Litematica.
* **core/utils.py:** Funzioni matematiche di utilita generale, algoritmi di calcolo delle formule Minecraft-Shorthand e regex di filtraggio.
* **ui/components.py:** Componenti grafici riutilizzabili, finestre di dialogo personalizzate e barre di progresso basate su Canvas.
* **ui/main_window.py:** Finestra principale dell'applicazione e gestione dei flussi logici della GUI.

---

## Installazione e Avvio

### Prerequisiti
L'applicazione richiede Python versione 3.8 o superiore installato sul sistema.

### Procedura di Configurazione
1. Clonare la repository o scaricare i file sorgenti in una cartella locale:
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
   cd YOUR_REPO_NAME
