#!/usr/bin/env python3
"""
🌱 Export NodeSet PROFESSIONALE con ObjectTypes personalizzati
SOLO per UAModeler - Server e client rimangono invariati
"""

import asyncio
import os
from asyncua import Server, ua
from asyncua.common.node import Node

async def create_custom_object_types(server, ns_idx):
    """Crea gli ObjectTypes personalizzati per il sistema di irrigazione"""
    
    # Ottieni il nodo BaseObjectType
    base_object_type = server.get_node(ua.ObjectIds.BaseObjectType)
    
    print("🏗️  Creazione ObjectTypes personalizzati...")
    
    # =============================================================================
    # 1. IrrigationValveType - Tipo personalizzato per le valvole
    # =============================================================================
    irrigation_valve_type = await base_object_type.add_object_type(ns_idx, "IrrigationValveType")
    
    # Descrizione del tipo (rimuoviamo set_description non supportato)
    
    # Status folder nel tipo
    status_folder = await irrigation_valve_type.add_object(ns_idx, "Status")
    await status_folder.add_variable(ns_idx, "IsIrrigating", False, ua.VariantType.Boolean)
    await status_folder.add_variable(ns_idx, "Mode", "Off", ua.VariantType.String)
    await status_folder.add_variable(ns_idx, "RemainingTime", 0, ua.VariantType.Int32)
    await status_folder.add_variable(ns_idx, "NextScheduledStart", None, ua.VariantType.DateTime)
    
    # Commands folder nel tipo
    commands_folder = await irrigation_valve_type.add_object(ns_idx, "Commands")
    duration_var = await commands_folder.add_variable(ns_idx, "CommandDuration", 0, ua.VariantType.Int32)
    start_var = await commands_folder.add_variable(ns_idx, "CommandStart", False, ua.VariantType.Boolean)
    stop_var = await commands_folder.add_variable(ns_idx, "CommandStop", False, ua.VariantType.Boolean)
    
    # Rendi scrivibili i comandi nel tipo
    await duration_var.set_writable()
    await start_var.set_writable()
    await stop_var.set_writable()
    
    # Info valvola nel tipo
    await irrigation_valve_type.add_variable(ns_idx, "Description", "", ua.VariantType.String)
    
    # =============================================================================
    # 2. IrrigationStationType - Tipo personalizzato per le stazioni
    # =============================================================================
    irrigation_station_type = await base_object_type.add_object_type(ns_idx, "IrrigationStationType")
    
    # StationInfo nel tipo
    station_info = await irrigation_station_type.add_object(ns_idx, "StationInfo")
    await station_info.add_variable(ns_idx, "StationId", "", ua.VariantType.String)
    await station_info.add_variable(ns_idx, "StationType", "", ua.VariantType.String)
    await station_info.add_variable(ns_idx, "ValveCount", 0, ua.VariantType.Int32)
    await station_info.add_variable(ns_idx, "Location", "", ua.VariantType.String)
    
    # =============================================================================
    # 3. IrrigationSystemType - Tipo personalizzato per il sistema
    # =============================================================================
    irrigation_system_type = await base_object_type.add_object_type(ns_idx, "IrrigationSystemType")
    
    # Controller nel tipo sistema
    controller_folder = await irrigation_system_type.add_object(ns_idx, "Controller")
    system_state_var = await controller_folder.add_variable(ns_idx, "SystemState", True, ua.VariantType.Boolean)
    await system_state_var.set_writable()
    
    # Stations folder nel tipo sistema
    stations_folder = await irrigation_system_type.add_object(ns_idx, "Stations")
    
    print(f"✅ ObjectTypes creati:")
    print(f"   • IrrigationValveType")
    print(f"   • IrrigationStationType") 
    print(f"   • IrrigationSystemType")
    
    return {
        "valve_type": irrigation_valve_type,
        "station_type": irrigation_station_type,
        "system_type": irrigation_system_type
    }

async def create_professional_addressspace(server, ns_idx, object_types):
    """Crea l'AddressSpace usando gli ObjectTypes personalizzati"""
    
    objects = server.get_objects_node()
    
    print("🏗️  Creazione AddressSpace con ObjectTypes...")
    
    # Root del sistema usando il tipo personalizzato
    irrigation_system = await objects.add_object(ns_idx, "IrrigationSystem", 
                                                objecttype=object_types["system_type"])
    
    # Crea manualmente la struttura (gli ObjectTypes definiscono il template, ma le istanze vanno create)
    controller = await irrigation_system.add_object(ns_idx, "Controller")
    system_state = await controller.add_variable(ns_idx, "SystemState", True, ua.VariantType.Boolean)
    await system_state.set_writable()
    
    stations_folder = await irrigation_system.add_object(ns_idx, "Stations")
    
    # Lista per tenere traccia di tutti i nodi
    created_nodes = [irrigation_system, controller, system_state, stations_folder]
    
    # Configurazione stazioni
    station_configs = [
        {"id": "Station1", "location": "Giardino Anteriore", "valves": 2, "type": "DoubleValve"},
        {"id": "Station2", "location": "Aiuole Laterali", "valves": 1, "type": "SingleValve"},
        {"id": "Station3", "location": "Giardino Posteriore", "valves": 2, "type": "DoubleValve"}
    ]
    
    # Crea stazioni usando il tipo personalizzato
    for config in station_configs:
        station = await stations_folder.add_object(ns_idx, config["id"], 
                                                 objecttype=object_types["station_type"])
        created_nodes.append(station)
        
        # Crea manualmente StationInfo
        station_info = await station.add_object(ns_idx, "StationInfo")
        station_id_var = await station_info.add_variable(ns_idx, "StationId", config["id"], ua.VariantType.String)
        station_type_var = await station_info.add_variable(ns_idx, "StationType", config["type"], ua.VariantType.String)
        valve_count_var = await station_info.add_variable(ns_idx, "ValveCount", config["valves"], ua.VariantType.Int32)
        location_var = await station_info.add_variable(ns_idx, "Location", config["location"], ua.VariantType.String)
        
        created_nodes.extend([station_info, station_id_var, station_type_var, valve_count_var, location_var])
        
        # Crea valvole usando il tipo personalizzato
        for valve_num in range(1, config["valves"] + 1):
            valve_name = f"Valve{valve_num}"
            valve = await station.add_object(ns_idx, valve_name, 
                                           objecttype=object_types["valve_type"])
            created_nodes.append(valve)
            
            # Crea manualmente la struttura della valvola
            description = f"{config['location']} - Valvola {valve_num}"
            desc_var = await valve.add_variable(ns_idx, "Description", description, ua.VariantType.String)
            
            # Status folder
            status_folder = await valve.add_object(ns_idx, "Status")
            is_irrigating = await status_folder.add_variable(ns_idx, "IsIrrigating", False, ua.VariantType.Boolean)
            mode = await status_folder.add_variable(ns_idx, "Mode", "Off", ua.VariantType.String)
            remaining_time = await status_folder.add_variable(ns_idx, "RemainingTime", 0, ua.VariantType.Int32)
            next_scheduled = await status_folder.add_variable(ns_idx, "NextScheduledStart", None, ua.VariantType.DateTime)
            
            # Commands folder
            commands_folder = await valve.add_object(ns_idx, "Commands")
            duration_cmd = await commands_folder.add_variable(ns_idx, "CommandDuration", 0, ua.VariantType.Int32)
            start_cmd = await commands_folder.add_variable(ns_idx, "CommandStart", False, ua.VariantType.Boolean)
            stop_cmd = await commands_folder.add_variable(ns_idx, "CommandStop", False, ua.VariantType.Boolean)
            
            # Rendi scrivibili i comandi
            await duration_cmd.set_writable()
            await start_cmd.set_writable()
            await stop_cmd.set_writable()
            
            created_nodes.extend([desc_var, status_folder, is_irrigating, mode, remaining_time, next_scheduled,
                                commands_folder, duration_cmd, start_cmd, stop_cmd])
    
    print(f"✅ AddressSpace creato con {len(created_nodes)} nodi")
    return created_nodes

async def export_professional_nodeset():
    """Funzione principale di export con ObjectTypes"""
    print("🌱 Export NodeSet PROFESSIONALE - Sistema di Irrigazione con ObjectTypes")
    print("=" * 80)
    
    # Crea server temporaneo per export
    server = Server()
    
    try:
        print("🔧 Inizializzazione server temporaneo...")
        await server.init()
        
        # Configurazione
        server.set_endpoint("opc.tcp://localhost:48402/professional_export")
        server.set_server_name("Professional Irrigation Export Server")
        
        # Registra namespace
        namespace_uri = "http://mvlabs.it/irrigation"
        ns_idx = await server.register_namespace(namespace_uri)
        print(f"📋 Namespace registrato: {namespace_uri} (index: {ns_idx})")
        
        # Crea ObjectTypes personalizzati
        object_types = await create_custom_object_types(server, ns_idx)
        
        # Crea AddressSpace usando i tipi
        created_nodes = await create_professional_addressspace(server, ns_idx, object_types)
        
        # Aggiungi ObjectTypes alla lista per l'export
        all_nodes = list(object_types.values()) + created_nodes
        
        # Avvia server temporaneamente
        print("🚀 Avvio server temporaneo...")
        await server.start()
        
        # Export NodeSet
        output_file = "irrigation_professional_nodeset.xml"
        print(f"📤 Esportazione NodeSet professionale in {output_file}...")
        
        await server.export_xml(all_nodes, output_file)
        
        print(f"✅ NodeSet professionale esportato con successo!")
        print(f"📁 File creato: {os.path.abspath(output_file)}")
        
        # Statistiche
        type_count = len(object_types)
        instance_count = len(created_nodes)
        total_count = len(all_nodes)
        
        print("\n" + "=" * 80)
        print("📊 CONTENUTO NODESET PROFESSIONALE:")
        print("=" * 80)
        print(f"🔧 ObjectTypes personalizzati: {type_count}")
        print(f"   • IrrigationSystemType")
        print(f"   • IrrigationStationType") 
        print(f"   • IrrigationValveType")
        print(f"📦 Istanze create: {instance_count}")
        print(f"   • 1 Sistema di irrigazione")
        print(f"   • 3 Stazioni (Station1, Station2, Station3)")
        print(f"   • 5 Valvole totali")
        print(f"📋 Nodi totali esportati: {total_count}")
        
        print("\n" + "=" * 80)
        print("📋 COME IMPORTARE IN UAMODELER:")
        print("=" * 80)
        print("1. Apri UAModeler")
        print("2. File → Import → NodeSet...")
        print(f"3. Seleziona: {output_file}")
        print("4. Conferma l'import del namespace")
        print("5. Naviga in:")
        print("   • Types → ObjectTypes → IrrigationSystemType")
        print("   • Objects → IrrigationSystem")
        print("\n💡 VANTAGGI OBJECTTYPES:")
        print("   • Struttura professionale e riutilizzabile")
        print("   • Information Model completo")
        print("   • Facile estensione per nuove istanze")
        print("   • Standard OPC-UA Companion Specifications")
        
        print(f"\n🎯 COMPATIBILITÀ:")
        print(f"   • Server esistente: INVARIATO (continua a funzionare)")
        print(f"   • Client esistenti: INVARIATI (stessa struttura finale)")
        print(f"   • UAModeler: Mostra struttura professionale con tipi")
        
    except Exception as e:
        print(f"❌ Errore durante l'export: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("🛑 Chiusura server temporaneo...")
        try:
            await server.stop()
        except:
            pass  # Server potrebbe non essere stato avviato
    
    return True

if __name__ == "__main__":
    success = asyncio.run(export_professional_nodeset())
    
    if success:
        print("\n🎉 EXPORT PROFESSIONALE COMPLETATO!")
        print("   Il file irrigation_professional_nodeset.xml è pronto per UAModeler")
        print("   🏆 Ora avete ObjectTypes personalizzati per un progetto da 100%!")
    else:
        print("\n❌ Export fallito. Controlla gli errori sopra.")
    
    input("\nPremi INVIO per uscire...")