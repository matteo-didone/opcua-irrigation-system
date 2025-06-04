#!/usr/bin/env python3
"""
Server OPC-UA SEMPLIFICATO per Sistema di Irrigazione
Usa solo variabili writable invece di metodi per evitare problemi
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from asyncua import Server, ua
from asyncua.common.node import Node

# Configurazione logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class ValveController:
    """Controlla un singolo rubinetto/valvola"""
    
    def __init__(self, valve_id: str):
        self.valve_id = valve_id
        self.is_irrigating = False
        self.mode = "Off"
        self.remaining_time = 0
        self.next_scheduled_start: Optional[datetime] = None
        self.start_time: Optional[datetime] = None
        self.duration = 0
        
        # Comandi tramite variabili
        self.command_duration = 0
        self.command_start = False
        self.command_stop = False
        
    async def process_commands(self):
        """Processa i comandi ricevuti tramite variabili"""
        # Comando start
        if self.command_start and self.command_duration > 0:
            await self.start_manual_irrigation(self.command_duration)
            self.command_start = False
            self.command_duration = 0
            
        # Comando stop
        if self.command_stop:
            await self.stop_irrigation()
            self.command_stop = False
        
    async def start_manual_irrigation(self, duration_seconds: int) -> bool:
        """Avvia irrigazione manuale"""
        if self.is_irrigating:
            return False
            
        self.mode = "Manual"
        self.is_irrigating = True
        self.remaining_time = duration_seconds
        self.duration = duration_seconds
        self.start_time = datetime.now()
        print(f"💧 Valvola {self.valve_id}: Avviata irrigazione manuale per {duration_seconds}s")
        return True
        
    async def stop_irrigation(self) -> bool:
        """Ferma l'irrigazione"""
        if self.is_irrigating:
            self.is_irrigating = False
            self.remaining_time = 0
            print(f"🛑 Valvola {self.valve_id}: Irrigazione fermata")
        self.mode = "Off"
        self.next_scheduled_start = None
        return True
        
    async def update(self):
        """Aggiorna lo stato della valvola"""
        # Processa comandi
        await self.process_commands()
        
        # Aggiorna timer
        if self.is_irrigating and self.start_time:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            self.remaining_time = max(0, self.duration - int(elapsed))
            
            if self.remaining_time <= 0:
                self.is_irrigating = False
                self.remaining_time = 0
                self.mode = "Off"
                print(f"✅ Valvola {self.valve_id}: Irrigazione completata")

class IrrigationSystem:
    """Sistema principale di irrigazione"""
    
    def __init__(self):
        self.system_on = True
        self.valves: Dict[str, ValveController] = {}
        
        # Crea le valvole
        for station in ["Station1", "Station2", "Station3"]:
            valve_count = 2 if station != "Station2" else 1
            for i in range(valve_count):
                valve_id = f"{station}_Valve{i+1}"
                self.valves[valve_id] = ValveController(valve_id)
        
    async def update(self):
        """Aggiorna tutto il sistema"""
        if self.system_on:
            for valve in self.valves.values():
                await valve.update()

class SimpleIrrigationServer:
    """Server OPC-UA semplificato"""
    
    def __init__(self):
        self.server = Server()
        self.irrigation_system = IrrigationSystem()
        self.nodes: Dict[str, Node] = {}
        
    async def init_server(self):
        """Inizializza il server"""
        await self.server.init()
        
        self.server.set_endpoint("opc.tcp://localhost:48400/irrigation")
        self.server.set_server_name("Simple Irrigation Server")
        
        namespace_uri = "http://mvlabs.it/irrigation"
        self.ns_idx = await self.server.register_namespace(namespace_uri)
        
        await self._create_address_space()
        
    async def _create_address_space(self):
        """Crea l'AddressSpace semplificato"""
        objects = self.server.get_objects_node()
        
        # Root del sistema
        irrigation_root = await objects.add_object(self.ns_idx, "IrrigationSystem")
        
        # Sistema on/off
        system_state = await irrigation_root.add_variable(self.ns_idx, "SystemState", True)
        await system_state.set_writable()
        self.nodes["system_state"] = system_state
        
        # Crea nodi per ogni valvola
        for valve_id, valve in self.irrigation_system.valves.items():
            valve_node = await irrigation_root.add_object(self.ns_idx, valve_id)
            
            # Status (read-only)
            is_irrigating = await valve_node.add_variable(self.ns_idx, "IsIrrigating", False)
            mode = await valve_node.add_variable(self.ns_idx, "Mode", "Off")
            remaining_time = await valve_node.add_variable(self.ns_idx, "RemainingTime", 0)
            
            # Commands (writable)
            duration_cmd = await valve_node.add_variable(self.ns_idx, "CommandDuration", 0)
            start_cmd = await valve_node.add_variable(self.ns_idx, "CommandStart", False)
            stop_cmd = await valve_node.add_variable(self.ns_idx, "CommandStop", False)
            
            await duration_cmd.set_writable()
            await start_cmd.set_writable()
            await stop_cmd.set_writable()
            
            # Salva riferimenti
            self.nodes[f"{valve_id}_irrigating"] = is_irrigating
            self.nodes[f"{valve_id}_mode"] = mode
            self.nodes[f"{valve_id}_remaining"] = remaining_time
            self.nodes[f"{valve_id}_duration_cmd"] = duration_cmd
            self.nodes[f"{valve_id}_start_cmd"] = start_cmd
            self.nodes[f"{valve_id}_stop_cmd"] = stop_cmd
    
    async def update_nodes(self):
        """Aggiorna i nodi OPC-UA"""
        # Aggiorna sistema
        await self.irrigation_system.update()
        
        # Leggi stato sistema
        system_on = await self.nodes["system_state"].read_value()
        self.irrigation_system.system_on = system_on
        
        # Aggiorna ogni valvola
        for valve_id, valve in self.irrigation_system.valves.items():
            # Leggi comandi
            duration = await self.nodes[f"{valve_id}_duration_cmd"].read_value()
            start = await self.nodes[f"{valve_id}_start_cmd"].read_value()
            stop = await self.nodes[f"{valve_id}_stop_cmd"].read_value()
            
            # Imposta comandi nella valvola
            valve.command_duration = duration
            valve.command_start = start
            valve.command_stop = stop
            
            # Aggiorna status
            await self.nodes[f"{valve_id}_irrigating"].write_value(valve.is_irrigating)
            await self.nodes[f"{valve_id}_mode"].write_value(valve.mode)
            await self.nodes[f"{valve_id}_remaining"].write_value(valve.remaining_time)
            
            # Reset comandi se eseguiti
            if start:
                await self.nodes[f"{valve_id}_start_cmd"].write_value(False)
            if stop:
                await self.nodes[f"{valve_id}_stop_cmd"].write_value(False)
    
    async def start_server(self):
        """Avvia il server"""
        await self.server.start()
        print("🌱 Server OPC-UA Semplificato avviato su opc.tcp://localhost:48400/irrigation")
        print("📍 Valvole disponibili:")
        for valve_id in self.irrigation_system.valves.keys():
            print(f"   - {valve_id}")
        print("\n🚀 Usa le variabili CommandDuration, CommandStart, CommandStop per controllare")
        print("   Esempio: Imposta CommandDuration=30, poi CommandStart=True")
        print("")
        
        try:
            while True:
                await self.update_nodes()
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Arresto server...")
        finally:
            await self.server.stop()

async def main():
    """Funzione principale"""
    server = SimpleIrrigationServer()
    await server.init_server()
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())