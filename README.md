# Wattson — catalogo delle impronte

Il catalogo condiviso degli elettrodomestici per [Wattson](https://github.com/tlabcustomaudio/wattson), l'investigatore dei consumi per Home Assistant.

Ogni voce dice quanto consuma un apparecchio e per quanto, misurato in una casa vera con una presa "profiler" e confrontato col contatore generale. Un Wattson appena installato lo usa per riconoscere subito gli apparecchi che altri hanno già misurato.

*English: a shared catalog of appliance power fingerprints (type · brand · model · product code · profile → watts and minutes), filled automatically by Wattson installs. Read `catalog.json`; contribute by opening an issue with the JSON block below.*

## Cosa contiene

`catalog.json` è una lista di voci:

| Campo | Esempio | Note |
|---|---|---|
| `tipo` | Deumidificatore | |
| `marca` | LG | |
| `modello` | Drymaster | |
| `codice` | DHB1260PL | codice prodotto, il più preciso |
| `profilo` | Laundry Dry | modalità o stato (es. *Stampa ABS*) |
| `w` | 205 | gradino sul contatore generale, W |
| `min` | 120 | durata tipica di un blocco, minuti |
| `n` | 3 | volte vista, in tutto |
| `case` | 1 | case diverse che l'hanno misurata (più alto = più affidabile) |
| `fonti` | | un contributo per casa, con id anonimo |

Una voce è la stessa se coincidono tipo, marca, modello, codice e profilo (senza maiuscole) e la potenza è entro ±15 %. `w` e `min` sono la media dei contributi, pesata sulle volte viste (al massimo 20 per casa, così nessuno domina la media).

I cinque campi di testo sono **tutti obbligatori**: una voce senza codice prodotto o senza profilo non entra.

## Privacy

Nel catalogo **non entra niente della casa**: niente nomi delle stanze o dei dispositivi, niente orari, niente indirizzi. Chi contribuisce è identificato solo da un hash del login GitHub, che serve a sostituire il proprio contributo quando lo si rimanda invece di sommarlo. L'issue con cui arriva il contributo resta pubblica, come ogni issue su GitHub.

## Come si contribuisce

**Con Wattson (automatico).** Nella vista *Impara* si impara un apparecchio con la presa Profiler compilando anche il **Tipo**. Se la condivisione è attiva, a fine sessione Wattson apre da solo un'issue qui, con il tuo account GitHub (lo colleghi una volta, come per HACS). La condivisione è **spenta di default**.

**A mano.** Apri un'issue con questo blocco nel testo:

````
```json
{"wattson": 1, "voci": [{"tipo": "Deumidificatore", "marca": "LG", "modello": "Drymaster",
  "codice": "DHB1260PL", "profilo": "Laundry Dry", "w": 205, "min": 120, "n": 1}]}
```
````

Una GitHub Action controlla il formato e i valori (w 150–10000 W, min 0,1–1440, niente link o indirizzi email), unisce il contributo a `catalog.json` e chiude l'issue. Se qualcosa non torna, l'issue resta aperta con l'etichetta `da-verificare`.

## Sviluppo

```bash
python3 tools/test_ingest.py
```
