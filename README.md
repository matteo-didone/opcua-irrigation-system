# 🌱 Sistema di Irrigazione OPC-UA Professionale

Un sistema completo di controllo irrigazione implementato con **ObjectTypes personalizzati OPC-UA**, sviluppato per l'esercitazione del corso di Automazione Industriale.

## 📋 Descrizione

Il sistema simula un impianto di irrigazione professionale per giardino composto da:

- **1 Controller principale**: gestisce l'accensione/spegnimento del sistema
- **3 Centraline**: controllano i rubinetti dell'acqua con ObjectTypes dedicati
  - Station1: 2 rubinetti (giardino anteriore) - DoubleValve
  - Station2: 1 rubinetto (aiuole laterali) - SingleValve
  - Station3: 2 rubinetti (giardino posteriore) - DoubleValve

## 🏗️ Architettura Professionale

```
┌─────────────────────────┐    OPC-UA    ┌─────────────────────────┐
│   Professional Server  │◄─────────────┤   Professional Monitor  │
│   + ObjectTypes        │              │   Client                │
│   irrigation_server.py │              │   monitor_client.py     │
└─────────────────────────┘              └─────────────────────────┘
            │                                        │
            │ Export NodeSet                         │ OPC-UA
            ▼                                        ▼
┌─────────────────────────┐              ┌─────────────────────────┐
│   UAModeler            │              │   Professional Control │
│   + ObjectTypes        │              │   Client                │
│   Import/Edit          │              │   control_client.py     │
└─────────────────────────┘              └─────────────────────────┘
```

## 🔧 ObjectTypes Personalizzati

### Information Model Professionale

```
IrrigationSystemType (ObjectType)
├── Controller/
│   └── SystemState (Boolean, Writable)
└── Stations/
    └── [IrrigationStationType instances]

IrrigationStationType (ObjectType)
├── StationInfo/
│   ├── StationId (String)
│   ├── Description (String)
│   ├── StationType (String)
│   └── ValveCount (Int32)
└── [IrrigationValveType instances]

IrrigationValveType (ObjectType)
├── Description (String)
├── Status/
│   ├── IsIrrigating (Boolean)
│   ├── Mode (String)
│   ├── RemainingTime (Int32)
│   └── NextScheduledStart (DateTime)
└── Commands/
    ├── CommandDuration (Int32, Writable)
    ├── CommandStart (Boolean, Writable)
    └── CommandStop (Boolean, Writable)
```

## 🚀 Installazione e Setup

### 1. Installa le dipendenze

```bash
pip install -r requirements.txt
```

### 2. Avvia il server professionale

```bash
python server/irrigation_server.py
```

Il server sarà disponibile su: `opc.tcp://localhost:48400/irrigation`

**Comandi server**:
- Premi `e` + INVIO per esportare NodeSet XML per UAModeler
- Premi `q` + INVIO per uscire

### 3. Avvia il monitoraggio (in un nuovo terminale)

```bash
# Monitoraggio continuo professionale
python client/monitor_client.py

# Lettura singola con ObjectTypes
python client/monitor_client.py -s

# Monitoraggio personalizzato
python client/monitor_client.py -i 1  # Aggiornamento ogni secondo
```

### 4. Controlla l'irrigazione (in un altro terminale)

```bash
# Modalità interattiva professionale
python client/control_client.py

# Comandi diretti con struttura gerarchica
python client/control_client.py start Station1_Valve1 300
python client/control_client.py stop Station1_Valve1
```

## 🎮 Utilizzo Professionale

### Server OPC-UA con ObjectTypes

Il server espone automaticamente:
- **ObjectTypes personalizzati**: IrrigationSystemType, IrrigationStationType, IrrigationValveType
- **Istanze strutturate**: Sistema → Stations → StationX → ValveY
- **Export automatico**: NodeSet XML per UAModeler
- **Aggiornamento real-time**: Stato ogni secondo con tipi coerenti

### Client di Monitoraggio Professionale

```bash
# Monitoraggio con architettura ObjectTypes
python client/monitor_client.py

# Visualizzazione gerarchica:
# IrrigationSystem/Controller + Stations/StationX/ValveY

# Opzioni avanzate
python client/monitor_client.py -i 5    # Ogni 5 secondi
python client/monitor_client.py -s      # Lettura singola
python client/monitor_client.py -u opc.tcp://remote:48400/irrigation
```

### Client di Controllo Professionale

#### Modalità Interattiva
```bash
python client/control_client.py
🌿 > help                                    # Mostra comandi
🌿 > list                                    # Struttura gerarchica
🌿 > status                                  # Stato sistema + valvole attive
🌿 > on                                      # Accende sistema
🌿 > start Station1_Valve1 300               # Irriga valvola specifica
🌿 > stop Station1_Valve1                    # Ferma irrigazione
🌿 > exit                                    # Esce
```

#### Struttura Comandi
```bash
# Controllo sistema
python client/control_client.py on
python client/control_client.py off
python client/control_client.py status

# Irrigazione con naming gerarchico
python client/control_client.py start Station1_Valve1 300  # Giardino Anteriore - Valvola 1
python client/control_client.py start Station2_Valve1 180  # Aiuole Laterali - Valvola 1
python client/control_client.py start Station3_Valve2 240  # Giardino Posteriore - Valvola 2

# Ferma irrigazione
python client/control_client.py stop Station1_Valve1

# Lista con descrizioni
python client/control_client.py list
```

## 🌐 AddressSpace OPC-UA Professionale

### Struttura Gerarchica Completa

```
Objects/
└── IrrigationSystem/ (IrrigationSystemType)
    ├── Controller/
    │   └── SystemState (Boolean, Writable)
    └── Stations/
        ├── Station1/ (IrrigationStationType)
        │   ├── StationInfo/
        │   │   ├── StationId: "Station1"
        │   │   ├── Description: "Giardino Anteriore"
        │   │   ├── StationType: "DoubleValve"
        │   │   └── ValveCount: 2
        │   ├── Valve1/ (IrrigationValveType)
        │   │   ├── Description: "Giardino Anteriore - Valvola 1"
        │   │   ├── Status/
        │   │   │   ├── IsIrrigating (Boolean)
        │   │   │   ├── Mode (String)
        │   │   │   ├── RemainingTime (Int32)
        │   │   │   └── NextScheduledStart (DateTime)
        │   │   └── Commands/
        │   │       ├── CommandDuration (Int32, Writable)
        │   │       ├── CommandStart (Boolean, Writable)
        │   │       └── CommandStop (Boolean, Writable)
        │   └── Valve2/ (IrrigationValveType)
        ├── Station2/ (IrrigationStationType - SingleValve)
        └── Station3/ (IrrigationStationType - DoubleValve)
```

### Namespace e ObjectTypes

- **URI**: `http://mvlabs.it/irrigation`
- **Index**: 2
- **ObjectTypes**: Visibili in UAModeler sotto Types → ObjectTypes
- **Istanze**: Sotto Objects → IrrigationSystem

## 📊 Scenari di Utilizzo Professionale

### Scenario 1: Test Completo ObjectTypes
```bash
# 1. Avvia server con ObjectTypes
python server/irrigation_server.py

# 2. Esporta NodeSet per UAModeler (nel server)
e

# 3. Importa in UAModeler
# File → Import → irrigation_professional_nodeset.xml

# 4. Testa funzionalità
python client/control_client.py
🌿 > list
🌿 > start Station1_Valve1 60
🌿 > status
```

### Scenario 2: Monitoraggio Multi-Valvola
```bash
# 1. Avvia irrigazione su più valvole
python client/control_client.py start Station1_Valve1 300
python client/control_client.py start Station1_Valve2 240
python client/control_client.py start Station3_Valve1 180

# 2. Monitora in tempo reale
python client/monitor_client.py -i 1

# 3. Verifica countdown simultaneo
```

### Scenario 3: Validazione Architettura
```bash
# 1. Verifica ObjectTypes in UAModeler
# Types → ObjectTypes → IrrigationSystemType, etc.

# 2. Verifica istanze
# Objects → IrrigationSystem → Controller + Stations

# 3. Test modifiche in UAModeler
# Aggiungi proprietà → Esporta → Reimporta
```

## 🔧 Configurazione Professionale

### Parametri Server
- **Endpoint**: `opc.tcp://localhost:48400/irrigation`
- **Aggiornamento**: 1 secondo con tipi OPC-UA corretti
- **Security**: None (per sviluppo)
- **ObjectTypes**: Creati automaticamente all'avvio

### Export NodeSet
Il server può esportare automaticamente il NodeSet XML:
```bash
# Durante l'esecuzione del server
e  # Genera irrigation_professional_nodeset.xml
```

### UAModeler Integration
1. **Import**: File → Import → NodeSet → `irrigation_professional_nodeset.xml`
2. **Visualizza ObjectTypes**: Types → ObjectTypes
3. **Visualizza Istanze**: Objects → IrrigationSystem
4. **Modifica**: Personalizza ObjectTypes e istanze
5. **Export**: File → Export → NodeSet per riutilizzo

## 🐛 Troubleshooting Professionale

### Errori di Tipo (Type Mismatch)
```
❌ BadTypeMismatch: Int64 vs Int32
```
**Soluzione**: Il server usa tipi OPC-UA corretti (Int32) automaticamente

### ObjectTypes non visibili in UAModeler
```
❌ ObjectTypes mancanti
```
**Soluzioni**:
1. Verifica che l'import del NodeSet sia andato a buon fine
2. Controlla Types → ObjectTypes nella vista ad albero
3. Assicurati di aver importato il file `irrigation_professional_nodeset.xml`

### Client non trova la struttura gerarchica
```
❌ Errore: BadNoMatch
```
**Soluzione**: 
1. Verifica che il server professionale sia in esecuzione
2. Usa i nomi corretti: `Station1_Valve1`, non `Station1/Valve1`
3. Controlla il namespace URI: `http://mvlabs.it/irrigation`

### Server non si avvia
```
❌ Errore: Address already in use
```
**Soluzione**: Porta 48400 occupata
```bash
# Windows
netstat -ano | findstr :48400
taskkill /PID <PID> /F

# Linux/Mac
sudo lsof -i :48400
kill <PID>
```

## 📚 Riferimenti Professionali

- [OPC-UA Specification](https://opcfoundation.org/developer-tools/specifications-unified-architecture/)
- [Information Modeling](https://opcfoundation.org/developer-tools/documents/)
- [Asyncua Documentation](https://python-opcua.readthedocs.io/)
- [UAModeler Guide](https://www.unified-automation.com/products/development-tools/uamodeler.html)
- [OPC-UA Companion Specifications](https://opcfoundation.org/markets-collaboration/specifications/)