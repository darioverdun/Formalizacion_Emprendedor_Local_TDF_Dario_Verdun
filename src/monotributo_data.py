#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÓDULO PRINCIPAL DE DATOS - SISTEMA EXPERTO MONOTRIBUTO
=======================================================

Este módulo unifica la gestión de datos del sistema experto,
combinando el scraping web y la gestión de archivos locales.

Autor: Sistema Experto Emprendedor Fueguino
Fecha: 2025
"""

from monotributo_scraper import obtener_datos_monotributo_web
from data_manager import (
    cargar_datos_json_locales,
    guardar_datos_json_locales,
    verificar_integridad_datos,
    obtener_info_archivos
)


def inicializar_datos_monotributo():
    """
    🚀 Inicializa los datos del sistema experto con la estrategia más robusta:
    1. Intenta obtener datos actualizados desde la web
    2. Si falla, carga datos locales existentes
    3. Si no hay datos locales, usa datos por defecto
    
    Returns:
        tuple: (categorias, pagos, aref) - Datos del sistema
    """
    print("🔧 Inicializando datos del Sistema Experto Monotributo...")
    
    # 1. Intentar obtener datos actualizados de la web
    print("🌐 Obteniendo datos actualizados desde AFIP...")
    datos_web_cat, datos_web_pagos = obtener_datos_monotributo_web()
    
    datos_categorias = None
    datos_pagos = None
    
    if datos_web_cat and datos_web_pagos:
        # Verificar integridad de datos web
        verificacion = verificar_integridad_datos(datos_web_cat, datos_web_pagos)
        
        if verificacion["valido"]:
            datos_categorias = datos_web_cat
            datos_pagos = datos_web_pagos
            
            # Guardar datos actualizados
            if guardar_datos_json_locales(datos_categorias, datos_pagos):
                print("✅ Datos del Monotributo actualizados y guardados desde AFIP")
            else:
                print("⚠️  Datos obtenidos de AFIP pero no se pudieron guardar localmente")
        else:
            print("❌ Los datos obtenidos de la web no pasaron la verificación de integridad")
            print(f"   Errores: {verificacion['errores']}")
    else:
        print("⚠️  No se pudieron obtener datos actualizados desde la web")
    
    # 2. Si no se obtuvieron datos web válidos, intentar cargar datos locales
    if not datos_categorias or not datos_pagos:
        print("📁 Intentando cargar datos desde archivos locales...")
        datos_local_cat, datos_local_pagos = cargar_datos_json_locales()
        
        if datos_local_cat and datos_local_pagos:
            # Verificar integridad de datos locales
            verificacion = verificar_integridad_datos(datos_local_cat, datos_local_pagos)
            
            if verificacion["valido"]:
                datos_categorias = datos_local_cat
                datos_pagos = datos_local_pagos
                print("✅ Datos locales del Monotributo cargados y verificados")
            else:
                print("❌ Los datos locales no pasaron la verificación de integridad")
                print(f"   Errores: {verificacion['errores']}")
        else:
            print("❌ No se pudieron cargar datos locales")
    
    # 3. Si aún no hay datos, usar estructura por defecto
    if not datos_categorias or not datos_pagos:
        print("⚠️  Usando estructura de datos por defecto (funcionalidad limitada)")
        datos_categorias = {"servicios": {}, "venta": {}}
        datos_pagos = {"servicios": {}, "venta": {}}
    
    # 4. Cargar datos AREF (provinciales)
    datos_aref = cargar_datos_aref()
    
    print("🚀 Inicialización completada")
    return datos_categorias, datos_pagos, datos_aref


def cargar_datos_aref():
    """
    🏔️ Carga los datos provinciales AREF desde archivo local.
    
    Returns:
        dict: Datos AREF o diccionario vacío si no se pueden cargar
    """
    import json
    import os
    
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(current_dir), 'data')
        aref_path = os.path.join(data_dir, 'aref.json')
        
        if os.path.exists(aref_path):
            with open(aref_path, 'r', encoding='utf-8') as f:
                datos_aref = json.load(f)
            print("✅ Datos AREF (provinciales) cargados correctamente")
            return datos_aref
        else:
            print("⚠️  Archivo aref.json no encontrado")
            return {}
            
    except Exception as e:
        print(f"❌ Error al cargar aref.json: {e}")
        return {}


def obtener_estadisticas_sistema():
    """
    📊 Obtiene estadísticas completas del sistema de datos.
    
    Returns:
        dict: Estadísticas del sistema
    """
    print("📊 Obteniendo estadísticas del sistema...")
    
    # Información de archivos
    info_archivos = obtener_info_archivos()
    
    # Cargar datos para estadísticas
    categorias, pagos = cargar_datos_json_locales()
    aref = cargar_datos_aref()
    
    estadisticas = {
        "archivos": info_archivos,
        "datos_disponibles": {
            "categorias": bool(categorias),
            "pagos": bool(pagos),
            "aref": bool(aref)
        },
        "conteos": {},
        "integridad": None
    }
    
    if categorias and pagos:
        # Contar elementos
        estadisticas["conteos"] = {
            "categorias_servicios": len(categorias.get("servicios", {})),
            "categorias_venta": len(categorias.get("venta", {})),
            "pagos_servicios": len(pagos.get("servicios", {})),
            "pagos_venta": len(pagos.get("venta", {})),
            "aref_categorias": len(aref) if aref else 0
        }
        
        # Verificar integridad
        estadisticas["integridad"] = verificar_integridad_datos(categorias, pagos)
    
    return estadisticas


def actualizar_datos_forzado():
    """
    🔄 Fuerza la actualización de datos desde la web, sobrescribiendo archivos locales.
    
    Returns:
        bool: True si la actualización fue exitosa
    """
    print("🔄 Forzando actualización de datos desde AFIP...")
    
    # Obtener datos frescos desde la web
    categorias, pagos = obtener_datos_monotributo_web()
    
    if categorias and pagos:
        # Verificar integridad
        verificacion = verificar_integridad_datos(categorias, pagos)
        
        if verificacion["valido"]:
            # Guardar datos actualizados
            if guardar_datos_json_locales(categorias, pagos):
                print("✅ Actualización forzada completada exitosamente")
                return True
            else:
                print("❌ Error al guardar datos actualizados")
                return False
        else:
            print("❌ Los datos obtenidos no pasaron la verificación de integridad")
            print(f"   Errores: {verificacion['errores']}")
            return False
    else:
        print("❌ No se pudieron obtener datos actualizados desde la web")
        return False
