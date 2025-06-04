#!/usr/bin/env python3
"""
Client semplificato che usa variabili invece di metodi OPC-UA
"""

import asyncio
import sys
from asyncua import Client

class SimpleIrrigationController:
    """Client semplificato per controllo tramite variabili"""
    
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
        print("✅ Sistema scoperto")
        
    async def _discover_nodes(self):
        """Scopre i nodi del sistema"""
        root = self.client.get_objects_node()
        irrigation_system = await root.get_child([f"{self.ns_idx}:IrrigationSystem"])
        
        # Sistema state
        system_state = await irrigation_system.get_child([f"{self.ns_idx}:SystemState"])
        self.nodes["system_state"] = system_state
        
        # Valvole
        valve_ids = ["Station1_Valve1", "Station1_Valve2", "Station2_Valve1", "Station3_Valve1", "Station3_Valve2"]
        
        for valve_id in valve_ids:
            try:
                valve_node = await irrigation_system.get_child([f"{self.ns_idx}:{valve_id}"])
                
                # Status
                is_irrigating = await valve_node.get_child([f"{self.ns_idx}:IsIrrigating"])
                mode = await valve_node.get_child([f"{self.ns_idx}:Mode"])
                remaining_time = await valve_node.get_child([f"{self.ns_idx}:RemainingTime"])
                
                # Commands
                duration_cmd = await valve_node.get_child([f"{self.ns_idx}:CommandDuration"])
                start_cmd = await valve_node.get_child([f"{self.ns_idx}:CommandStart"])
                stop_cmd = await valve_node.get_child([f"{self.ns_idx}:CommandStop"])
                
                self.nodes[valve_id] = {
                    "irrigating": is_irrigating,
                    "mode": mode,
                    "remaining": remaining_time,
                    "duration_cmd": duration_cmd,
                    "start_cmd": start_cmd,
                    "stop_cmd": stop_cmd
                }
            except:
                pass  # Valvola non trovata
                
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
            
            # Imposta durata e comando start
            await valve["duration_cmd"].write_value(duration)
            await valve["start_cmd"].write_value(True)
            
            mins, secs = divmod(duration, 60)
            print(f"✅ Comando inviato: {valve_id} per {mins:02d}:{secs:02d}")
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
            print(f"✅ Stop inviato: {valve_id}")
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
            "remaining": remaining
        }
        
    def list_valves(self):
        """Lista valvole"""
        print("\n💧 Valvole disponibili:")
        descriptions = {
            "Station1_Valve1": "Giardino Anteriore - Valvola 1",
            "Station1_Valve2": "Giardino Anteriore - Valvola 2", 
            "Station2_Valve1": "Aiuole Laterali - Valvola 1",
            "Station3_Valve1": "Giardino Posteriore - Valvola 1",
            "Station3_Valve2": "Giardino Posteriore - Valvola 2"
        }
        
        for valve_id in self.nodes:
            if valve_id != "system_state":
                desc = descriptions.get(valve_id, valve_id)
                print(f"  • {valve_id}: {desc}")
        print()
        
    async def disconnect(self):
        """Disconnette"""
        await self.client.disconnect()
        print("✅ Disconnesso")

async def interactive_mode(controller):
    """Modalità interattiva semplificata"""
    print("🌱 Controller Semplificato - Sistema di Irrigazione")
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
                print("  list                      - Lista valvole")
                print("  on/off                    - Accendi/spegni sistema")
                print("  start <valvola> <durata>  - Avvia irrigazione")
                print("  stop <valvola>            - Ferma irrigazione")
                print("  exit                      - Esci")
                print("\nEsempio: start Station1_Valve1 60")
                
            elif cmd == "status":
                system_on = await controller.get_system_state()
                status = "🟢 ACCESO" if system_on else "🔴 SPENTO"
                print(f"Sistema: {status}")
                
            elif cmd == "list":
                controller.list_valves()
                
            elif cmd == "on":
                await controller.set_system_state(True)
                
            elif cmd == "off":
                await controller.set_system_state(False)
                
            elif cmd == "start":
                if len(parts) != 3:
                    print("❌ Uso: start <valvola> <durata_secondi>")
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
    controller = SimpleIrrigationController()
    
    try:
        print("🔌 Connessione al server semplificato...")
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