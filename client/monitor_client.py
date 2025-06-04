#!/usr/bin/env python3
"""
Monitor client professionale per il server con ObjectTypes
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

class ProfessionalIrrigationMonitor:
    """Monitor per il server professionale con ObjectTypes"""
    
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
            print("✅ Sistema professionale di irrigazione scoperto")
            
        except Exception as e:
            print(f"❌ Errore durante la connessione: {e}")
            raise
            
    async def _discover_nodes(self):
        """Scopre tutti i nodi del sistema professionale"""
        root = self.client.get_objects_node()
        
        # Sistema di irrigazione
        irrigation_system = await root.get_child([f"{self.ns_idx}:IrrigationSystem"])
        
        # Controller → SystemState
        controller = await irrigation_system.get_child([f"{self.ns_idx}:Controller"])
        system_state = await controller.get_child([f"{self.ns_idx}:SystemState"])
        self.nodes["system_state"] = system_state
        
        # Stations folder
        stations_folder = await irrigation_system.get_child([f"{self.ns_idx}:Stations"])
        
        # Stazioni
        station_ids = ["Station1", "Station2", "Station3"]
        
        for station_id in station_ids:
            try:
                station_node = await stations_folder.get_child([f"{self.ns_idx}:{station_id}"])
                
                # StationInfo
                station_info = await station_node.get_child([f"{self.ns_idx}:StationInfo"])
                station_desc = await (await station_info.get_child([f"{self.ns_idx}:Description"])).read_value()
                station_type = await (await station_info.get_child([f"{self.ns_idx}:StationType"])).read_value()
                valve_count = await (await station_info.get_child([f"{self.ns_idx}:ValveCount"])).read_value()
                
                # Salva info stazione
                self.nodes[f"{station_id}_info"] = {
                    "description": station_desc,
                    "type": station_type,
                    "valve_count": valve_count
                }
                
                # Valvole della stazione
                for valve_num in range(1, valve_count + 1):
                    valve_id = f"Valve{valve_num}"
                    full_valve_id = f"{station_id}_{valve_id}"
                    
                    try:
                        valve_node = await station_node.get_child([f"{self.ns_idx}:{valve_id}"])
                        
                        # Description
                        description = await (await valve_node.get_child([f"{self.ns_idx}:Description"])).read_value()
                        
                        # Status
                        status_folder = await valve_node.get_child([f"{self.ns_idx}:Status"])
                        is_irrigating = await status_folder.get_child([f"{self.ns_idx}:IsIrrigating"])
                        mode = await status_folder.get_child([f"{self.ns_idx}:Mode"])
                        remaining_time = await status_folder.get_child([f"{self.ns_idx}:RemainingTime"])
                        
                        self.nodes[f"{full_valve_id}_description"] = description
                        self.nodes[f"{full_valve_id}_irrigating"] = is_irrigating
                        self.nodes[f"{full_valve_id}_mode"] = mode
                        self.nodes[f"{full_valve_id}_remaining"] = remaining_time
                        
                    except:
                        pass  # Valvola non trovata
                        
            except:
                pass  # Stazione non trovata
                
    async def read_system_status(self) -> Dict:
        """Legge lo stato completo del sistema professionale"""
        status = {}
        
        # Stato sistema
        system_on = await self.nodes["system_state"].read_value()
        status["system"] = {"on": system_on}
        
        # Stazioni
        status["stations"] = {}
        
        station_ids = ["Station1", "Station2", "Station3"]
        
        for station_id in station_ids:
            if f"{station_id}_info" in self.nodes:
                station_info = self.nodes[f"{station_id}_info"]
                
                status["stations"][station_id] = {
                    "description": station_info["description"],
                    "type": station_info["type"], 
                    "valve_count": station_info["valve_count"],
                    "valves": {}
                }
                
                # Valvole della stazione
                for valve_num in range(1, station_info["valve_count"] + 1):
                    valve_id = f"Valve{valve_num}"
                    full_valve_id = f"{station_id}_{valve_id}"
                    
                    if f"{full_valve_id}_irrigating" in self.nodes:
                        try:
                            description = await self.nodes[f"{full_valve_id}_description"].read_value()
                            is_irrigating = await self.nodes[f"{full_valve_id}_irrigating"].read_value()
                            mode = await self.nodes[f"{full_valve_id}_mode"].read_value()
                            remaining_time = await self.nodes[f"{full_valve_id}_remaining"].read_value()
                            
                            status["stations"][station_id]["valves"][valve_id] = {
                                "description": description,
                                "irrigating": is_irrigating,
                                "mode": mode,
                                "remaining_time": remaining_time
                            }
                        except:
                            pass
                    
        return status
        
    def format_status_display(self, status: Dict) -> str:
        """Formatta lo stato per la visualizzazione professionale"""
        output = []
        output.append("=" * 80)
        output.append("        🌱 SISTEMA IRRIGAZIONE PROFESSIONALE - ObjectTypes 🌱")
        output.append("=" * 80)
        
        # Stato sistema
        system_state = "🟢 ACCESO" if status["system"]["on"] else "🔴 SPENTO"
        output.append(f"🏠 Sistema: {system_state}")
        output.append("")
        
        # Architettura
        output.append("🏗️  Architettura: IrrigationSystem → Controller + Stations → StationX → ValveY")
        output.append("🔧 ObjectTypes: IrrigationSystemType, IrrigationStationType, IrrigationValveType")
        output.append("")
        
        # Stato stazioni
        for station_id, station_data in status["stations"].items():
            if not station_data["valves"]:
                continue
                
            output.append(f"📁 {station_id} - {station_data['description']}")
            output.append(f"   Tipo: {station_data['type']} ({station_data['valve_count']} valvole)")
            output.append("-" * 70)
            
            for valve_id, valve_data in station_data["valves"].items():
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
                
                output.append(f"  {icon} {color}{valve_id}: {state}{reset_color}")
                output.append(f"      📍 {valve_data['description']}")
                output.append(f"      🔧 Modalità: {valve_data['mode']}")
                
                if valve_data["irrigating"]:
                    mins, secs = divmod(valve_data["remaining_time"], 60)
                    output.append(f"      ⏱️  Tempo rimanente: {mins:02d}:{secs:02d}")
                        
                output.append("")
                
        output.append("=" * 80)
        return "\n".join(output)
        
    def clear_screen(self):
        """Pulisce lo schermo"""
        os.system('cls' if os.name == 'nt' else 'clear')
        
    async def monitor_continuous(self, interval: int = 2):
        """Monitoraggio continuo del sistema"""
        print("🌱 Avvio monitoraggio sistema irrigazione professionale...")
        print("   Struttura con ObjectTypes personalizzati")
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
                print("\n💡 Suggerimenti:")
                print("   • Usa professional_control_client.py per controllare l'irrigazione")
                print("   • Struttura: StationX_ValveY (es. Station1_Valve1)")
                print("   • ObjectTypes visibili in UAModeler sotto Types → ObjectTypes")
                
                await asyncio.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoraggio interrotto dall'utente")
            
    async def monitor_once(self):
        """Mostra lo stato una sola volta"""
        print("📊 Lettura stato sistema irrigazione professionale...")
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
🌱 Professional Monitor Client - Sistema di Irrigazione OPC-UA con ObjectTypes

UTILIZZO:
    python professional_monitor_client.py [OPZIONI]

OPZIONI:
    -h, --help          Mostra questo messaggio di aiuto
    -s, --single        Esegue una lettura singola dello stato
    -c, --continuous    Monitoraggio continuo (default)
    -i INTERVAL         Intervallo di aggiornamento in secondi (default: 2)
    -u URL              URL del server OPC-UA (default: opc.tcp://localhost:48400/irrigation)

STRUTTURA PROFESSIONALE:
    IrrigationSystem/
    ├── Controller/
    │   └── SystemState
    └── Stations/
        ├── Station1/ (IrrigationStationType)
        │   ├── StationInfo/
        │   ├── Valve1/ (IrrigationValveType)
        │   └── Valve2/ (IrrigationValveType)
        ├── Station2/ (IrrigationStationType)
        └── Station3/ (IrrigationStationType)

ESEMPI:
    python professional_monitor_client.py                     # Monitoraggio continuo
    python professional_monitor_client.py -s                  # Lettura singola
    python professional_monitor_client.py -c -i 5             # Monitoraggio ogni 5 secondi

CONTROLLI:
    - Ctrl+C: Esce dal monitoraggio continuo
    - Durante il monitoraggio, usa professional_control_client.py in un altro terminale
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
    
    monitor = ProfessionalIrrigationMonitor(server_url)
    
    try:
        print("🔌 Connessione al server OPC-UA professionale...")
        await monitor.connect()
        
        if single_mode:
            await monitor.monitor_once()
        else:
            await monitor.monitor_continuous(interval)
            
    except ConnectionError:
        print("❌ Impossibile connettersi al server OPC-UA")
        print("💡 Assicurati che il server sia in esecuzione con: python professional_irrigation_server.py")
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        try:
            await monitor.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())