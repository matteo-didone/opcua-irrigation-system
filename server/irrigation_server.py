#!/usr/bin/env python3
"""
Server OPC-UA PROFESSIONALE per Sistema di Irrigazione
Con ObjectTypes personalizzati e struttura gerarchica completa
"""

import asyncio
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from asyncua import Server, ua
from asyncua.common.node import Node

# Configurazione logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class ValveController:
    """Controlla un singolo rubinetto/valvola"""
    
    def __init__(self, valve_id: str, description: str):
        self.valve_id = valve_id
        self.description = description
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
        print(f"💧 {self.description}: Avviata irrigazione manuale per {duration_seconds}s")
        return True
        
    async def stop_irrigation(self) -> bool:
        """Ferma l'irrigazione"""
        if self.is_irrigating:
            self.is_irrigating = False
            self.remaining_time = 0
            print(f"🛑 {self.description}: Irrigazione fermata")
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
                print(f"✅ {self.description}: Irrigazione completata")

class StationController:
    """Controlla una stazione di irrigazione"""
    
    def __init__(self, station_id: str, description: str, valve_count: int):
        self.station_id = station_id
        self.description = description
        self.valve_count = valve_count
        self.station_type = "DoubleValve" if valve_count > 1 else "SingleValve"
        self.valves: Dict[str, ValveController] = {}
        
        # Crea le valvole
        for i in range(1, valve_count + 1):
            valve_id = f"Valve{i}"
            valve_description = f"{description} - Valvola {i}"
            self.valves[valve_id] = ValveController(f"{station_id}_{valve_id}", valve_description)
    
    async def update(self):
        """Aggiorna tutte le valvole della stazione"""
        for valve in self.valves.values():
            await valve.update()

class IrrigationSystem:
    """Sistema principale di irrigazione con ObjectTypes"""
    
    def __init__(self):
        self.system_on = True
        self.stations: Dict[str, StationController] = {}
        
        # Configurazione stazioni
        station_configs = [
            {"id": "Station1", "description": "Giardino Anteriore", "valves": 2},
            {"id": "Station2", "description": "Aiuole Laterali", "valves": 1},
            {"id": "Station3", "description": "Giardino Posteriore", "valves": 2}
        ]
        
        # Crea le stazioni
        for config in station_configs:
            self.stations[config["id"]] = StationController(
                config["id"], config["description"], config["valves"]
            )
        
    async def update(self):
        """Aggiorna tutto il sistema"""
        if self.system_on:
            for station in self.stations.values():
                await station.update()

class ProfessionalIrrigationServer:
    """Server OPC-UA professionale con ObjectTypes"""
    
    def __init__(self):
        self.server = Server()
        self.irrigation_system = IrrigationSystem()
        self.nodes: Dict[str, Node] = {}
        self.object_types: Dict[str, Node] = {}
        self.ns_idx = None
        
    async def init_server(self):
        """Inizializza il server"""
        await self.server.init()
        
        self.server.set_endpoint("opc.tcp://localhost:48400/irrigation")
        self.server.set_server_name("Professional Irrigation Server")
        
        namespace_uri = "http://mvlabs.it/irrigation"
        self.ns_idx = await self.server.register_namespace(namespace_uri)
        
        # Crea ObjectTypes prima dell'AddressSpace
        await self._create_object_types()
        await self._create_address_space()
        
    async def _create_object_types(self):
        """Crea gli ObjectTypes personalizzati"""
        print("🏗️  Creazione ObjectTypes personalizzati...")
        
        base_object_type = self.server.get_node(ua.ObjectIds.BaseObjectType)
        
        # =============================================================================
        # 1. IrrigationValveType
        # =============================================================================
        valve_type = await base_object_type.add_object_type(self.ns_idx, "IrrigationValveType")
        
        # Descrizione valvola
        await valve_type.add_variable(self.ns_idx, "Description", "", ua.VariantType.String)
        
        # Status folder
        status_folder = await valve_type.add_object(self.ns_idx, "Status")
        await status_folder.add_variable(self.ns_idx, "IsIrrigating", False, ua.VariantType.Boolean)
        await status_folder.add_variable(self.ns_idx, "Mode", "Off", ua.VariantType.String)
        await status_folder.add_variable(self.ns_idx, "RemainingTime", 0, ua.VariantType.Int32)
        await status_folder.add_variable(self.ns_idx, "NextScheduledStart", None, ua.VariantType.DateTime)
        
        # Commands folder
        commands_folder = await valve_type.add_object(self.ns_idx, "Commands")
        duration_var = await commands_folder.add_variable(self.ns_idx, "CommandDuration", 0, ua.VariantType.Int32)
        start_var = await commands_folder.add_variable(self.ns_idx, "CommandStart", False, ua.VariantType.Boolean)
        stop_var = await commands_folder.add_variable(self.ns_idx, "CommandStop", False, ua.VariantType.Boolean)
        
        await duration_var.set_writable()
        await start_var.set_writable()
        await stop_var.set_writable()
        
        self.object_types["valve_type"] = valve_type
        
        # =============================================================================
        # 2. IrrigationStationType
        # =============================================================================
        station_type = await base_object_type.add_object_type(self.ns_idx, "IrrigationStationType")
        
        # StationInfo
        station_info = await station_type.add_object(self.ns_idx, "StationInfo")
        await station_info.add_variable(self.ns_idx, "StationId", "", ua.VariantType.String)
        await station_info.add_variable(self.ns_idx, "Description", "", ua.VariantType.String)
        await station_info.add_variable(self.ns_idx, "StationType", "", ua.VariantType.String)
        await station_info.add_variable(self.ns_idx, "ValveCount", 0, ua.VariantType.Int32)
        
        self.object_types["station_type"] = station_type
        
        # =============================================================================
        # 3. IrrigationSystemType
        # =============================================================================
        system_type = await base_object_type.add_object_type(self.ns_idx, "IrrigationSystemType")
        
        # Controller
        controller_folder = await system_type.add_object(self.ns_idx, "Controller")
        system_state_var = await controller_folder.add_variable(self.ns_idx, "SystemState", True, ua.VariantType.Boolean)
        await system_state_var.set_writable()
        
        # Stations folder
        await system_type.add_object(self.ns_idx, "Stations")
        
        self.object_types["system_type"] = system_type
        
        print("✅ ObjectTypes creati: IrrigationSystemType, IrrigationStationType, IrrigationValveType")
        
    async def _create_address_space(self):
        """Crea l'AddressSpace usando gli ObjectTypes"""
        print("🏗️  Creazione AddressSpace professionale...")
        
        objects = self.server.get_objects_node()
        
        # Root del sistema usando il tipo personalizzato
        irrigation_root = await objects.add_object(self.ns_idx, "IrrigationSystem", 
                                                 objecttype=self.object_types["system_type"])
        
        # Controller
        controller = await irrigation_root.add_object(self.ns_idx, "Controller")
        system_state = await controller.add_variable(self.ns_idx, "SystemState", True, ua.VariantType.Boolean)
        await system_state.set_writable()
        self.nodes["system_state"] = system_state
        
        # Stations folder
        stations_folder = await irrigation_root.add_object(self.ns_idx, "Stations")
        
        # Crea stazioni usando ObjectTypes
        for station_id, station_controller in self.irrigation_system.stations.items():
            station_node = await stations_folder.add_object(self.ns_idx, station_id,
                                                          objecttype=self.object_types["station_type"])
            
            # StationInfo
            station_info = await station_node.add_object(self.ns_idx, "StationInfo")
            station_id_var = await station_info.add_variable(self.ns_idx, "StationId", station_id, ua.VariantType.String)
            station_desc_var = await station_info.add_variable(self.ns_idx, "Description", station_controller.description, ua.VariantType.String)
            station_type_var = await station_info.add_variable(self.ns_idx, "StationType", station_controller.station_type, ua.VariantType.String)
            valve_count_var = await station_info.add_variable(self.ns_idx, "ValveCount", station_controller.valve_count, ua.VariantType.Int32)
            
            # Crea valvole usando ObjectTypes
            for valve_id, valve_controller in station_controller.valves.items():
                valve_node = await station_node.add_object(self.ns_idx, valve_id,
                                                         objecttype=self.object_types["valve_type"])
                
                # Description
                desc_var = await valve_node.add_variable(self.ns_idx, "Description", valve_controller.description, ua.VariantType.String)
                
                # Status folder
                status_folder = await valve_node.add_object(self.ns_idx, "Status")
                is_irrigating = await status_folder.add_variable(self.ns_idx, "IsIrrigating", False, ua.VariantType.Boolean)
                mode = await status_folder.add_variable(self.ns_idx, "Mode", "Off", ua.VariantType.String)
                remaining_time = await status_folder.add_variable(self.ns_idx, "RemainingTime", 0, ua.VariantType.Int32)
                next_scheduled = await status_folder.add_variable(self.ns_idx, "NextScheduledStart", None, ua.VariantType.DateTime)
                
                # Commands folder
                commands_folder = await valve_node.add_object(self.ns_idx, "Commands")
                duration_cmd = await commands_folder.add_variable(self.ns_idx, "CommandDuration", 0, ua.VariantType.Int32)
                start_cmd = await commands_folder.add_variable(self.ns_idx, "CommandStart", False, ua.VariantType.Boolean)
                stop_cmd = await commands_folder.add_variable(self.ns_idx, "CommandStop", False, ua.VariantType.Boolean)
                
                await duration_cmd.set_writable()
                await start_cmd.set_writable()
                await stop_cmd.set_writable()
                
                # Salva riferimenti per aggiornamenti
                full_valve_id = f"{station_id}_{valve_id}"
                self.nodes[f"{full_valve_id}_irrigating"] = is_irrigating
                self.nodes[f"{full_valve_id}_mode"] = mode
                self.nodes[f"{full_valve_id}_remaining"] = remaining_time
                self.nodes[f"{full_valve_id}_duration_cmd"] = duration_cmd
                self.nodes[f"{full_valve_id}_start_cmd"] = start_cmd
                self.nodes[f"{full_valve_id}_stop_cmd"] = stop_cmd
        
        print("✅ AddressSpace professionale creato")
    
    async def update_nodes(self):
        """Aggiorna i nodi OPC-UA"""
        # Aggiorna sistema
        await self.irrigation_system.update()
        
        # Leggi stato sistema
        system_on = await self.nodes["system_state"].read_value()
        self.irrigation_system.system_on = system_on
        
        # Aggiorna ogni valvola
        for station_id, station in self.irrigation_system.stations.items():
            for valve_id, valve in station.valves.items():
                full_valve_id = f"{station_id}_{valve_id}"
                
                # Leggi comandi 
                duration = await self.nodes[f"{full_valve_id}_duration_cmd"].read_value()
                start = await self.nodes[f"{full_valve_id}_start_cmd"].read_value()
                stop = await self.nodes[f"{full_valve_id}_stop_cmd"].read_value()
                
                # Imposta comandi nella valvola (con conversioni sicure)
                valve.command_duration = int(duration) if duration else 0
                valve.command_start = start
                valve.command_stop = stop
                
                # Aggiorna status (con tipi OPC-UA corretti)
                await self.nodes[f"{full_valve_id}_irrigating"].write_value(valve.is_irrigating)
                await self.nodes[f"{full_valve_id}_mode"].write_value(valve.mode)
                await self.nodes[f"{full_valve_id}_remaining"].write_value(ua.Variant(valve.remaining_time, ua.VariantType.Int32))
                
                # Reset comandi se eseguiti
                if start:
                    await self.nodes[f"{full_valve_id}_start_cmd"].write_value(False)
                if stop:
                    await self.nodes[f"{full_valve_id}_stop_cmd"].write_value(False)
    
    async def export_addressspace(self, filename="irrigation_professional_nodeset.xml"):
        """Esporta l'AddressSpace corrente come NodeSet XML"""
        try:
            print(f"📤 Esportazione AddressSpace professionale in {filename}...")
            
            # Esporta solo il namespace personalizzato
            await self.server.export_xml([self.ns_idx], filename)
            
            print(f"✅ AddressSpace esportato in: {filename}")
            print(f"📁 Percorso completo: {os.path.abspath(filename)}")
            print("\n📋 Per importare in UAModeler:")
            print("   File → Import → NodeSet → Seleziona il file XML")
            
            return True
            
        except Exception as e:
            print(f"❌ Errore durante l'esportazione: {e}")
            return False
    
    async def start_server(self):
        """Avvia il server"""
        await self.server.start()
        print("🌱 Server OPC-UA Professionale avviato su opc.tcp://localhost:48400/irrigation")
        print("📍 Stazioni e valvole disponibili:")
        
        for station_id, station in self.irrigation_system.stations.items():
            print(f"   📁 {station_id} - {station.description} ({station.station_type})")
            for valve_id, valve in station.valves.items():
                print(f"      💧 {valve_id}: {valve.description}")
        
        print("\n🚀 Struttura con ObjectTypes personalizzati:")
        print("   • IrrigationSystemType → IrrigationSystem (istanza)")
        print("   • IrrigationStationType → Station1, Station2, Station3 (istanze)")
        print("   • IrrigationValveType → Valve1, Valve2, etc. (istanze)")
        print("\n💡 Premi 'e' + INVIO per esportare AddressSpace in XML")
        print("   Premi 'q' + INVIO per uscire")
        print("")
        
        try:
            # Loop principale con comandi
            import threading
            
            def input_handler():
                while True:
                    try:
                        cmd = input().strip().lower()
                        if cmd == 'q':
                            print("🛑 Uscita...")
                            os._exit(0)
                        elif cmd == 'e':
                            # Esporta in thread separato
                            async def export():
                                await self.export_addressspace()
                            
                            # Programma l'export nel loop asincrono
                            asyncio.create_task(export())
                            print("📤 Export avviato...")
                            
                    except EOFError:
                        break
                    except KeyboardInterrupt:
                        break
            
            # Avvia input handler in thread separato
            input_thread = threading.Thread(target=input_handler, daemon=True)
            input_thread.start()
            
            # Loop principale server
            while True:
                await self.update_nodes()
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Arresto server...")
        finally:
            await self.server.stop()

async def main():
    """Funzione principale"""
    print("🌱 Server OPC-UA Professionale - Sistema di Irrigazione")
    print("=" * 60)
    server = ProfessionalIrrigationServer()
    await server.init_server()
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())