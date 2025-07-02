from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
import sys

# Agregar src/ al path para importar módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

# Importaciones modulares actualizadas desde src/
from monotributo_scraper import obtener_datos_monotributo_web
from data_manager import cargar_datos_json_locales, guardar_datos_json_locales
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Sistema Experto Monotributo API")

# Modelos Pydantic para validación de datos
class RespuestaUsuario(BaseModel):
    pregunta_id: str
    respuesta: str
    valor_numerico: Optional[float] = None

class EstadoSesion(BaseModel):
    id_sesion: str
    estado_actual: Dict[str, Any] = {}
    applied_rules: List[str] = []

# =====================================================================================
# BASE DE CONOCIMIENTO (KNOWLEDGE BASE) - SISTEMA EXPERTO MONOTRIBUTO
# =====================================================================================

# Base de conocimiento cargada dinámicamente desde rules.json
knowledge_base = {}

# Funciones auxiliares para evaluación de condiciones complejas
def evaluar_precio_unitario_maximo(estado, respuesta, valor_numerico=None):
    """Evalúa si el precio unitario supera el límite de categoría A"""
    try:
        # Verificar que los datos estén cargados
        if not datos_categorias:
            return False
        
        # Acceder a los datos correctamente (manejar ambos formatos)
        if "datos" in datos_categorias:
            precio_max = datos_categorias["datos"]["venta"]["A"]["precio_unitario_maximo"]
        else:
            precio_max = datos_categorias["venta"]["A"]["precio_unitario_maximo"]
        
        # La respuesta debe comenzar con "SÍ" para indicar que supera el límite
        resultado = respuesta.startswith("SÍ")
        return resultado
    except Exception as e:
        return False

def evaluar_ingresos_limite(estado, respuesta, valor_numerico):
    """Evalúa si los ingresos exceden el límite máximo permitido"""
    if valor_numerico is None:
        return False
    
    try:
        # Verificar que los datos estén cargados
        if not datos_categorias:
            return False
        
        # Acceder a los datos correctamente (manejar ambos formatos)
        if "datos" in datos_categorias:
            categorias_data = datos_categorias["datos"]
        else:
            categorias_data = datos_categorias
            
        tipo_actividad = estado.get("tipo_actividad", "servicios")
        
        if tipo_actividad == "venta":
            categoria_maxima = estado.get("categoria_maxima", "K")
            limite_maximo = categorias_data[tipo_actividad][categoria_maxima]["ingresos"]
        else:
            limite_maximo = categorias_data[tipo_actividad]["H"]["ingresos"]
        
        resultado = valor_numerico > limite_maximo
        return resultado
    except Exception as e:
        return False

def evaluar_ingresos_dentro_limite(estado, respuesta, valor_numerico):
    """Evalúa si los ingresos están dentro del límite permitido"""
    return not evaluar_ingresos_limite(estado, respuesta, valor_numerico)

def evaluar_supera_parametro(estado, respuesta, parametro_tipo):
    """Evalúa si se supera un parámetro específico (superficie, energía, alquileres)"""
    return respuesta.startswith("SÍ")

def evaluar_supera_parametro_superficie(estado, respuesta, valor_numerico=None):
    """Evalúa si se supera el parámetro de superficie"""
    return evaluar_supera_parametro(estado, respuesta, "superficie")

def evaluar_no_supera_parametro_superficie(estado, respuesta, valor_numerico=None):
    """Evalúa si NO se supera el parámetro de superficie"""
    return not evaluar_supera_parametro(estado, respuesta, "superficie")

def evaluar_supera_parametro_energia(estado, respuesta, valor_numerico=None):
    """Evalúa si se supera el parámetro de energía"""
    return evaluar_supera_parametro(estado, respuesta, "energia")

def evaluar_no_supera_parametro_energia(estado, respuesta, valor_numerico=None):
    """Evalúa si NO se supera el parámetro de energía"""
    return not evaluar_supera_parametro(estado, respuesta, "energia")

def evaluar_supera_parametro_alquileres(estado, respuesta, valor_numerico=None):
    """Evalúa si se supera el parámetro de alquileres"""
    return evaluar_supera_parametro(estado, respuesta, "alquileres")

def evaluar_no_supera_parametro_alquileres(estado, respuesta, valor_numerico=None):
    """Evalúa si NO se supera el parámetro de alquileres"""
    return not evaluar_supera_parametro(estado, respuesta, "alquileres")

# Funciones de post-acción para cálculos complejos
def establecer_tipo_actividad(estado, respuesta):
    """Establece el tipo de actividad basado en la respuesta"""
    estado["tipo_actividad"] = "servicios" if respuesta.startswith("SÍ") else "venta"
    if estado["tipo_actividad"] == "venta":
        estado["categoria_actual"] = "A"
    return estado

def calcular_categoria_por_ingresos(estado, valor_numerico):
    """Calcula la categoría basada en los ingresos anuales"""
    tipo_actividad = estado["tipo_actividad"]
    
    # Acceder a los datos correctamente (manejar ambos formatos)
    if "datos" in datos_categorias:
        categorias_data = datos_categorias["datos"]
    else:
        categorias_data = datos_categorias
    
    for categoria in sorted(categorias_data[tipo_actividad].keys()):
        if valor_numerico <= categorias_data[tipo_actividad][categoria]["ingresos"]:
            if tipo_actividad == "venta" and estado.get("categoria_maxima"):
                if categoria > estado["categoria_maxima"]:
                    categoria = estado["categoria_maxima"]
            estado["categoria_actual"] = categoria
            estado["categoria_final"] = categoria
            break
    return estado

def avanzar_categoria_por_parametro(estado, parametro_tipo):
    """Avanza a la siguiente categoría cuando se supera un parámetro"""
    categoria_actual = estado["categoria_actual"]
    tipo_actividad = estado["tipo_actividad"]
    
    # Acceder a los datos correctamente (manejar ambos formatos)
    if "datos" in datos_categorias:
        categorias_data = datos_categorias["datos"]
    else:
        categorias_data = datos_categorias
    
    categorias_ordenadas = sorted(categorias_data[tipo_actividad].keys())
    idx_actual = categorias_ordenadas.index(categoria_actual)
    
    if parametro_tipo == "alquileres":
        # Para alquileres, buscar categoría con valor diferente
        valor_actual = categorias_data[tipo_actividad][categoria_actual]["alquileres"]
        for cat in categorias_ordenadas[idx_actual + 1:]:
            if categorias_data[tipo_actividad][cat]["alquileres"] > valor_actual:
                estado["categoria_actual"] = cat
                return estado
    else:
        # Para superficie y energía, avanzar a la siguiente categoría
        if idx_actual + 1 < len(categorias_ordenadas):
            estado["categoria_actual"] = categorias_ordenadas[idx_actual + 1]
            return estado
    
    # Si no se puede avanzar más, marcar para régimen general
    estado["excede_parametros"] = True
    return estado

def establecer_categoria_final(estado):
    """Establece la categoría final cuando no se superan más parámetros"""
    estado["categoria_final"] = estado["categoria_actual"]
    return estado

def establecer_categoria_inicial(estado, respuesta):
    """Establece la categoría inicial A para emprendedores sin ingresos"""
    estado["categoria_actual"] = "A"
    estado["categoria_final"] = "A"
    return estado

def establecer_categoria_para_superficie(estado, respuesta):
    """Establece la categoría actual para evaluar superficie cuando tiene local"""
    # Si no hay categoría actual establecida, usar la categoría basada en ingresos
    if "categoria_actual" not in estado:
        # Si se calculó categoría por ingresos anteriormente, usar esa
        if "categoria_final" in estado:
            estado["categoria_actual"] = estado["categoria_final"]
        else:
            # Por defecto, usar categoría A si no hay otra información
            estado["categoria_actual"] = "A"
    
    print(f"Estableciendo categoría para evaluación de superficie: {estado['categoria_actual']}")
    return estado

def avanzar_categoria_por_parametro_superficie(estado, respuesta):
    """Avanza a la siguiente categoría cuando se supera el parámetro de superficie"""
    return avanzar_categoria_por_parametro(estado, "superficie")

def avanzar_categoria_por_parametro_energia(estado, respuesta):
    """Avanza a la siguiente categoría cuando se supera el parámetro de energía"""
    return avanzar_categoria_por_parametro(estado, "energia")

def avanzar_categoria_por_parametro_alquileres(estado, respuesta):
    """Avanza a la siguiente categoría cuando se supera el parámetro de alquileres"""
    return avanzar_categoria_por_parametro(estado, "alquileres")

def calcular_pagos_finales(estado, respuesta_dependencia):
    """Calcula los pagos finales basado en la categoría y relación de dependencia"""
    categoria_final = estado["categoria_final"]
    tipo_actividad = estado["tipo_actividad"]
    
    # Convertir la respuesta del usuario a un booleano
    # La respuesta es "SÍ" si contiene "SÍ" al inicio
    respuesta_str = str(respuesta_dependencia).upper().strip()
    en_relacion_dependencia = respuesta_str.startswith("SÍ")
    
    try:
        # Acceder a los datos correctamente (manejar formato con metadatos)
        if "datos" in datos_pagos:
            pagos_categoria = datos_pagos["datos"][tipo_actividad][categoria_final]
        else:
            pagos_categoria = datos_pagos[tipo_actividad][categoria_final]
        
        # Preparar estructura de pagos
        solo_impuesto = float(pagos_categoria["solo_impuesto"])
        pago_completo = float(pagos_categoria["completo"])
        
        # Calcular SIPA y Obra Social como la diferencia
        sipa_y_obra_social = pago_completo - solo_impuesto
        # Aproximadamente SIPA es 60% y Obra Social 40% del total
        sipa_valor = sipa_y_obra_social * 0.6
        obra_social_valor = sipa_y_obra_social * 0.4
        
        pagos_nacionales = {"impuesto": f"{solo_impuesto:.2f}"}
        
        if en_relacion_dependencia:
            pagos_nacionales["sipa"] = "No aplica - Cubierto por tu empleo actual"
            pagos_nacionales["obra_social"] = "No aplica - Cubierto por tu empleo actual"
            total_nacional = solo_impuesto
        else:
            pagos_nacionales["sipa"] = f"{sipa_valor:.2f}"
            pagos_nacionales["obra_social"] = f"{obra_social_valor:.2f}"
            total_nacional = pago_completo
        
        # Preparar pagos provinciales (AREF)
        pagos_provinciales = {}
        total_provincial = 0
        if datos_aref and categoria_final in datos_aref:
            pagos_provinciales["aref"] = datos_aref[categoria_final]
            total_provincial = float(datos_aref[categoria_final])
        
        total_general = total_nacional + total_provincial
        
        estado["resultado_final"] = {
            "categoria": categoria_final,
            "tipo_actividad": tipo_actividad,
            "pagos_nacionales": pagos_nacionales,
            "pagos_provinciales": pagos_provinciales,
            "total_nacional": total_nacional,
            "total_provincial": total_provincial,
            "total_general": total_general,
            "en_relacion_dependencia": en_relacion_dependencia
        }
    except KeyError as e:
        estado["error"] = f"Error al calcular pagos: {e}"
    
    return estado

# Mapeo de nombres de funciones para carga dinámica
FUNCTION_MAP = {
    "evaluar_precio_unitario_maximo": evaluar_precio_unitario_maximo,
    "evaluar_ingresos_limite": evaluar_ingresos_limite,
    "evaluar_ingresos_dentro_limite": evaluar_ingresos_dentro_limite,
    "evaluar_supera_parametro_superficie": evaluar_supera_parametro_superficie,
    "evaluar_no_supera_parametro_superficie": evaluar_no_supera_parametro_superficie,
    "evaluar_supera_parametro_energia": evaluar_supera_parametro_energia,
    "evaluar_no_supera_parametro_energia": evaluar_no_supera_parametro_energia,
    "evaluar_supera_parametro_alquileres": evaluar_supera_parametro_alquileres,
    "evaluar_no_supera_parametro_alquileres": evaluar_no_supera_parametro_alquileres,
    "establecer_tipo_actividad": establecer_tipo_actividad,
    "calcular_categoria_por_ingresos": calcular_categoria_por_ingresos,
    "avanzar_categoria_por_parametro": avanzar_categoria_por_parametro,
    "establecer_categoria_final": establecer_categoria_final,
    "establecer_categoria_inicial": establecer_categoria_inicial,
    "establecer_categoria_para_superficie": establecer_categoria_para_superficie,
    "avanzar_categoria_por_parametro_superficie": avanzar_categoria_por_parametro_superficie,
    "avanzar_categoria_por_parametro_energia": avanzar_categoria_por_parametro_energia,
    "avanzar_categoria_por_parametro_alquileres": avanzar_categoria_por_parametro_alquileres,
    "calcular_pagos_finales": calcular_pagos_finales
}

def cargar_reglas_desde_json():
    """Carga las reglas de la base de conocimiento desde el archivo rules.json"""
    global knowledge_base
    current_dir = os.path.dirname(os.path.abspath(__file__))
    rules_path = os.path.join(current_dir, 'src', 'knowledge_base', 'rules.json')
    
    try:
        with open(rules_path, 'r', encoding='utf-8') as f:
            rules_data = json.load(f)
        
        # Procesar las reglas cargadas
        for rule_name, rule_data in rules_data.items():
            rule = {
                "condition": rule_data["condition"],
                "action": rule_data["action"],
                "description": rule_data["description"],
                "explanation": rule_data["explanation"]
            }
            
            # Mapear funciones de evaluación si existen
            if "eval_func" in rule_data["condition"]:
                func_name = rule_data["condition"]["eval_func"]
                if func_name in FUNCTION_MAP:
                    rule["condition"]["eval_func"] = FUNCTION_MAP[func_name]
                else:
                    print(f"Advertencia: Función {func_name} no encontrada en FUNCTION_MAP")
            
            # Mapear funciones de post-acción si existen
            if "post_action_func" in rule_data:
                func_name = rule_data["post_action_func"]
                if func_name in FUNCTION_MAP:
                    rule["post_action_func"] = FUNCTION_MAP[func_name]
                else:
                    print(f"Advertencia: Función {func_name} no encontrada en FUNCTION_MAP")
            
            knowledge_base[rule_name] = rule
        
        print(f"Cargadas {len(knowledge_base)} reglas desde rules.json")
        return True
        
    except Exception as e:
        print(f"Error cargando reglas desde JSON: {e}")
        return False

def generar_explicacion_detallada(reglas_aplicadas):
    """Genera explicaciones detalladas y legibles para las reglas aplicadas"""
    explicaciones = []
    
    for rule_name in reglas_aplicadas:
        if rule_name in knowledge_base:
            rule = knowledge_base[rule_name]
            explicacion = {
                "regla": rule_name,
                "descripcion": rule.get("description", "Regla del sistema"),
                "explicacion": rule.get("explanation", "Esta regla se activó según las condiciones del sistema."),
                "tipo": "activada"
            }
            explicaciones.append(explicacion)
        else:
            # Fallback para reglas que no están en el knowledge_base
            explicaciones.append({
                "regla": rule_name,
                "descripcion": "Regla heredada del sistema",
                "explicacion": f"Se aplicó la regla {rule_name} según la lógica del sistema experto.",
                "tipo": "heredada"
            })
    
    return explicaciones

# =====================================================================================
# CARGA DINÁMICA Y GESTIÓN DE DATOS (HECHOS)
# =====================================================================================

# Almacenamiento en memoria de las sesiones
sesiones = {}

# Cargar datos del monotributo al inicio
datos_categorias = None
datos_pagos = None
datos_aref = None

def inicializar_datos():
    global datos_categorias, datos_pagos, datos_aref
    
    print("Inicializando sistema experto...")
    
    # 1. Cargar reglas de la base de conocimiento
    if not cargar_reglas_desde_json():
        print("Error crítico: No se pudieron cargar las reglas del sistema")
        return False
    
    # 2. Cargar datos AREF (hechos provinciales)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(current_dir, 'data', 'aref.json'), 'r') as f:
            datos_aref = json.load(f)
        print("Datos AREF cargados correctamente")
    except Exception as e:
        print(f"Error al cargar aref.json: {e}")
        datos_aref = {}
    
    # 3. Intentar obtener datos actualizados de la web (hechos nacionales)
    print("Obteniendo datos actualizados de ARCA...")
    datos_web_cat, datos_web_pagos = obtener_datos_monotributo_web()
    
    if datos_web_cat and datos_web_pagos:
        datos_categorias = datos_web_cat
        datos_pagos = datos_web_pagos
        guardar_datos_json_locales(datos_categorias, datos_pagos)
        print("Datos del Monotributo actualizados desde ARCA")
    else:
        # Si falla, intentar cargar datos locales
        print("Fallo la conexión web, cargando datos locales...")
        datos_local_cat, datos_local_pagos = cargar_datos_json_locales()
        if datos_local_cat and datos_local_pagos:
            datos_categorias = datos_local_cat
            datos_pagos = datos_local_pagos
            print("Datos locales del Monotributo cargados")
        else:
            datos_categorias = {"servicios": {}, "venta": {}}
            datos_pagos = {"servicios": {}, "venta": {}}
            print("Usando datos por defecto")
    
    # 4. Actualizar pregunta dinámica del precio unitario
    try:
        precio_max = datos_categorias["venta"]["A"]["precio_unitario_maximo"]
        # Actualizar la regla dinámicamente
        if "actividad_servicios_NO" in knowledge_base:
            knowledge_base["actividad_servicios_NO"]["action"]["pregunta"]["texto"] = f"¿El precio unitario de los productos que vas a vender supera los ${precio_max:,.2f}?"
            print(f"Pregunta de precio unitario actualizada: ${precio_max:,.2f}")
    except Exception as e:
        print(f"Error actualizando pregunta de precio unitario: {e}")
    
    print("Sistema experto inicializado correctamente")
    return True

@app.on_event("startup")
async def startup_event():
    inicializar_datos()

# Inicializar datos al importar el módulo
if __name__ != "__main__":
    inicializar_datos()

@app.post("/iniciar_sesion")
async def iniciar_sesion():
    """Inicia una nueva sesión del sistema experto"""
    from uuid import uuid4
    sesion_id = str(uuid4())
    sesiones[sesion_id] = {
        "estado": "inicio",
        "respuestas": {},
        "categoria_actual": None,
        "tipo_actividad": None,
        "applied_rules": []  # Lista de reglas aplicadas para explicación
    }
    
    return {
        "sesion_id": sesion_id,
        "siguiente_pregunta": {
            "id": "persona_juridica",
            "texto": "¿Sos persona jurídica (empresa o sociedad)?",
            "opciones": ["SÍ", "NO (Persona Física)"],
            "tipo": "opcion"
        }
    }

# =====================================================================================
# MOTOR DE INFERENCIA - SISTEMA EXPERTO
# =====================================================================================

def evaluar_condicion(rule_name, rule, estado, respuesta, valor_numerico=None):
    """Evalúa si una regla se activa basada en su condición"""
    condition = rule["condition"]
    
    print(f"  Condición: {condition}")
    
    # Verificar coincidencia de pregunta_id
    if "pregunta_id" in condition:
        if respuesta.pregunta_id != condition["pregunta_id"]:
            print(f"  Pregunta ID no coincide: {respuesta.pregunta_id} != {condition['pregunta_id']}")
            return False
        print(f"  Pregunta ID coincide: {respuesta.pregunta_id}")
    
    # Verificar patrón de pregunta (para preguntas dinámicas)
    if "pregunta_pattern" in condition:
        if not respuesta.pregunta_id.startswith(condition["pregunta_pattern"]):
            print(f"  Patrón no coincide: {respuesta.pregunta_id} no empieza con {condition['pregunta_pattern']}")
            return False
        print(f"  Patrón coincide: {respuesta.pregunta_id}")
    
    # Verificar respuesta exacta
    if "respuesta" in condition:
        if respuesta.respuesta != condition["respuesta"]:
            print(f"  Respuesta no coincide: '{respuesta.respuesta}' != '{condition['respuesta']}'")
            return False
        print(f"  Respuesta coincide: '{respuesta.respuesta}'")
    
    # Evaluar función de evaluación personalizada
    if "eval_func" in condition:
        try:
            func = condition["eval_func"]
            resultado = func(estado, respuesta.respuesta, valor_numerico)
            return resultado
        except Exception as e:
            return False
    
    print(f"  Condición cumplida (sin restricciones adicionales)")
    return True

def generar_pregunta_dinamica(tipo_pregunta, categoria_actual, tipo_actividad):
    """Genera preguntas dinámicas basadas en la categoría actual"""
    print(f"Generando pregunta dinámica:")
    print(f"   - tipo_pregunta: {tipo_pregunta}")
    print(f"   - categoria_actual: {categoria_actual}")
    print(f"   - tipo_actividad: {tipo_actividad}")
    print(f"   - datos_categorias disponible: {datos_categorias is not None}")
    
    try:
        # Acceder a los datos correctamente (manejar tanto formato directo como con metadatos)
        if isinstance(datos_categorias, dict):
            if "datos" in datos_categorias:
                # Formato con metadatos (cuando se carga desde JSON)
                limites = datos_categorias["datos"][tipo_actividad][categoria_actual]
                print(f"   - Usando formato con metadatos")
            else:
                # Formato directo (cuando viene del scraper)
                limites = datos_categorias[tipo_actividad][categoria_actual]
                print(f"   - Usando formato directo")
        else:
            print("Error: datos_categorias no está inicializado correctamente")
            return None
        
        print(f"   - Límites encontrados: {limites}")
        
        if tipo_pregunta == "superficie":
            pregunta = {
                "id": f"superficie_cat_{categoria_actual}",
                "texto": f"¿La superficie afectada de tu local supera los {limites['superficie']} m2?",
                "opciones": ["SÍ (Supera el límite)", "NO (No supera el límite / Desconozco)"],
                "tipo": "opcion",
                "categoria_actual": categoria_actual
            }
            print(f"Pregunta de superficie generada: {pregunta['texto']}")
            return pregunta
        elif tipo_pregunta == "energia":
            pregunta = {
                "id": f"energia_cat_{categoria_actual}",
                "texto": f"¿El consumo de energía eléctrica supera los {limites['energia']} Kw?",
                "opciones": ["SÍ (Supera el límite)", "NO (No supera el límite / Desconozco)"],
                "tipo": "opcion",
                "categoria_actual": categoria_actual
            }
            print(f"Pregunta de energía generada: {pregunta['texto']}")
            return pregunta
        elif tipo_pregunta == "alquileres":
            # Formatear el valor de alquileres como moneda
            alquileres_formateado = f"${limites['alquileres']:,.0f}".replace(',', '.')
            pregunta = {
                "id": f"alquileres_cat_{categoria_actual}",
                "texto": f"¿Los alquileres devengados anuales superan los {alquileres_formateado}?",
                "opciones": ["SÍ (Supera el límite)", "NO (No supera el límite / Desconozco)"],
                "tipo": "opcion",
                "categoria_actual": categoria_actual
            }
            print(f"Pregunta de alquileres generada: {pregunta['texto']}")
            return pregunta
    except Exception as e:
        print(f"Error generando pregunta dinámica: {e}")
        print(f"   - tipo_pregunta: {tipo_pregunta}")
        print(f"   - categoria_actual: {categoria_actual}")
        print(f"   - tipo_actividad: {tipo_actividad}")
        print(f"   - datos_categorias tipo: {type(datos_categorias)}")
        if isinstance(datos_categorias, dict):
            print(f"   - claves en datos_categorias: {list(datos_categorias.keys())}")
        import traceback
        traceback.print_exc()
        return None

def ejecutar_accion(rule_name, action, estado, respuesta, valor_numerico=None):
    """Ejecuta la acción asociada a una regla activada"""
    tipo_accion = action["tipo"]
    
    print(f"EJECUTANDO ACCIÓN:")
    print(f"   Regla: {rule_name}")
    print(f"   Tipo: {tipo_accion}")
    print(f"   Estado actual: {estado}")
    
    if tipo_accion == "resultado":
        return {
            "tipo": "resultado",
            "mensaje": action["mensaje"],
            "detalles": {
                "razonamiento_aplicado": generar_explicacion_detallada(estado.get("applied_rules", [])),
                "reglas_raw": estado.get("applied_rules", [])  # Para backward compatibility
            }
        }
    
    elif tipo_accion == "pregunta":
        return {
            "tipo": "pregunta",
            "pregunta": action["pregunta"]
        }
    
    elif tipo_accion == "pregunta_superficie":
        categoria_actual = estado.get("categoria_actual", "A")
        tipo_actividad = estado.get("tipo_actividad", "servicios")
        print(f"   Generando pregunta de superficie:")
        print(f"      categoria_actual: {categoria_actual}")
        print(f"      tipo_actividad: {tipo_actividad}")
        
        pregunta = generar_pregunta_dinamica("superficie", categoria_actual, tipo_actividad)
        if pregunta:
            print(f"   Pregunta generada exitosamente")
            return {
                "tipo": "pregunta",
                "pregunta": pregunta
            }
        else:
            print(f"   Error: No se pudo generar pregunta")
            return {
                "tipo": "error",
                "mensaje": "Error generando pregunta de superficie"
            }
    
    elif tipo_accion == "pregunta_energia":
        categoria_actual = estado.get("categoria_actual", "A")
        tipo_actividad = estado.get("tipo_actividad", "servicios")
        pregunta = generar_pregunta_dinamica("energia", categoria_actual, tipo_actividad)
        if pregunta:
            return {
                "tipo": "pregunta",
                "pregunta": pregunta
            }
        else:
            return {
                "tipo": "error",
                "mensaje": "Error generando pregunta de energía"
            }
    
    elif tipo_accion == "pregunta_alquileres":
        categoria_actual = estado.get("categoria_actual", "A")
        tipo_actividad = estado.get("tipo_actividad", "servicios")
        pregunta = generar_pregunta_dinamica("alquileres", categoria_actual, tipo_actividad)
        if pregunta:
            return {
                "tipo": "pregunta",
                "pregunta": pregunta
            }
        else:
            return {
                "tipo": "error",
                "mensaje": "Error generando pregunta de alquileres"
            }
    
    elif tipo_accion == "avanzar_categoria":
        # Verificar si se puede avanzar o se debe ir a régimen general
        if estado.get("excede_parametros"):
            return {
                "tipo": "resultado",
                "mensaje": "Régimen General (Excede límites de parámetros)",
                "detalles": {
                    "razonamiento_aplicado": generar_explicacion_detallada(estado.get("applied_rules", [])),
                    "reglas_raw": estado.get("applied_rules", [])
                }
            }
        else:
            # Generar la siguiente pregunta del mismo tipo de parámetro
            parametro = action["parametro"]
            categoria_actual = estado.get("categoria_actual", "A")
            tipo_actividad = estado.get("tipo_actividad", "servicios")
            
            if parametro == "superficie":
                pregunta = generar_pregunta_dinamica("superficie", categoria_actual, tipo_actividad)
            elif parametro == "energia":
                pregunta = generar_pregunta_dinamica("energia", categoria_actual, tipo_actividad)
            elif parametro == "alquileres":
                pregunta = generar_pregunta_dinamica("alquileres", categoria_actual, tipo_actividad)
            
            if pregunta:
                return {
                    "tipo": "pregunta",
                    "pregunta": pregunta
                }
            else:
                return {
                    "tipo": "resultado",
                    "mensaje": "Régimen General (Excede límites de parámetros)",
                    "detalles": {
                        "razonamiento_aplicado": generar_explicacion_detallada(estado.get("applied_rules", [])),
                        "reglas_raw": estado.get("applied_rules", [])
                    }
                }
    
    elif tipo_accion == "resultado_final":
        # Generar resultado final con la información calculada
        if "error" in estado:
            return {
                "tipo": "error",
                "mensaje": estado["error"],
                "detalles": {
                    "razonamiento_aplicado": generar_explicacion_detallada(estado.get("applied_rules", [])),
                    "reglas_raw": estado.get("applied_rules", [])
                }
            }
        elif "resultado_final" in estado:
            resultado = estado["resultado_final"]
            return {
                "tipo": "resultado",
                "mensaje": f"Te corresponde la Categoría {resultado['categoria']}",
                "detalles": {
                    **resultado,
                    "razonamiento_aplicado": generar_explicacion_detallada(estado.get("applied_rules", [])),
                    "reglas_raw": estado.get("applied_rules", [])
                }
            }
        else:
            return {
                "tipo": "error",
                "mensaje": "Error al calcular el resultado final",
                "detalles": {
                    "razonamiento_aplicado": generar_explicacion_detallada(estado.get("applied_rules", [])),
                    "reglas_raw": estado.get("applied_rules", [])
                }
            }
    
    return None

@app.post("/responder/{sesion_id}")
async def procesar_respuesta(sesion_id: str, respuesta: RespuestaUsuario):
    """Motor de Inferencia - Procesa la respuesta del usuario consultando la Base de Conocimiento"""
    if sesion_id not in sesiones:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    estado = sesiones[sesion_id]
    estado["respuestas"][respuesta.pregunta_id] = respuesta.dict()
    
    # Debugging
    print(f"\n=== MOTOR DE INFERENCIA ===")
    print(f"Procesando respuesta - ID: {respuesta.pregunta_id}")
    print(f"Respuesta: {respuesta.respuesta}")
    if respuesta.valor_numerico:
        print(f"Valor numérico: {respuesta.valor_numerico}")
    
    # Manejar pregunta dinámica para precio unitario
    if respuesta.pregunta_id == "precio_unitario":
        try:
            # Acceder a los datos correctamente (manejar ambos formatos)
            if "datos" in datos_categorias:
                precio_max = datos_categorias["datos"]["venta"]["A"]["precio_unitario_maximo"]
            else:
                precio_max = datos_categorias["venta"]["A"]["precio_unitario_maximo"]
            # Actualizar la regla dinámicamente
            knowledge_base["actividad_servicios_NO"]["action"]["pregunta"]["texto"] = f"¿El precio unitario de los productos que vas a vender supera los ${precio_max:,.2f}?"
        except:
            pass
    
    # MOTOR DE INFERENCIA: Consultar la Base de Conocimiento
    # Priorizar reglas de respuesta exacta sobre reglas con funciones de evaluación
    reglas_ordenadas = []
    reglas_con_funciones = []
    
    for rule_name, rule in knowledge_base.items():
        if "eval_func" in rule["condition"]:
            reglas_con_funciones.append((rule_name, rule))
        else:
            reglas_ordenadas.append((rule_name, rule))
    
    # Evaluar primero reglas exactas, luego reglas con funciones
    reglas_ordenadas.extend(reglas_con_funciones)
    
    for rule_name, rule in reglas_ordenadas:
        # Evaluar si la regla se activa
        if evaluar_condicion(rule_name, rule, estado, respuesta, respuesta.valor_numerico):
            
            print(f"REGLA ACTIVADA: {rule_name}")
            print(f"   Acción: {rule['action']['tipo']}")
            if 'post_action_func' in rule:
                print(f"   Post-action: {rule['post_action_func']}")
            
            # Registrar la regla aplicada para explicación
            estado["applied_rules"].append(rule_name)
            
            # Ejecutar post_action_func si existe
            if "post_action_func" in rule:
                try:
                    func = rule["post_action_func"]
                    # Si es un string, buscar la función en FUNCTION_MAP
                    if isinstance(func, str):
                        print(f"Ejecutando post_action_func (por nombre): {func}")
                        func = FUNCTION_MAP.get(func)
                    else:
                        print(f"Ejecutando post_action_func (función directa): {func}")
                    
                    if func and callable(func):
                        if respuesta.valor_numerico is not None:
                            estado = func(estado, respuesta.valor_numerico)
                        else:
                            estado = func(estado, respuesta.respuesta)
                        print(f"Post-action ejecutada correctamente")
                        print(f"   Estado actualizado: categoria_actual = {estado.get('categoria_actual', 'NO ESTABLECIDA')}")
                    else:
                        print(f"Función post_action no encontrada o no es callable: {rule['post_action_func']}")
                        print(f"   Tipo: {type(rule['post_action_func'])}")
                        if isinstance(rule['post_action_func'], str):
                            print(f"   Funciones disponibles: {list(FUNCTION_MAP.keys())}")
                except Exception as e:
                    print(f"Error ejecutando post_action: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Ejecutar la acción principal
            print(f"Ejecutando acción principal: {rule['action']['tipo']}")
            resultado = ejecutar_accion(rule_name, rule["action"], estado, respuesta, respuesta.valor_numerico)
            
            if resultado:
                print(f"Acción ejecutada, retornando resultado")
                return resultado
            else:
                print(f"Acción no retornó resultado")
    
    # Si ninguna regla se activó, es un error
    print(f"Ninguna regla se activó para pregunta_id: {respuesta.pregunta_id}, respuesta: {respuesta.respuesta}")
    raise HTTPException(status_code=400, detail=f"Pregunta no reconocida o secuencia inválida. ID: {respuesta.pregunta_id}, Respuesta: {respuesta.respuesta}")

# =====================================================================================
# FIN DEL MOTOR DE INFERENCIA
# =====================================================================================

@app.get("/reiniciar/{sesion_id}")
async def reiniciar_sesion(sesion_id: str):
    """Reinicia una sesión existente"""
    if sesion_id in sesiones:
        del sesiones[sesion_id]
    return await iniciar_sesion()

@app.get("/actualizar_datos")
async def actualizar_datos():
    """Actualiza los datos del monotributo desde la web"""
    if inicializar_datos():
        return {"mensaje": "Datos actualizados correctamente", "reglas_cargadas": len(knowledge_base)}
    else:
        return {"error": "Error al actualizar los datos"}

@app.get("/info_sistema")
async def info_sistema():
    """Proporciona información sobre el estado del sistema experto"""
    return {
        "reglas_cargadas": len(knowledge_base),
        "reglas_disponibles": list(knowledge_base.keys()),
        "datos_categorias_disponibles": bool(datos_categorias),
        "datos_pagos_disponibles": bool(datos_pagos),
        "datos_aref_disponibles": bool(datos_aref),
        "sistema": "Sistema Experto Monotributo v2.0 - Modular"
    }

# Montar la carpeta static para archivos estáticos
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_static_dir = os.path.join(current_dir, 'frontend', 'static')
frontend_templates_dir = os.path.join(current_dir, 'frontend', 'templates')

app.mount("/static", StaticFiles(directory=frontend_static_dir), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(frontend_templates_dir, 'index.html'))

# Punto de entrada para ejecución directa - ACTUALIZACIÓN 7 MODULAR
if __name__ == "__main__":
    import uvicorn
    import os
    
    # Puerto dinámico para Render - ACTUALIZACIÓN 7
    port = int(os.environ.get("PORT", 8000))
    
    print("SISTEMA EXPERTO EMPRENDEDOR FUEGUINO - ACTUALIZACIÓN 7 MODULAR")
    print(f"Puerto configurado: {port}")
    print("Arquitectura modular con reglas en JSON!")
    print("Base de conocimiento separada y explicaciones mejoradas")
    print("Iniciando sistema experto...")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
