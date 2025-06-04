# Progettazione AddressSpace - Sistema di Irrigazione

## Struttura dell'AddressSpace

```
Root/
└── Objects/
    └── IrrigationSystem/
        ├── Controller/
        │   ├── SystemState (Boolean) - Acceso/Spento
        │   ├── TurnOn() (Method)
        │   └── TurnOff() (Method)
        │
        └── Stations/
            ├── Station1/
            │   ├── StationInfo/
            │   │   ├── StationId (String)
            │   │   ├── StationType (String) - "SingleValve" o "DoubleValve"
            │   │   └── ValveCount (Int32)
            │   │
            │   ├── Valve1/
            │   │   ├── Status/
            │   │   │   ├── IsIrrigating (Boolean)
            │   │   │   ├── Mode (String) - "Manual" o "Automatic"
            │   │   │   ├── RemainingTime (Int32) - secondi
            │   │   │   └── NextScheduledStart (DateTime)
            │   │   │
            │   │   └── Commands/
            │   │       ├── StartManualIrrigation(duration) (Method)
            │   │       ├── StartAutomaticIrrigation(startTime, duration) (Method)
            │   │       └── StopIrrigation() (Method)
            │   │
            │   └── Valve2/ (solo per centraline a 2 rubinetti)
            │       ├── Status/
            │       │   ├── IsIrrigating (Boolean)
            │       │   ├── Mode (String)
            │       │   ├── RemainingTime (Int32)
            │       │   └── NextScheduledStart (DateTime)
            │       │
            │       └── Commands/
            │           ├── StartManualIrrigation(duration) (Method)
            │           ├── StartAutomaticIrrigation(startTime, duration) (Method)
            │           └── StopIrrigation() (Method)
            │
            ├── Station2/
            │   └── ... (stessa struttura)
            │
            └── Station3/
                └── ... (stessa struttura)
```

## Installazione Tipo di Esempio

- **Controller**: 1 unità di controllo principale
- **Station1**: Centralina a 2 rubinetti (giardino anteriore)
- **Station2**: Centralina a 1 rubinetto (aiuole laterali)  
- **Station3**: Centralina a 2 rubinetti (giardino posteriore)

## Tipi di Dati Personalizzati

### StationInfo ObjectType
- StationId: String
- StationType: String ("SingleValve" | "DoubleValve")
- ValveCount: Int32

### ValveStatus ObjectType
- IsIrrigating: Boolean
- Mode: String ("Manual" | "Automatic" | "Off")
- RemainingTime: Int32 (secondi rimanenti)
- NextScheduledStart: DateTime

### ValveCommands ObjectType
- StartManualIrrigation(duration: Int32): StatusCode
- StartAutomaticIrrigation(startTime: DateTime, duration: Int32): StatusCode
- StopIrrigation(): StatusCode

## Namespace

- Namespace URI: `http://mvlabs.it/irrigation`
- Namespace Index: 2 (assumendo 0=OPC-UA, 1=locale)

## Diagramma UML dell'AddressSpace

```mermaid
graph TD
    A[Objects] --> B[IrrigationSystem]
    B --> C[Controller]
    B --> D[Stations]
    
    C --> C1[SystemState: Boolean]
    C --> C2[TurnOn: Method]
    C --> C3[TurnOff: Method]
    
    D --> S1[Station1]
    D --> S2[Station2] 
    D --> S3[Station3]
    
    S1 --> S1I[StationInfo]
    S1 --> S1V1[Valve1]
    S1 --> S1V2[Valve2]
    
    S1I --> S1I1[StationId: String]
    S1I --> S1I2[StationType: String]
    S1I --> S1I3[ValveCount: Int32]
    
    S1V1 --> S1V1S[Status]
    S1V1 --> S1V1C[Commands]
    
    S1V1S --> S1V1S1[IsIrrigating: Boolean]
    S1V1S --> S1V1S2[Mode: String]
    S1V1S --> S1V1S3[RemainingTime: Int32]
    S1V1S --> S1V1S4[NextScheduledStart: DateTime]
    
    S1V1C --> S1V1C1[StartManualIrrigation: Method]
    S1V1C --> S1V1C2[StartAutomaticIrrigation: Method]
    S1V1C --> S1V1C3[StopIrrigation: Method]
```

## Esempi di NodeId

### Controller
- `ns=2;s=IrrigationSystem.Controller.SystemState`
- `ns=2;s=IrrigationSystem.Controller.TurnOn`
- `ns=2;s=IrrigationSystem.Controller.TurnOff`

### Stazioni
- `ns=2;s=IrrigationSystem.Stations.Station1.StationInfo.StationId`
- `ns=2;s=IrrigationSystem.Stations.Station1.Valve1.Status.IsIrrigating`
- `ns=2;s=IrrigationSystem.Stations.Station1.Valve1.Commands.StartManualIrrigation`

## Permissions e Security

### Livelli di Accesso
- **Read Only**: Tutti i nodi Status
- **Read/Write**: SystemState (solo per admin)
- **Execute**: Tutti i metodi Commands (autenticazione richiesta)

### Security Policies
- **None**: Per testing e sviluppo
- **Basic128Rsa15**: Per ambienti di produzione
- **Basic256Sha256**: Raccomandato per sicurezza massima