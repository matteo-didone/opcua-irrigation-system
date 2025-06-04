#!/usr/bin/env python3
"""
🌱 Export NodeSet per UAModeler - Sistema di Irrigazione
Crea un file XML che può essere importato direttamente in UAModeler
"""

import asyncio
import os
from asyncua import Server

async def create_irrigation_addressspace(server, ns_idx):
    """Ricrea l'AddressSpace identico al server principale"""
    objects = server.get_objects_node()
    
    # Root del sistema
    irrigation_root = await objects.add_object(ns_idx, "IrrigationSystem")
    
    # Sistema on/off
    system_state = await irrigation_root.add_variable(ns_idx, "SystemState", True)
    await system_state.set_writable()
    
    # Lista per tenere traccia di tutti i nodi creati
    created_nodes = [irrigation_root, system_state]
    
    # Crea nodi per ogni valvola (struttura semplificata come nel server)
    valve_configs = [
        ("Station1_Valve1", "Giardino Anteriore - Valvola 1"),
        ("Station1_Valve2", "Giardino Anteriore - Valvola 2"),
        ("Station2_Valve1", "Aiuole Laterali - Valvola 1"),
        ("Station3_Valve1", "Giardino Posteriore - Valvola 1"),
        ("Station3_Valve2", "Giardino Posteriore - Valvola 2")
    ]
    
    for valve_id, description in valve_configs:
        valve_node = await irrigation_root.add_object(ns_idx, valve_id)
        created_nodes.append(valve_node)
        
        # Aggiungi descrizione come variabile
        desc_node = await valve_node.add_variable(ns_idx, "Description", description)
        created_nodes.append(desc_node)
        
        # Status (read-only)
        is_irrigating = await valve_node.add_variable(ns_idx, "IsIrrigating", False)
        mode = await valve_node.add_variable(ns_idx, "Mode", "Off")
        remaining_time = await valve_node.add_variable(ns_idx, "RemainingTime", 0)
        
        created_nodes.extend([is_irrigating, mode, remaining_time])
        
        # Commands (writable)
        duration_cmd = await valve_node.add_variable(ns_idx, "CommandDuration", 0)
        start_cmd = await valve_node.add_variable(ns_idx, "CommandStart", False)
        stop_cmd = await valve_node.add_variable(ns_idx, "CommandStop", False)
        
        await duration_cmd.set_writable()
        await start_cmd.set_writable()
        await stop_cmd.set_writable()
        
        created_nodes.extend([duration_cmd, start_cmd, stop_cmd])
    
    return created_nodes

async def export_to_uamodeler():
    """Funzione principale di export"""
    print("🌱 Export NodeSet per UAModeler - Sistema di Irrigazione")
    print("=" * 65)
    
    # Crea server temporaneo per export
    server = Server()
    
    try:
        print("🔧 Inizializzazione server temporaneo...")
        await server.init()
        
        # Configurazione minima
        server.set_endpoint("opc.tcp://localhost:48401/export")
        server.set_server_name("Irrigation Export Server")
        
        # Registra namespace (IDENTICO al server principale)
        namespace_uri = "http://mvlabs.it/irrigation"
        ns_idx = await server.register_namespace(namespace_uri)
        print(f"📋 Namespace registrato: {namespace_uri} (index: {ns_idx})")
        
        # Crea AddressSpace
        print("🏗️  Creazione AddressSpace...")
        created_nodes = await create_irrigation_addressspace(server, ns_idx)
        print(f"📊 Creati {len(created_nodes)} nodi")
        
        # Avvia server temporaneamente
        print("🚀 Avvio server temporaneo...")
        await server.start()
        
        # Export NodeSet - usa i nodi creati invece dell'indice namespace
        output_file = "irrigation_nodeset.xml"
        print(f"📤 Esportazione in {output_file}...")
        
        await server.export_xml(created_nodes, output_file)
        
        print(f"✅ NodeSet esportato con successo!")
        print(f"📁 File creato: {os.path.abspath(output_file)}")
        
        # Istruzioni per UAModeler
        print("\n" + "=" * 65)
        print("📋 COME IMPORTARE IN UAMODELER:")
        print("=" * 65)
        print("1. Apri UAModeler")
        print("2. File → Import → NodeSet...")
        print(f"3. Seleziona: {output_file}")
        print("4. Conferma l'import del namespace")
        print("5. Naviga in: Objects → IrrigationSystem")
        print("\n💡 SUGGERIMENTI:")
        print("   • Dopo l'import, puoi modificare il modello")
        print("   • Puoi aggiungere tipi personalizzati")
        print("   • Salva il progetto UAModeler per future modifiche")
        print("   • Puoi esportare di nuovo da UAModeler se necessario")
        
        # Verifica contenuto
        print(f"\n📊 CONTENUTO ESPORTATO:")
        print(f"   • Namespace: {namespace_uri}")
        print(f"   • Sistema principale: IrrigationSystem")
        print(f"   • Controllo sistema: SystemState")
        print(f"   • Valvole: 5 (Station1_Valve1, Station1_Valve2, etc.)")
        print(f"   • Variabili per valvola: 6 (3 status + 3 command)")
        
    except Exception as e:
        print(f"❌ Errore durante l'export: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("🛑 Chiusura server temporaneo...")
        await server.stop()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(export_to_uamodeler())
    
    if success:
        print("\n🎉 EXPORT COMPLETATO CON SUCCESSO!")
        print("   Il file irrigation_nodeset.xml è pronto per UAModeler")
    else:
        print("\n❌ Export fallito. Controlla gli errori sopra.")
    
    input("\nPremi INVIO per uscire...")