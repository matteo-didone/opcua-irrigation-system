# 🌱 Sistema di Irrigazione OPC-UA

Un sistema completo di controllo irrigazione implementato con OPC-UA, sviluppato per l'esercitazione del corso di Automazione Industriale.

## 📋 Descrizione

Il sistema simula un impianto di irrigazione per giardino composto da:

- **1 Controller principale**: gestisce l'accensione/spegnimento del sistema
- **3 Centraline**: controllano i rubinetti dell'acqua
  - Station1: 2 rubinetti (giardino anteriore)
  - Station2: 1 rubinetto (aiuole laterali)
  - Station3: 2 rubinetti (giardino posteriore)

## 🏗️ Architettura

```
┌─────────────────┐    OPC-UA    ┌─────────────────┐
│   Server        │◄─────────────┤   Client        │
│   irrigation_   │              │   monitor_      │
│   server.py     │              │   client.py     │
└─────────────────┘              └─────────────────┘
                                          │
                                          │ OPC-UA
                                          ▼
                                 ┌─────────────────┐
                                 │   Client        │
                                 │   control_      │
                                 │   client.py     │
                                 └─────────────────┘
```

## 📁 Struttura del Progetto

```
opcua-irrigation-system/
├── server/
│   └── irrigation_server.py     # Server OPC-UA principale
├── client/
│   ├── monitor_client.py        # Client per monitoraggio
│   └── control_client.py        # Client per controllo
├── config/
│   └── server_config.py         # Configurazioni server
├── docs/
│   └── addressspace_design.md   # Documentazione AddressSpace
├── requirements.txt             # Dipendenze Python
└── README.md                   # Questo file
```

## 🚀 Installazione e Setup

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Avvia il server

```bash
python server/irrigation_server.py
```

Il server sarà disponibile su: `opc.tcp://localhost:4840/irrigation`

### 3. Avvia il monitoraggio (in un nuovo terminale)

```bash
# Monitoraggio continuo
python client/monitor_client.py

# Lettura singola
python client/monitor_client.py -s
```

### 4. Controlla l'irrigazione (in un altro terminale)

```bash
# Modalità interattiva
python client/control_client.py

# Comandi diretti
python client/control_client.py start Station1 Valve1 300
python client/control_client.py stop Station1 Valve1
```

## 🎮 Utilizzo

### Server OPC-UA

Il server espone automaticamente:
- Sistema con 3 stazioni preconfigurate
- Aggiornamento stato ogni secondo
- Metodi per controllo irrigazione
- Simulazione realistica dei tempi

### Client di Monitoraggio

```bash
# Monitoraggio continuo con aggiornamento ogni 2 secondi
python client/monitor_client.py

# Monitoraggio ogni 5 secondi
python client/monitor_client.py -i 5

# Lettura singola dello stato
python client/monitor_client.py -s

# Server remoto
python client/monitor_client.py -u opc.tcp://192.168.1.100:4840/irrigation
```

### Client di Controllo

#### Modalità Interattiva
```bash
python client/control_client.py
🌿 > help                              # Mostra comandi
🌿 > list                              # Elenca stazioni
🌿 > status                            # Stato sistema
🌿 > on                                # Accende sistema
🌿 > start Station1 Valve1 300         # Irriga 5 minuti
🌿 > auto Station2 Valve1 06:00 1800   # Programma alle 06:00 per 30 min
🌿 > stop Station1 Valve1              # Ferma irrigazione
🌿 > exit                              # Esce
```

#### Modalità Comando
```bash
# Controllo sistema
python client/control_client.py on
python client/control_client.py off
python client/control_client.py status

# Irrigazione manuale
python client/control_client.py start Station1 Valve1 300

# Ferma irrigazione
python client/control_client.py stop Station1 Valve1

# Lista stazioni
python client/control_client.py list
```

## 🌐 AddressSpace OPC-UA

### Struttura Completa

```
Objects/
└── IrrigationSystem/
    ├── Controller/
    │   ├── SystemState (Boolean)
    │   ├── TurnOn() (Method)
    │   └── TurnOff() (Method)
    └── Stations/
        ├── Station1/ (DoubleValve)
        │   ├── StationInfo/
        │   ├── Valve1/
        │   │   ├── Status/
        │   │   └── Commands/
        │   └── Valve2/
        ├── Station2/ (SingleValve)
        └── Station3/ (DoubleValve)
```

### Namespace

- **URI**: `http://mvlabs.it/irrigation`
- **Index**: 2

## 📊 Esempi di Scenario

### Scenario 1: Irrigazione Mattutina
```bash
# 1. Accendi il sistema
python client/control_client.py on

# 2. Programma irrigazione automatica alle 06:00
python client/control_client.py auto Station1 Valve1 06:00 1800  # 30 min
python client/control_client.py auto Station2 Valve1 06:30 900   # 15 min
python client/control_client.py auto Station3 Valve1 07:00 1200  # 20 min

# 3. Monitora il sistema
python client/monitor_client.py
```

### Scenario 2: Irrigazione di Emergenza
```bash
# 1. Verifica stato
python client/control_client.py status

# 2. Avvia irrigazione immediata
python client/control_client.py start Station1 Valve1 600   # 10 minuti
python client/control_client.py start Station1 Valve2 600   # 10 minuti

# 3. Monitora in tempo reale
python client/monitor_client.py -i 1  # aggiornamento ogni secondo
```

## 🔧 Configurazione

### Parametri Server
- **Endpoint**: `opc.tcp://localhost:4840/irrigation`
- **Aggiornamento**: 1 secondo
- **Security**: None (per sviluppo)

### Personalizzazione
Modifica `server/irrigation_server.py` per:
- Cambiare numero di stazioni
- Modificare numero di valvole per stazione
- Aggiungere sensori (temperatura, umidità, etc.)
- Implementare logiche di irrigazione più complesse

## 🐛 Troubleshooting

### Server non si avvia
```
❌ Errore: [Errno 98] Address already in use
```
**Soluzione**: Un altro processo sta usando la porta 4840
```bash
# Linux/Mac
sudo lsof -i :4840
kill <PID>

# Windows
netstat -ano | findstr :4840
taskkill /PID <PID> /F
```

### Client non si connette
```
❌ Impossibile connettersi al server OPC-UA
```
**Soluzioni**:
1. Verifica che il server sia in esecuzione
2. Controlla firewall/antivirus
3. Verifica l'URL del server

### Errori di dipendenze
```
❌ Libreria asyncua non trovata!
```
**Soluzione**:
```bash
pip install asyncua
# oppure
pip install -r requirements.txt
```

## 📚 Riferimenti

- [Documentazione OPC-UA](https://opcfoundation.org/)
- [Libreria asyncua](https://python-opcua.readthedocs.io/)
- [Specifica OPC-UA](https://reference.opcfoundation.org/)

## 👥 Autori

Sviluppato per il corso di Automazione Industriale - MVLabs
- Esercitazione OPC-UA
- Sistema di Irrigazione IoT

## 📄 Licenza

Progetto didattico - Uso educativo

---

🌱 **Happy Irrigation!** 🌱