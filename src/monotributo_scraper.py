#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MÓDULO DE SCRAPING DE DATOS - SISTEMA EXPERTO MONOTRIBUTO
=========================================================

Este módulo se encarga exclusivamente del scraping de datos de la página
oficial de AFIP para obtener información actualizada sobre categorías y
pagos del Monotributo.

Autor: Sistema Experto Emprendedor Fueguino
Fecha: 2025
"""

import pandas as pd
import os


def limpiar_valor(texto):
    """
    Limpia un string de valor monetario (ej: '$ 7.813.063,45'),
    de superficie ('Hasta 30 m2') o energía ('Hasta 3330 Kw') a float.
    Retorna None si no se puede convertir.
    
    Args:
        texto (str): Texto a limpiar y convertir
        
    Returns:
        float or None: Valor numérico limpio o None si no se puede convertir
    """
    if pd.isna(texto):  # Maneja valores NaN (vacíos) de pandas
        return None
    
    s_valor = str(texto).strip()
    if not s_valor or s_valor.lower() in ['nan', 'none', '']:
        return None
    
    # Eliminar '$', 'Hasta ', ' m2', ' Kw', puntos de miles y espacios
    s_valor = s_valor.replace('$', '').replace('Hasta ', '').replace(' m2', '').replace(' Kw', '').strip()
    # Eliminar puntos de miles (pero no el punto decimal)
    if ',' in s_valor:
        s_valor = s_valor.replace('.', '').replace(',', '.')
    
    try:
        valor = float(s_valor)
        return valor if valor > 0 else None
    except (ValueError, TypeError):
        return None  # Retorna None si no se puede convertir


def obtener_datos_monotributo_web():
    """
    🕷️ FUNCIÓN PRINCIPAL DE SCRAPING
    
    Realiza scraping de la página oficial de AFIP para obtener datos
    actualizados de categorías y pagos del Monotributo.
    
    URL objetivo: https://www.afip.gob.ar/monotributo/categorias.asp
    
    Returns:
        tuple: (categorias_dict, pagos_dict) si es exitoso, (None, None) si falla
        
    Estructura de retorno:
        categorias_dict = {
            "servicios": {"A": {"ingresos": float, "superficie": float, ...}, ...},
            "venta": {"A": {"ingresos": float, "superficie": float, ...}, ...}
        }
        
        pagos_dict = {
            "servicios": {"A": {"solo_impuesto": float, "completo": float, ...}, ...},
            "venta": {"A": {"solo_impuesto": float, "completo": float, ...}, ...}
        }
    """
    url = "https://www.afip.gob.ar/monotributo/categorias.asp"
    categorias_dict = {"servicios": {}, "venta": {}}
    pagos_dict = {"servicios": {}, "venta": {}}

    print(f"🌐 Realizando scraping de: {url}")
    
    try:
        # Usar pandas para leer todas las tablas de la página
        print("📥 Descargando página web...")
        tablas = pd.read_html(url, encoding='utf-8')
        print(f"📊 Encontradas {len(tablas)} tablas en la página")
        
        df_monotributo = None
        
        # Buscar la tabla correcta: aquella que contenga una columna 'Categ.'
        # y que contenga la categoría 'K'.
        for i, tabla in enumerate(tablas):
            print(f"🔍 Analizando tabla {i+1}: {tabla.shape} - Columnas: {tabla.columns.tolist()[:3]}...")
            
            if (len(tabla.columns) > 0 and 
                (tabla.columns[0] == 'Categ.' or 
                 (isinstance(tabla.columns[0], tuple) and 'Categ.' in str(tabla.columns[0])))):
                
                # Verificar si la categoría 'K' está en la primera columna
                primera_columna_str = tabla.iloc[:, 0].astype(str).values
                if any('K' in str(val) for val in primera_columna_str):
                    df_monotributo = tabla
                    print(f"✅ Tabla de monotributo encontrada (tabla #{i+1})")
                    break
        
        if df_monotributo is None:
            print(f"❌ Error: No se encontró la tabla de categorías del Monotributo en {url}")
            print("📋 Tablas disponibles:")
            for i, tabla in enumerate(tablas):
                print(f"   Tabla {i+1}: {tabla.shape} - Primeras columnas: {tabla.columns.tolist()[:5]}")
            return None, None
        
        print("📊 Tabla de Monotributo encontrada, procesando datos...")
        
        # Aplanar columnas multi-nivel si existen
        nuevas_columnas = []
        for col in df_monotributo.columns:
            if isinstance(col, tuple):
                # Simplificar nombres de columnas compuestas
                if col[0] == col[1]:
                    nuevas_columnas.append(col[0].strip())
                elif col[0] == 'Impuesto integrado' and col[1] == 'Locaciones y prestaciones de servicios':
                    nuevas_columnas.append('Impuesto integrado Servicios')
                elif col[0] == 'Impuesto integrado' and col[1] == 'Venta de cosas muebles':
                    nuevas_columnas.append('Impuesto integrado Venta')
                elif col[0] == 'Total' and col[1] == 'Locaciones y prestaciones de servicios':
                    nuevas_columnas.append('Total Servicios')
                elif col[0] == 'Total' and col[1] == 'Venta de cosas muebles':
                    nuevas_columnas.append('Total Venta')
                else:
                    nuevas_columnas.append('_'.join(map(str, col)).strip())
            else:
                nuevas_columnas.append(col.strip())
        
        # Asignar nuevos nombres de columnas
        df_monotributo.columns = nuevas_columnas
        
        print("📋 Estructura de datos detectada:")
        print(f"   - Columnas: {df_monotributo.columns.tolist()}")
        print(f"   - Filas: {len(df_monotributo)}")
        print(f"   - Primera fila de datos: {df_monotributo.iloc[0].tolist()}")
        
        # Procesar datos por categoría
        for index, fila in df_monotributo.iterrows():
            categoria = fila.iloc[0]  # Primera columna = categoría (A, B, C, etc.)
            
            if pd.isna(categoria) or categoria.strip() == '':
                continue
                
            categoria = categoria.strip()
            
            # Extraer datos comunes (ingresos, superficie, energía, alquileres)
            datos_categoria = {}
            
            # Mapeo de columnas esperadas (ACTUALIZADO JULIO 2025 - NOMBRES EXACTOS DE AFIP)
            mapeo_columnas = {
                'ingresos': ['Ingresos brutos (*)', 'Ingresos brutos', 'Ingresos brutos anuales', 'Ingresos Brutos'],
                'superficie': ['Sup. Afectada (**)', 'Sup. Afectada', 'Superficie afectada a la actividad', 'Superficie'],
                'energia': ['Energía eléctrica consumida anualmente', 'Energia', 'Energía'],
                'alquileres': ['Alquileres devengados anualmente', 'Alquileres']
            }
            
            # Extraer datos básicos de la categoría
            for campo, posibles_nombres in mapeo_columnas.items():
                valor = None
                for nombre_col in posibles_nombres:
                    if nombre_col in df_monotributo.columns:
                        valor_raw = fila[nombre_col]
                        valor = limpiar_valor(valor_raw)
                        if valor is not None:
                            print(f"   📊 {categoria}: {campo} = {valor} (columna: '{nombre_col}')")
                            break
                
                if valor is not None:
                    datos_categoria[campo] = valor
                else:
                    print(f"   ⚠️  {categoria}: No se encontró valor para {campo} en columnas: {posibles_nombres}")
            
            # Agregar precio unitario máximo para venta (solo categoría A)
            if categoria == 'A':
                # Buscar columna de precio unitario
                for col in df_monotributo.columns:
                    if 'precio' in col.lower() and 'unitario' in col.lower():
                        precio_unitario = limpiar_valor(fila[col])
                        if precio_unitario is not None:
                            datos_categoria['precio_unitario_maximo'] = precio_unitario
                            break
            
            # Guardar datos de categoría para servicios y venta
            if datos_categoria:
                categorias_dict["servicios"][categoria] = datos_categoria.copy()
                categorias_dict["venta"][categoria] = datos_categoria.copy()
            
            # Extraer datos de pagos
            pagos_categoria = {}
            
            # Mapeo de columnas de pagos
            mapeo_pagos = {
                'solo_impuesto': ['Impuesto integrado Servicios', 'Impuesto integrado Venta'],
                'completo': ['Total Servicios', 'Total Venta'],
                'sipa': ['SIPA'],
                'obra_social': ['Obra Social']
            }
            
            for campo, posibles_nombres in mapeo_pagos.items():
                for nombre_col in posibles_nombres:
                    if nombre_col in df_monotributo.columns:
                        valor = limpiar_valor(fila[nombre_col])
                        if valor is not None:
                            if campo in ['solo_impuesto', 'completo']:
                                # Determinar si es para servicios o venta
                                tipo = 'servicios' if 'Servicios' in nombre_col else 'venta'
                                if categoria not in pagos_dict[tipo]:
                                    pagos_dict[tipo][categoria] = {}
                                pagos_dict[tipo][categoria][campo] = valor
                            else:
                                # SIPA y Obra Social son iguales para ambos tipos
                                for tipo in ['servicios', 'venta']:
                                    if categoria not in pagos_dict[tipo]:
                                        pagos_dict[tipo][categoria] = {}
                                    pagos_dict[tipo][categoria][campo] = valor
        
        print(f"✅ Scraping completado exitosamente:")
        print(f"   - Categorías de servicios: {list(categorias_dict['servicios'].keys())}")
        print(f"   - Categorías de venta: {list(categorias_dict['venta'].keys())}")
        print(f"   - Pagos de servicios: {list(pagos_dict['servicios'].keys())}")
        print(f"   - Pagos de venta: {list(pagos_dict['venta'].keys())}")
        
        return categorias_dict, pagos_dict
        
    except Exception as e:
        print(f"❌ Error durante el scraping: {e}")
        return None, None
