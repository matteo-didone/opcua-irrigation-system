#!/usr/bin/env python3
"""
Client professionale per il server con ObjectTypes
Compatibile con la struttura gerarchica: Stations/StationX/ValveY
"""

import asyncio
import sys
from asyncua import Client, ua

class ProfessionalIrrigationController:
    """Client professionale per la struttura con ObjectTypes"""
    
    def __init__(self, server_url: str = "opc.tcp://localhost:48400/irrigation"):
        self.server_url = server_url
        self.client = Client(server_url)
        self.ns_idx = None
        self.nodes = {}
        
    async def connect(self):
        """Connette al server"""
        await self.client.connect()
        print(f"✅ Connesso al server: {self.server_url}")
        
        # Trova namespace
        namespaces = await self.client.get_namespace_array()
        for i, ns in enumerate(namespaces):
            if "mvlabs.it/irrigation" in ns:
                self.ns_idx = i
                break
                
        # Scopri nodi
        await self._discover_nodes()
        print("✅ Sistema professionale scoperto")
        
    async def _discover_nodes(self):
        """Scopre i nodi del sistema professionale"""
        root = self.client.get_objects_node()
        irrigation_system = await root.get_child([f"{self.ns_idx}:IrrigationSystem"])
        
        # Controller → SystemState
        controller = await irrigation_system.get_child([f"{self.ns_idx}:Controller"])
        system_state = await controller.get_child([f"{self.ns_idx}:SystemState"])
        self.nodes["system_state"] = system_state
        
        # Stations folder
        stations_folder = await irrigation_system.get_child([f"{self.ns_idx}:Stations"])
        
        # Stazioni e valvole
        station_ids = ["Station1", "Station2", "Station3"]
        
        for station_id in station_ids:
            try:
                station_node = await stations_folder.get_child([f"{self.ns_idx}:{station_id}"])
                
                # StationInfo
                station_info = await station_node.get_child([f"{self.ns_idx}:StationInfo"])
                valve_count_node = await station_info.get_child([f"{self.ns_idx}:ValveCount"])
                valve_count = await valve_count_node.read_value()
                
                # Valvole della stazione
                for valve_num in range(1, valve_count + 1):
                    valve_id = f"Valve{valve_num}"
                    full_valve_id = f"{station_id}_{valve_id}"
                    
                    try:
                        valve_node = await station_node.get_child([f"{self.ns_idx}:{valve_id}"])
                        
                        # Status
                        status_folder = await valve_node.get_child([f"{self.ns_idx}:Status"])
                        is_irrigating = await status_folder.get_child([f"{self.ns_idx}:IsIrrigating"])
                        mode = await status_folder.get_child([f"{self.ns_idx}:Mode"])
                        remaining_time = await status_folder.get_child([f"{self.ns_idx}:RemainingTime"])
                        
                        # Commands
                        commands_folder = await valve_node.get_child([f"{self.ns_idx}:Commands"])
                        duration_cmd = await commands_folder.get_child([f"{self.ns_idx}:CommandDuration"])
                        start_cmd = await commands_folder.get_child([f"{self.ns_idx}:CommandStart"])
                        stop_cmd = await commands_folder.get_child([f"{self.ns_idx}:CommandStop"])
                        
                        # Description
                        description = await valve_node.get_child([f"{self.ns_idx}:Description"])
                        desc_text = await description.read_value()
                        
                        self.nodes[full_valve_id] = {
                            "description": desc_text,
                            "irrigating": is_irrigating,
                            "mode": mode,
                            "remaining": remaining_time,
                            "duration_cmd": duration_cmd,
                            "start_cmd": start_cmd,
                            "stop_cmd": stop_cmd,
                            "station": station_id,
                            "valve": valve_id
                        }
                    except:
                        pass  # Valvola non trovata
                        
            except:
                pass  # Stazione non trovata
                
    async def get_system_state(self) -> bool:
        """Stato del sistema"""
        return await self.nodes["system_state"].read_value()
        
    async def set_system_state(self, on: bool):
        """Imposta stato sistema"""
        await self.nodes["system_state"].write_value(on)
        status = "🟢 ACCESO" if on else "🔴 SPENTO"
        print(f"Sistema: {status}")
        
    async def start_irrigation(self, valve_id: str, duration: int) -> bool:
        """Avvia irrigazione tramite variabili"""
        if valve_id not in self.nodes:
            print(f"❌ Valvola {valve_id} non trovata")
            return False
            
        try:
            valve = self.nodes[valve_id]
            
            # Imposta durata e comando start (con tipi OPC-UA corretti)
            await valve["duration_cmd"].write_value(ua.Variant(duration, ua.VariantType.Int32))
            await valve["start_cmd"].write_value(True)
            
            mins, secs = divmod(duration, 60)
            print(f"✅ Comando inviato: {valve['description']} per {mins:02d}:{secs:02d}")
            return True
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            return False
            
    async def stop_irrigation(self, valve_id: str) -> bool:
        """Ferma irrigazione"""
        if valve_id not in self.nodes:
            print(f"❌ Valvola {valve_id} non trovata")
            return False
            
        try:
            valve = self.nodes[valve_id]
            await valve["stop_cmd"].write_value(True)
            print(f"✅ Stop inviato: {valve['description']}")
            return True
            
        except Exception as e:
            print(f"❌ Errore: {e}")
            return False
            
    async def get_valve_status(self, valve_id: str):
        """Stato valvola"""
        if valve_id not in self.nodes:
            return None
            
        valve = self.nodes[valve_id]
        irrigating = await valve["irrigating"].read_value()
        mode = await valve["mode"].read_value()
        remaining = await valve["remaining"].read_value()
        
        return {
            "irrigating": irrigating,
            "mode": mode,
            "remaining": remaining,
            "description": valve["description"]
        }
        
    def list_valves(self):
        """Lista valvole con struttura gerarchica"""
        print("\n💧 Stazioni e valvole disponibili:")
        
        # Raggruppa per stazione
        stations = {}
        for valve_id, valve_data in self.nodes.items():
            if valve_id != "system_state":
                station = valve_data["station"]
                if station not in stations:
                    stations[station] = []
                stations[station].append((valve_id, valve_data))
        
        # Mostra struttura gerarchica
        for station_id in sorted(stations.keys()):
            valves = stations[station_id]
            valve_count = len(valves)
            station_type = "DoubleValve" if valve_count > 1 else "SingleValve"
            
            print(f"\n  📁 {station_id} ({station_type} - {valve_count} valvole):")
            for valve_id, valve_data in sorted(valves):
                print(f"    💧 {valve_id}: {valve_data['description']}")
        print()
        
    async def disconnect(self):
        """Disconnette"""
        await self.client.disconnect()
        print("✅ Disconnesso")

async def interactive_mode(controller):
    """Modalità interattiva professionale"""
    print("🌱 Controller Professionale - Sistema di Irrigazione con ObjectTypes")
    print("   Struttura: IrrigationSystem/Controller + Stations/StationX/ValveY")
    print("   Comandi: help, status, list, on, off, start <valvola> <durata>, stop <valvola>, exit")
    print()
    
    while True:
        try:
            command = input("🌿 > ").strip()
            if not command:
                continue
                
            parts = command.split()
            cmd = parts[0].lower()
            
            if cmd == "exit":
                break
            elif cmd == "help":
                print("Comandi:")
                print("  status                    - Stato sistema")
                print("  list                      - Lista stazioni e valvole")
                print("  on/off                    - Accendi/spegni sistema")
                print("  start <valvola> <durata>  - Avvia irrigazione")
                print("  stop <valvola>            - Ferma irrigazione")
                print("  exit                      - Esci")
                print("\nEsempio: start Station1_Valve1 60")
                print("Formato valvola: StationX_ValveY (es. Station1_Valve1)")
                
            elif cmd == "status":
                system_on = await controller.get_system_state()
                status = "🟢 ACCESO" if system_on else "🔴 SPENTO"
                print(f"Sistema: {status}")
                
                # Mostra anche stato valvole attive
                active_valves = []
                for valve_id in controller.nodes:
                    if valve_id != "system_state":
                        valve_status = await controller.get_valve_status(valve_id)
                        if valve_status and valve_status["irrigating"]:
                            remaining = valve_status["remaining"]
                            mins, secs = divmod(remaining, 60)
                            active_valves.append(f"{valve_status['description']} ({mins:02d}:{secs:02d})")
                
                if active_valves:
                    print("💧 Valvole in irrigazione:")
                    for valve_info in active_valves:
                        print(f"   • {valve_info}")
                else:
                    print("⭕ Nessuna valvola in irrigazione")
                
            elif cmd == "list":
                controller.list_valves()
                
            elif cmd == "on":
                await controller.set_system_state(True)
                
            elif cmd == "off":
                await controller.set_system_state(False)
                
            elif cmd == "start":
                if len(parts) != 3:
                    print("❌ Uso: start <valvola> <durata_secondi>")
                    print("   Esempio: start Station1_Valve1 60")
                    continue
                valve_id, duration_str = parts[1], parts[2]
                try:
                    duration = int(duration_str)
                    await controller.start_irrigation(valve_id, duration)
                except ValueError:
                    print("❌ Durata deve essere un numero")
                    
            elif cmd == "stop":
                if len(parts) != 2:
                    print("❌ Uso: stop <valvola>")
                    print("   Esempio: stop Station1_Valve1")
                    continue
                valve_id = parts[1]
                await controller.stop_irrigation(valve_id)
                
            else:
                print(f"❌ Comando '{cmd}' non riconosciuto")
                
        except KeyboardInterrupt:
            print("\n🛑 Uscita")
            break
        except Exception as e:
            print(f"❌ Errore: {e}")

async def main():
    """Main"""
    controller = ProfessionalIrrigationController()
    
    try:
        print("🔌 Connessione al server professionale...")
        await controller.connect()
        await interactive_mode(controller)
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        try:
            await controller.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())