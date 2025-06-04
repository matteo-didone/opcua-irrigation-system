#!/usr/bin/env python3
"""
Monitor client semplificato per il server con variabili
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Dict

from asyncua import Client
from asyncua.common.node import Node

# Configurazione logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class SimpleIrrigationMonitor:
    """Monitor per il server semplificato"""
    
    def __init__(self, server_url: str = "opc.tcp://localhost:48400/irrigation"):
        self.server_url = server_url
        self.client = Client(server_url)
        self.ns_idx = None
        self.nodes: Dict[str, Node] = {}
        
    async def connect(self):
        """Connette al server"""
        try:
            await self.client.connect()
            print(f"✅ Connesso al server: {self.server_url}")
            
            # Trova namespace
            namespaces = await self.client.get_namespace_array()
            for i, ns in enumerate(namespaces):
                if "mvlabs.it/irrigation" in ns:
                    self.ns_idx = i
                    break
                    
            if self.ns_idx is None:
                raise Exception("Namespace del sistema di irrigazione non trovato")
                
            # Scopri nodi
            await self._discover_nodes()
            print("✅ Sistema di irrigazione scoperto")
            
        except Exception as e:
            print(f"❌ Errore durante la connessione: {e}")
            raise
            
    async def _discover_nodes(self):
        """Scopre tutti i nodi del sistema semplificato"""
        root = self.client.get_objects_node()
        
        # Sistema di irrigazione
        irrigation_system = await root.get_child([f"{self.ns_idx}:IrrigationSystem"])
        
        # Stato sistema
        system_state = await irrigation_system.get_child([f"{self.ns_idx}:SystemState"])
        self.nodes["system_state"] = system_state
        
        # Valvole (struttura semplificata)
        valve_ids = ["Station1_Valve1", "Station1_Valve2", "Station2_Valve1", "Station3_Valve1", "Station3_Valve2"]
        
        for valve_id in valve_ids:
            try:
                valve_node = await irrigation_system.get_child([f"{self.ns_idx}:{valve_id}"])
                
                # Status
                is_irrigating = await valve_node.get_child([f"{self.ns_idx}:IsIrrigating"])
                mode = await valve_node.get_child([f"{self.ns_idx}:Mode"])
                remaining_time = await valve_node.get_child([f"{self.ns_idx}:RemainingTime"])
                
                self.nodes[f"{valve_id}_irrigating"] = is_irrigating
                self.nodes[f"{valve_id}_mode"] = mode
                self.nodes[f"{valve_id}_remaining"] = remaining_time
                
            except:
                pass  # Valvola non trovata, salta
                
    async def read_system_status(self) -> Dict:
        """Legge lo stato completo del sistema"""
        status = {}
        
        # Stato sistema
        system_on = await self.nodes["system_state"].read_value()
        status["system"] = {"on": system_on}
        
        # Valvole raggruppate per stazione
        status["stations"] = {
            "Station1": {"valves": {}},
            "Station2": {"valves": {}}, 
            "Station3": {"valves": {}}
        }
        
        # Leggi stato di ogni valvola
        valve_mapping = {
            "Station1_Valve1": ("Station1", "Valve1"),
            "Station1_Valve2": ("Station1", "Valve2"),
            "Station2_Valve1": ("Station2", "Valve1"),
            "Station3_Valve1": ("Station3", "Valve1"),
            "Station3_Valve2": ("Station3", "Valve2")
        }
        
        for valve_id, (station_id, valve_name) in valve_mapping.items():
            if f"{valve_id}_irrigating" in self.nodes:
                try:
                    is_irrigating = await self.nodes[f"{valve_id}_irrigating"].read_value()
                    mode = await self.nodes[f"{valve_id}_mode"].read_value()
                    remaining_time = await self.nodes[f"{valve_id}_remaining"].read_value()
                    
                    status["stations"][station_id]["valves"][valve_name] = {
                        "irrigating": is_irrigating,
                        "mode": mode,
                        "remaining_time": remaining_time
                    }
                except:
                    pass
                    
        return status
        
    def format_status_display(self, status: Dict) -> str:
        """Formatta lo stato per la visualizzazione"""
        output = []
        output.append("=" * 70)
        output.append("           🌱 STATO SISTEMA DI IRRIGAZIONE 🌱")
        output.append("=" * 70)
        
        # Stato sistema
        system_state = "🟢 ACCESO" if status["system"]["on"] else "🔴 SPENTO"
        output.append(f"🏠 Sistema: {system_state}")
        output.append("")
        
        # Descrizioni stazioni
        descriptions = {
            "Station1": "Giardino Anteriore",
            "Station2": "Aiuole Laterali", 
            "Station3": "Giardino Posteriore"
        }
        
        # Stato stazioni
        for station_id, station_data in status["stations"].items():
            if not station_data["valves"]:
                continue
                
            description = descriptions.get(station_id, station_id)
            valve_count = len(station_data["valves"])
            station_type = "DoubleValve" if valve_count > 1 else "SingleValve"
            
            output.append(f"📍 {station_id} - {description}")
            output.append(f"   Tipo: {station_type} ({valve_count} valvole)")
            output.append("-" * 60)
            
            for valve_name, valve_data in station_data["valves"].items():
                # Icona e stato
                if valve_data["irrigating"]:
                    icon = "💧"
                    state = "IRRIGANDO"
                    color = "\033[94m"  # Blu
                elif valve_data["mode"] == "Automatic":
                    icon = "⏰"
                    state = "PROGRAMMATA"
                    color = "\033[93m"  # Giallo
                else:
                    icon = "⭕"
                    state = "FERMA"
                    color = "\033[90m"  # Grigio
                
                reset_color = "\033[0m"
                
                output.append(f"  {icon} {color}{valve_name}: {state}{reset_color}")
                output.append(f"      Modalità: {valve_data['mode']}")
                
                if valve_data["irrigating"]:
                    mins, secs = divmod(valve_data["remaining_time"], 60)
                    output.append(f"      ⏱️  Tempo rimanente: {mins:02d}:{secs:02d}")
                        
                output.append("")
                
        output.append("=" * 70)
        return "\n".join(output)
        
    def clear_screen(self):
        """Pulisce lo schermo"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    async def monitor_continuous(self, interval: int = 2):
        """Monitoraggio continuo del sistema"""
        print("🌱 Avvio monitoraggio sistema di irrigazione...")
        print("   Premi Ctrl+C per uscire")
        print("")
        input("Premi INVIO per iniziare...")
        
        try:
            while True:
                self.clear_screen()
                
                # Leggi e mostra stato
                status = await self.read_system_status()
                display = self.format_status_display(status)
                print(display)
                
                # Timestamp aggiornamento
                now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                print(f"🕐 Ultimo aggiornamento: {now}")
                print(f"🔄 Prossimo aggiornamento tra {interval} secondi...")
                print("\n💡 Suggerimento: Usa simple_control_client.py per controllare l'irrigazione")
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoraggio interrotto dall'utente")
            
    async def monitor_once(self):
        """Mostra lo stato una sola volta"""
        print("📊 Lettura stato sistema di irrigazione...")
        status = await self.read_system_status()
        display = self.format_status_display(status)
        print(display)
        
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        print(f"🕐 Stato letto il: {now}")
        
    async def disconnect(self):
        """Disconnette dal server"""
        await self.client.disconnect()
        print("✅ Disconnesso dal server")

def print_help():
    """Mostra l'help del programma"""
    print("""
🌱 Simple Monitor Client - Sistema di Irrigazione OPC-UA

UTILIZZO:
    python simple_monitor_client.py [OPZIONI]

OPZIONI:
    -h, --help          Mostra questo messaggio di aiuto
    -s, --single        Esegue una lettura singola dello stato
    -c, --continuous    Monitoraggio continuo (default)
    -i INTERVAL         Intervallo di aggiornamento in secondi (default: 2)
    -u URL              URL del server OPC-UA (default: opc.tcp://localhost:48400/irrigation)

ESEMPI:
    python simple_monitor_client.py                     # Monitoraggio continuo
    python simple_monitor_client.py -s                  # Lettura singola
    python simple_monitor_client.py -c -i 5             # Monitoraggio ogni 5 secondi

CONTROLLI:
    - Ctrl+C: Esce dal monitoraggio continuo
    - Durante il monitoraggio continuo, usa simple_control_client.py in un altro terminale
    """)

async def main():
    """Funzione principale"""
    import sys
    
    # Parse argomenti semplice
    args = sys.argv[1:]
    
    if "-h" in args or "--help" in args:
        print_help()
        return
        
    # Parametri di default
    server_url = "opc.tcp://localhost:48400/irrigation"
    single_mode = "-s" in args or "--single" in args
    interval = 2
    
    # Parse URL
    if "-u" in args:
        try:
            url_index = args.index("-u")
            server_url = args[url_index + 1]
        except (ValueError, IndexError):
            print("❌ Errore: URL non specificato dopo -u")
            return
            
    # Parse interval
    if "-i" in args:
        try:
            interval_index = args.index("-i")
            interval = int(args[interval_index + 1])
        except (ValueError, IndexError):
            print("❌ Errore: Intervallo non valido dopo -i")
            return
    
    monitor = SimpleIrrigationMonitor(server_url)
    
    try:
        print("🔌 Connessione al server OPC-UA...")
        await monitor.connect()
        
        if single_mode:
            await monitor.monitor_once()
        else:
            await monitor.monitor_continuous(interval)
            
    except ConnectionError:
        print("❌ Impossibile connettersi al server OPC-UA")
        print("💡 Assicurati che il server sia in esecuzione con: python server/irrigation_server_simple.py")
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        try:
            await monitor.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())