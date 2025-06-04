#!/usr/bin/env python3
"""
Configurazione per il Server OPC-UA del Sistema di Irrigazione
"""

# Configurazione Server OPC-UA
SERVER_CONFIG = {
    # Endpoint del server
    "endpoint": "opc.tcp://localhost:4840/irrigation",
    
    # Nome del server
    "server_name": "Irrigation System Server",
    
    # URI del namespace personalizzato  
    "namespace_uri": "http://mvlabs.it/irrigation",
    
    # Intervallo di aggiornamento in secondi
    "update_interval": 1.0,
    
    # Configurazione logging
    "log_level": "INFO",
    
    # Security (per sviluppo)
    "security_policy": "None",
    
    # Certificate settings (se security abilitata)
    "certificate_path": None,
    "private_key_path": None,
}

# Configurazione installazione di default
INSTALLATION_CONFIG = {
    "stations": [
        {
            "id": "Station1",
            "description": "Giardino Anteriore", 
            "valve_count": 2,
            "type": "DoubleValve"
        },
        {
            "id": "Station2", 
            "description": "Aiuole Laterali",
            "valve_count": 1,
            "type": "SingleValve"
        },
        {
            "id": "Station3",
            "description": "Giardino Posteriore",
            "valve_count": 2, 
            "type": "DoubleValve"
        }
    ]
}

# Configurazione comportamento valvole
VALVE_CONFIG = {
    # Durata minima/massima irrigazione (secondi)
    "min_duration": 10,
    "max_duration": 7200,  # 2 ore
    
    # Durata di default per test
    "default_test_duration": 300,  # 5 minuti
    
    # Simulazione consumo acqua
    "water_flow_rate": 5.0,  # litri/minuto
}

# Configurazione Client 
CLIENT_CONFIG = {
    # Server di default
    "default_server_url": "opc.tcp://localhost:4840/irrigation",
    
    # Timeout connessione
    "connection_timeout": 10.0,
    
    # Intervallo monitoraggio
    "default_monitor_interval": 2,
    
    # Namespace del sistema
    "irrigation_namespace": "http://mvlabs.it/irrigation",
}

# Messaggi e descrizioni
MESSAGES = {
    "system_on": "🟢 Sistema di irrigazione acceso",
    "system_off": "🔴 Sistema di irrigazione spento", 
    "irrigation_started": "💧 Irrigazione avviata",
    "irrigation_stopped": "⭕ Irrigazione fermata",
    "irrigation_scheduled": "⏰ Irrigazione programmata",
    "station_descriptions": {
        "Station1": "Giardino Anteriore",
        "Station2": "Aiuole Laterali",
        "Station3": "Giardino Posteriore"
    }
}

# Funzioni di utilità
def get_server_endpoint():
    """Restituisce l'endpoint del server"""
    return SERVER_CONFIG["endpoint"]

def get_namespace_uri():
    """Restituisce l'URI del namespace"""
    return SERVER_CONFIG["namespace_uri"]

def get_station_description(station_id: str) -> str:
    """Restituisce la descrizione di una stazione"""
    return MESSAGES["station_descriptions"].get(station_id, station_id)

def validate_duration(duration: int) -> bool:
    """Valida la durata dell'irrigazione"""
    return VALVE_CONFIG["min_duration"] <= duration <= VALVE_CONFIG["max_duration"]

def format_duration(seconds: int) -> str:
    """Formatta la durata in formato leggibile"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

# Esempi di utilizzo
if __name__ == "__main__":
    print("🌱 Configurazione Sistema di Irrigazione")
    print("=" * 50)
    print(f"Server Endpoint: {get_server_endpoint()}")
    print(f"Namespace URI: {get_namespace_uri()}")
    print()
    
    print("Stazioni configurate:")
    for station in INSTALLATION_CONFIG["stations"]:
        desc = get_station_description(station["id"])
        print(f"  - {station['id']}: {desc} ({station['valve_count']} valvole)")
    
    print()
    print("Configurazione valvole:")
    print(f"  - Durata min: {format_duration(VALVE_CONFIG['min_duration'])}")
    print(f"  - Durata max: {format_duration(VALVE_CONFIG['max_duration'])}")
    print(f"  - Portata acqua: {VALVE_CONFIG['water_flow_rate']} l/min")