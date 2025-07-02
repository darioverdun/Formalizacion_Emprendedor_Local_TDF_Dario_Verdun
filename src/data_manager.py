#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÓDULO DE GESTIÓN DE DATOS LOCALES - SISTEMA EXPERTO MONOTRIBUTO
================================================================

Este módulo se encarga de la gestión de archivos JSON locales para
almacenar y cargar datos de categorías y pagos del Monotributo.

Autor: Sistema Experto Emprendedor Fueguino
Fecha: 2025
"""

import json
import os
from datetime import datetime


def guardar_datos_json_locales(categorias, pagos):
    """
    💾 Guarda los datos de categorías y pagos en archivos JSON locales.
    
    Args:
        categorias (dict): Diccionario con datos de categorías
        pagos (dict): Diccionario con datos de pagos
        
    Returns:
        bool: True si se guardaron exitosamente, False en caso de error
    """
    try:
        # Obtener la ruta de la carpeta data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(current_dir), 'data')
        
        # Crear la carpeta data si no existe
        os.makedirs(data_dir, exist_ok=True)
        
        categorias_path = os.path.join(data_dir, 'categorias.json')
        pagos_path = os.path.join(data_dir, 'pagos.json')
        
        # Agregar metadatos de fecha de actualización
        categorias_con_meta = {
            "fecha_actualizacion": datetime.now().isoformat(),
            "fuente": "AFIP - Scraping Web",
            "datos": categorias
        }
        
        pagos_con_meta = {
            "fecha_actualizacion": datetime.now().isoformat(),
            "fuente": "AFIP - Scraping Web", 
            "datos": pagos
        }
        
        # Guardar archivos
        with open(categorias_path, 'w', encoding='utf-8') as f:
            json.dump(categorias_con_meta, f, indent=4, ensure_ascii=False)
            
        with open(pagos_path, 'w', encoding='utf-8') as f:
            json.dump(pagos_con_meta, f, indent=4, ensure_ascii=False)
        
        print(f"💾 Datos guardados exitosamente:")
        print(f"   - Categorías: {categorias_path}")
        print(f"   - Pagos: {pagos_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error al guardar datos localmente: {e}")
        return False


def cargar_datos_json_locales():
    """
    📁 Carga los datos de categorías y pagos desde archivos JSON locales.
    
    Returns:
        tuple: (categorias, pagos) si se cargan exitosamente, (None, None) si falla
    """
    try:
        # Obtener la ruta de la carpeta data
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(current_dir), 'data')
        
        categorias_path = os.path.join(data_dir, 'categorias.json')
        pagos_path = os.path.join(data_dir, 'pagos.json')
        
        # Verificar que los archivos existan
        if not os.path.exists(categorias_path) or not os.path.exists(pagos_path):
            print("⚠️  No se encontraron archivos JSON locales")
            return None, None
        
        # Cargar archivos
        with open(categorias_path, 'r', encoding='utf-8') as f:
            categorias_data = json.load(f)
            
        with open(pagos_path, 'r', encoding='utf-8') as f:
            pagos_data = json.load(f)
        
        # Extraer datos (manejar tanto formato con metadatos como sin metadatos)
        if isinstance(categorias_data, dict) and "datos" in categorias_data:
            categorias = categorias_data["datos"]
            fecha_cat = categorias_data.get("fecha_actualizacion", "Desconocida")
        else:
            categorias = categorias_data
            fecha_cat = "Formato legacy"
            
        if isinstance(pagos_data, dict) and "datos" in pagos_data:
            pagos = pagos_data["datos"]
            fecha_pagos = pagos_data.get("fecha_actualizacion", "Desconocida")
        else:
            pagos = pagos_data
            fecha_pagos = "Formato legacy"
        
        print(f"📁 Datos locales cargados exitosamente:")
        print(f"   - Categorías: {len(categorias.get('servicios', {}))} categorías (Actualizado: {fecha_cat})")
        print(f"   - Pagos: {len(pagos.get('servicios', {}))} categorías (Actualizado: {fecha_pagos})")
        
        return categorias, pagos
        
    except json.JSONDecodeError as e:
        print(f"❌ Error al decodificar JSON: {e}")
        print("   Los archivos pueden estar corruptos")
        return None, None
        
    except Exception as e:
        print(f"❌ Error al cargar datos locales: {e}")
        return None, None


def verificar_integridad_datos(categorias, pagos):
    """
    🔍 Verifica la integridad de los datos cargados.
    
    Args:
        categorias (dict): Datos de categorías
        pagos (dict): Datos de pagos
        
    Returns:
        dict: Resultado de la verificación con estadísticas
    """
    resultado = {
        "valido": True,
        "errores": [],
        "advertencias": [],
        "estadisticas": {}
    }
    
    try:
        # Verificar estructura básica
        if not isinstance(categorias, dict) or not isinstance(pagos, dict):
            resultado["valido"] = False
            resultado["errores"].append("Estructura de datos inválida")
            return resultado
        
        # Verificar que existan las claves principales
        for tipo in ["servicios", "venta"]:
            if tipo not in categorias:
                resultado["errores"].append(f"Falta tipo '{tipo}' en categorías")
                resultado["valido"] = False
                
            if tipo not in pagos:
                resultado["errores"].append(f"Falta tipo '{tipo}' en pagos")
                resultado["valido"] = False
        
        if not resultado["valido"]:
            return resultado
        
        # Estadísticas
        resultado["estadisticas"] = {
            "categorias_servicios": len(categorias.get("servicios", {})),
            "categorias_venta": len(categorias.get("venta", {})),
            "pagos_servicios": len(pagos.get("servicios", {})),
            "pagos_venta": len(pagos.get("venta", {}))
        }
        
        # Verificar que las categorías de servicios y venta coincidan
        cats_servicios = set(categorias.get("servicios", {}).keys())
        cats_venta = set(categorias.get("venta", {}).keys())
        pagos_servicios = set(pagos.get("servicios", {}).keys())
        pagos_venta = set(pagos.get("venta", {}).keys())
        
        if cats_servicios != cats_venta:
            resultado["advertencias"].append("Las categorías de servicios y venta no coinciden")
        
        if cats_servicios != pagos_servicios:
            resultado["advertencias"].append("Las categorías y pagos de servicios no coinciden")
            
        if cats_venta != pagos_venta:
            resultado["advertencias"].append("Las categorías y pagos de venta no coinciden")
        
        # Verificar campos requeridos
        campos_requeridos_cat = ["ingresos", "superficie", "energia", "alquileres"]
        campos_requeridos_pagos = ["solo_impuesto", "completo", "sipa", "obra_social"]
        
        for tipo in ["servicios", "venta"]:
            for cat, datos in categorias.get(tipo, {}).items():
                for campo in campos_requeridos_cat:
                    if campo not in datos:
                        resultado["advertencias"].append(f"Falta campo '{campo}' en categoría {cat} ({tipo})")
        
        for tipo in ["servicios", "venta"]:
            for cat, datos in pagos.get(tipo, {}).items():
                for campo in campos_requeridos_pagos:
                    if campo not in datos:
                        resultado["advertencias"].append(f"Falta campo '{campo}' en pagos {cat} ({tipo})")
        
        print(f"🔍 Verificación de integridad completada:")
        print(f"   - Estado: {'✅ VÁLIDO' if resultado['valido'] else '❌ INVÁLIDO'}")
        print(f"   - Errores: {len(resultado['errores'])}")
        print(f"   - Advertencias: {len(resultado['advertencias'])}")
        
        return resultado
        
    except Exception as e:
        resultado["valido"] = False
        resultado["errores"].append(f"Error durante verificación: {e}")
        return resultado


def obtener_info_archivos():
    """
    📋 Obtiene información sobre los archivos de datos locales.
    
    Returns:
        dict: Información sobre los archivos
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(current_dir), 'data')
    
    info = {
        "data_dir": data_dir,
        "archivos": {}
    }
    
    archivos = ["categorias.json", "pagos.json", "aref.json"]
    
    for archivo in archivos:
        path = os.path.join(data_dir, archivo)
        if os.path.exists(path):
            stat = os.stat(path)
            info["archivos"][archivo] = {
                "existe": True,
                "tamaño": stat.st_size,
                "modificado": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "path": path
            }
        else:
            info["archivos"][archivo] = {
                "existe": False,
                "path": path
            }
    
    return info
