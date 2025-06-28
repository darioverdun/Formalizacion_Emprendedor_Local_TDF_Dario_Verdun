from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
from sistema_experto_5_cop_json import (
    obtener_datos_monotributo_web,
    cargar_datos_json_locales,
    guardar_datos_json_locales
)
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

# Funciones auxiliares para evaluación de condiciones complejas
def evaluar_precio_unitario_maximo(estado, respuesta, valor_numerico=None):
    """Evalúa si el precio unitario supera el límite de categoría A"""
    try:
        precio_max = datos_categorias["venta"]["A"]["precio_unitario_maximo"]
        return respuesta.startswith("SÍ")
    except:
        return False

def evaluar_ingresos_limite(estado, respuesta, valor_numerico):
    """Evalúa si los ingresos exceden el límite máximo permitido"""
    if valor_numerico is None:
        return False
    
    tipo_actividad = estado.get("tipo_actividad", "servicios")
    if tipo_actividad == "venta":
        categoria_maxima = estado.get("categoria_maxima", "K")
        limite_maximo = datos_categorias[tipo_actividad][categoria_maxima]["ingresos"]
    else:
        limite_maximo = datos_categorias[tipo_actividad]["H"]["ingresos"]
    
    return valor_numerico > limite_maximo

def evaluar_supera_parametro(estado, respuesta, parametro_tipo):
    """Evalúa si se supera un parámetro específico (superficie, energía, alquileres)"""
    return respuesta.startswith("SÍ")

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
    
    for categoria in sorted(datos_categorias[tipo_actividad].keys()):
        if valor_numerico <= datos_categorias[tipo_actividad][categoria]["ingresos"]:
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
    categorias_ordenadas = sorted(datos_categorias[tipo_actividad].keys())
    idx_actual = categorias_ordenadas.index(categoria_actual)
    
    if parametro_tipo == "alquileres":
        # Para alquileres, buscar categoría con valor diferente
        valor_actual = datos_categorias[tipo_actividad][categoria_actual]["alquileres"]
        for cat in categorias_ordenadas[idx_actual + 1:]:
            if datos_categorias[tipo_actividad][cat]["alquileres"] > valor_actual:
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

def calcular_pagos_finales(estado, en_relacion_dependencia):
    """Calcula los pagos finales basado en la categoría y relación de dependencia"""
    categoria_final = estado["categoria_final"]
    tipo_actividad = estado["tipo_actividad"]
    
    try:
        pagos_categoria = datos_pagos[tipo_actividad][categoria_final]
        
        # Preparar estructura de pagos
        pagos_nacionales = {"impuesto": pagos_categoria["solo_impuesto"]}
        
        if en_relacion_dependencia:
            pagos_nacionales["sipa"] = "No aplica - Cubierto por tu empleo actual"
            pagos_nacionales["obra_social"] = "No aplica - Cubierto por tu empleo actual"
            total_nacional = float(pagos_categoria["solo_impuesto"])
        else:
            pagos_nacionales["sipa"] = pagos_categoria["sipa"]
            pagos_nacionales["obra_social"] = pagos_categoria["obra_social"]
            total_nacional = float(pagos_categoria["solo_impuesto"]) + float(pagos_categoria["sipa"]) + float(pagos_categoria["obra_social"])
        
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

# BASE DE CONOCIMIENTO - REGLAS DEL SISTEMA EXPERTO
knowledge_base = {
    "persona_juridica_SI": {
        "condition": {
            "pregunta_id": "persona_juridica",
            "respuesta": "SÍ"
        },
        "action": {
            "tipo": "resultado",
            "mensaje": """Régimen General (No calificás para el Monotributo)
Según los datos que ingresaste, no cumplís con los requisitos para inscribirte en el régimen simplificado del Monotributo. Deberás tributar bajo el Régimen General.

Importante: Este régimen implica el cumplimiento de obligaciones impositivas más complejas, con presentaciones mensuales y anuales ante ARCA (como IVA y Ganancias).
Para evitar multas, intereses o sanciones por errores u omisiones, se recomienda contar con el acompañamiento de un profesional matriculado, como un contador o contadora de confianza.

Para más información, podés visitar:
https://www.afip.gob.ar/landing/default.asp"""
        }
    },
    
    "persona_juridica_NO": {
        "condition": {
            "pregunta_id": "persona_juridica",
            "respuesta": "NO (Persona Física)"
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "socio_sociedad",
                "texto": "¿Sos integrante o tenés participación en alguna sociedad o empresa registrada?",
                "opciones": ["SÍ", "NO"],
                "tipo": "opcion"
            }
        }
    },
    
    "socio_sociedad_SI": {
        "condition": {
            "pregunta_id": "socio_sociedad",
            "respuesta": "SÍ"
        },
        "action": {
            "tipo": "resultado",
            "mensaje": """Régimen General (No calificás para el Monotributo)
Según los datos que ingresaste, no cumplís con los requisitos para inscribirte en el régimen simplificado del Monotributo. Deberás tributar bajo el Régimen General.

Importante: Este régimen implica el cumplimiento de obligaciones impositivas más complejas, con presentaciones mensuales y anuales ante ARCA (como IVA y Ganancias).
Para evitar multas, intereses o sanciones por errores u omisiones, se recomienda contar con el acompañamiento de un profesional matriculado, como un contador o contadora de confianza.

Para más información, podés visitar:
https://www.afip.gob.ar/landing/default.asp"""
        }
    },
    
    "socio_sociedad_NO": {
        "condition": {
            "pregunta_id": "socio_sociedad",
            "respuesta": "NO"
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "actividades_diferentes",
                "texto": "¿Vas a realizar más de 3 actividades económicas diferentes?",
                "opciones": ["SÍ", "NO (3 o menos actividades)"],
                "tipo": "opcion"
            }
        }
    },
    
    "actividades_diferentes_SI": {
        "condition": {
            "pregunta_id": "actividades_diferentes",
            "respuesta": "SÍ"
        },
        "action": {
            "tipo": "resultado",
            "mensaje": """Régimen General (No calificás para el Monotributo)
Según los datos que ingresaste, no cumplís con los requisitos para inscribirte en el régimen simplificado del Monotributo. Deberás tributar bajo el Régimen General.

Importante: Este régimen implica el cumplimiento de obligaciones impositivas más complejas, con presentaciones mensuales y anuales ante ARCA (como IVA y Ganancias).
Para evitar multas, intereses o sanciones por errores u omisiones, se recomienda contar con el acompañamiento de un profesional matriculado, como un contador o contadora de confianza.

Para más información, podés visitar:
https://www.afip.gob.ar/landing/default.asp"""
        }
    },
    
    "actividades_diferentes_NO": {
        "condition": {
            "pregunta_id": "actividades_diferentes",
            "respuesta": "NO (3 o menos actividades)"
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "actividad_servicios",
                "texto": "¿Tu actividad principal es la prestación de servicios?",
                "opciones": ["SÍ (Prestación de Servicios)", "NO (Venta de Cosas Muebles)"],
                "tipo": "opcion"
            }
        }
    },
    
    "actividad_servicios_SI": {
        "condition": {
            "pregunta_id": "actividad_servicios",
            "respuesta": "SÍ (Prestación de Servicios)"
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "genera_ingresos",
                "texto": "¿Ya estás generando ingresos y podés estimar tu facturación anual?",
                "opciones": ["SÍ", "NO"],
                "tipo": "opcion"
            }
        },
        "post_action_func": lambda estado, respuesta: establecer_tipo_actividad(estado, respuesta)
    },
    
    "actividad_servicios_NO": {
        "condition": {
            "pregunta_id": "actividad_servicios",
            "respuesta": "NO (Venta de Cosas Muebles)"
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "precio_unitario",
                "texto": "¿El precio unitario de los productos que vas a vender supera los $466,361.15?",
                "opciones": ["SÍ (Supera el límite)", "NO (No supera el límite)"],
                "tipo": "opcion"
            }
        },
        "post_action_func": lambda estado, respuesta: establecer_tipo_actividad(estado, respuesta)
    },
    
    "precio_unitario_excede": {
        "condition": {
            "pregunta_id": "precio_unitario",
            "eval_func": evaluar_precio_unitario_maximo
        },
        "action": {
            "tipo": "resultado",
            "mensaje": """Régimen General (No calificás para el Monotributo)
Según los datos que ingresaste, no cumplís con los requisitos para inscribirte en el régimen simplificado del Monotributo. Deberás tributar bajo el Régimen General.

Importante: Este régimen implica el cumplimiento de obligaciones impositivas más complejas, con presentaciones mensuales y anuales ante ARCA (como IVA y Ganancias).
Para evitar multas, intereses o sanciones por errores u omisiones, se recomienda contar con el acompañamiento de un profesional matriculado, como un contador o contadora de confianza.

Para más información, podés visitar:
https://www.afip.gob.ar/landing/default.asp"""
        }
    },
    
    "precio_unitario_acepta": {
        "condition": {
            "pregunta_id": "precio_unitario",
            "respuesta": "NO (No supera el límite)"
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "genera_ingresos",
                "texto": "¿Ya estás generando ingresos y podés estimar tu facturación anual?",
                "opciones": ["SÍ", "NO"],
                "tipo": "opcion"
            }
        }
    },
    
    "genera_ingresos_SI": {
        "condition": {
            "pregunta_id": "genera_ingresos",
            "respuesta": "SÍ"
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "ingresos_anuales",
                "texto": "Ingresá tu proyección de ingresos brutos anuales (sin puntos ni comas, ejemplo: 10222333)",
                "tipo": "numero"
            }
        }
    },
    
    "genera_ingresos_NO": {
        "condition": {
            "pregunta_id": "genera_ingresos",
            "respuesta": "NO"
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "tiene_local",
                "texto": "¿Tu actividad se desarrolla en un local o establecimiento físico (alquilado o propio)?",
                "opciones": ["SÍ (Tiene local)", "NO (No tiene local)"],
                "tipo": "opcion"
            }
        },
        "post_action_func": lambda estado, respuesta: {**estado, "categoria_actual": "A", "categoria_final": "A"}
    },
    
    "ingresos_exceden_limite": {
        "condition": {
            "pregunta_id": "ingresos_anuales",
            "eval_func": evaluar_ingresos_limite
        },
        "action": {
            "tipo": "resultado",
            "mensaje": "Régimen General (Excede límite de ingresos)"
        }
    },
    
    "ingresos_dentro_limite": {
        "condition": {
            "pregunta_id": "ingresos_anuales",
            "eval_func": lambda estado, respuesta, valor_numerico: not evaluar_ingresos_limite(estado, respuesta, valor_numerico)
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "tiene_local",
                "texto": "¿Tu actividad se desarrolla en un local o establecimiento físico (alquilado o propio)?",
                "opciones": ["SÍ (Tiene local)", "NO (No tiene local)"],
                "tipo": "opcion"
            }
        },
        "post_action_func": lambda estado, valor_numerico: calcular_categoria_por_ingresos(estado, valor_numerico)
    },
    
    "tiene_local_NO": {
        "condition": {
            "pregunta_id": "tiene_local",
            "respuesta": "NO (No tiene local)"
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "relacion_dependencia",
                "texto": "¿Estás en relación de dependencia?",
                "opciones": ["SÍ", "NO"],
                "tipo": "opcion"
            }
        },
        "post_action_func": lambda estado, respuesta: establecer_categoria_final(estado)
    },
    
    "tiene_local_SI": {
        "condition": {
            "pregunta_id": "tiene_local",
            "respuesta": "SÍ (Tiene local)"
        },
        "action": {
            "tipo": "pregunta_superficie",  # Tipo especial para generar pregunta dinámica
            "pregunta_base": "superficie"
        }
    },
    
    "supera_superficie": {
        "condition": {
            "pregunta_pattern": "superficie_cat_",
            "eval_func": lambda estado, respuesta, valor_numerico: evaluar_supera_parametro(estado, respuesta, "superficie")
        },
        "action": {
            "tipo": "avanzar_categoria",
            "parametro": "superficie"
        },
        "post_action_func": lambda estado, respuesta: avanzar_categoria_por_parametro(estado, "superficie")
    },
    
    "no_supera_superficie": {
        "condition": {
            "pregunta_pattern": "superficie_cat_",
            "eval_func": lambda estado, respuesta, valor_numerico: not evaluar_supera_parametro(estado, respuesta, "superficie")
        },
        "action": {
            "tipo": "pregunta_energia",  # Tipo especial para generar pregunta dinámica
            "pregunta_base": "energia"
        }
    },
    
    "supera_energia": {
        "condition": {
            "pregunta_pattern": "energia_cat_",
            "eval_func": lambda estado, respuesta, valor_numerico: evaluar_supera_parametro(estado, respuesta, "energia")
        },
        "action": {
            "tipo": "avanzar_categoria",
            "parametro": "energia"
        },
        "post_action_func": lambda estado, respuesta: avanzar_categoria_por_parametro(estado, "energia")
    },
    
    "no_supera_energia": {
        "condition": {
            "pregunta_pattern": "energia_cat_",
            "eval_func": lambda estado, respuesta, valor_numerico: not evaluar_supera_parametro(estado, respuesta, "energia")
        },
        "action": {
            "tipo": "pregunta_alquileres",  # Tipo especial para generar pregunta dinámica
            "pregunta_base": "alquileres"
        }
    },
    
    "supera_alquileres": {
        "condition": {
            "pregunta_pattern": "alquileres_cat_",
            "eval_func": lambda estado, respuesta, valor_numerico: evaluar_supera_parametro(estado, respuesta, "alquileres")
        },
        "action": {
            "tipo": "avanzar_categoria",
            "parametro": "alquileres"
        },
        "post_action_func": lambda estado, respuesta: avanzar_categoria_por_parametro(estado, "alquileres")
    },
    
    "no_supera_alquileres": {
        "condition": {
            "pregunta_pattern": "alquileres_cat_",
            "eval_func": lambda estado, respuesta, valor_numerico: not evaluar_supera_parametro(estado, respuesta, "alquileres")
        },
        "action": {
            "tipo": "pregunta",
            "pregunta": {
                "id": "relacion_dependencia",
                "texto": "¿Estás en relación de dependencia?",
                "opciones": ["SÍ", "NO"],
                "tipo": "opcion"
            }
        },
        "post_action_func": lambda estado, respuesta: establecer_categoria_final(estado)
    },
    
    "relacion_dependencia_final": {
        "condition": {
            "pregunta_id": "relacion_dependencia"
        },
        "action": {
            "tipo": "resultado_final"
        },
        "post_action_func": lambda estado, respuesta: calcular_pagos_finales(estado, respuesta == "SÍ")
    }
}

# =====================================================================================
# FIN DE LA BASE DE CONOCIMIENTO
# =====================================================================================

# Almacenamiento en memoria de las sesiones
sesiones = {}

# Cargar datos del monotributo al inicio
datos_categorias = None
datos_pagos = None
datos_aref = None

def inicializar_datos():
    global datos_categorias, datos_pagos, datos_aref
    
    # Cargar datos AREF
    current_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(current_dir, 'data', 'aref.json'), 'r') as f:
            datos_aref = json.load(f)
    except Exception as e:
        print(f"Error al cargar aref.json: {e}")
        datos_aref = {}
    
    # Intentar obtener datos actualizados de la web
    datos_web_cat, datos_web_pagos = obtener_datos_monotributo_web()
    
    if datos_web_cat and datos_web_pagos:
        datos_categorias = datos_web_cat
        datos_pagos = datos_web_pagos
        guardar_datos_json_locales(datos_categorias, datos_pagos)
    else:
        # Si falla, intentar cargar datos locales
        datos_local_cat, datos_local_pagos = cargar_datos_json_locales()
        if datos_local_cat and datos_local_pagos:
            datos_categorias = datos_local_cat
            datos_pagos = datos_local_pagos
        else:
            datos_categorias = {"servicios": {}, "venta": {}}
            datos_pagos = {"servicios": {}, "venta": {}}
    
    # Actualizar la pregunta del precio unitario dinámicamente
    try:
        precio_max = datos_categorias["venta"]["A"]["precio_unitario_maximo"]
        knowledge_base["actividad_servicios_NO"]["action"]["pregunta"]["texto"] = f"¿El precio unitario de los productos que vas a vender supera los ${precio_max:,.2f}?"
        print(f"Pregunta de precio unitario actualizada con valor: ${precio_max:,.2f}")
    except Exception as e:
        print(f"Error actualizando pregunta de precio unitario: {e}")

@app.on_event("startup")
async def startup_event():
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
    
    # Verificar coincidencia de pregunta_id
    if "pregunta_id" in condition:
        if respuesta.pregunta_id != condition["pregunta_id"]:
            return False
    
    # Verificar patrón de pregunta (para preguntas dinámicas)
    if "pregunta_pattern" in condition:
        if not respuesta.pregunta_id.startswith(condition["pregunta_pattern"]):
            return False
    
    # Verificar respuesta exacta
    if "respuesta" in condition:
        if respuesta.respuesta != condition["respuesta"]:
            return False
    
    # Evaluar función de evaluación personalizada
    if "eval_func" in condition:
        try:
            return condition["eval_func"](estado, respuesta.respuesta, valor_numerico)
        except Exception as e:
            print(f"Error evaluando función en regla {rule_name}: {e}")
            return False
    
    return True

def generar_pregunta_dinamica(tipo_pregunta, categoria_actual, tipo_actividad):
    """Genera preguntas dinámicas basadas en la categoría actual"""
    try:
        limites = datos_categorias[tipo_actividad][categoria_actual]
        
        if tipo_pregunta == "superficie":
            return {
                "id": f"superficie_cat_{categoria_actual}",
                "texto": f"¿La superficie afectada de tu local supera los {limites['superficie']} m2?",
                "opciones": ["SÍ (Supera el límite)", "NO (No supera el límite / Desconozco)"],
                "tipo": "opcion",
                "categoria_actual": categoria_actual
            }
        elif tipo_pregunta == "energia":
            return {
                "id": f"energia_cat_{categoria_actual}",
                "texto": f"¿El consumo de energía eléctrica supera los {limites['energia']} Kw?",
                "opciones": ["SÍ (Supera el límite)", "NO (No supera el límite / Desconozco)"],
                "tipo": "opcion",
                "categoria_actual": categoria_actual
            }
        elif tipo_pregunta == "alquileres":
            return {
                "id": f"alquileres_cat_{categoria_actual}",
                "texto": f"¿Los alquileres devengados superan los {limites['alquileres']}?",
                "opciones": ["SÍ (Supera el límite)", "NO (No supera el límite / Desconozco)"],
                "tipo": "opcion",
                "categoria_actual": categoria_actual
            }
    except Exception as e:
        print(f"Error generando pregunta dinámica: {e}")
        return None

def ejecutar_accion(rule_name, action, estado, respuesta, valor_numerico=None):
    """Ejecuta la acción asociada a una regla activada"""
    tipo_accion = action["tipo"]
    
    if tipo_accion == "resultado":
        return {
            "tipo": "resultado",
            "mensaje": action["mensaje"],
            "detalles": {
                "razonamiento_aplicado": estado.get("applied_rules", [])
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
        pregunta = generar_pregunta_dinamica("superficie", categoria_actual, tipo_actividad)
        if pregunta:
            return {
                "tipo": "pregunta",
                "pregunta": pregunta
            }
        else:
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
                "mensaje": "Régimen General (Excede límites de parámetros)"
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
                    "mensaje": "Régimen General (Excede límites de parámetros)"
                }
    
    elif tipo_accion == "resultado_final":
        # Generar resultado final con la información calculada
        if "error" in estado:
            return {
                "tipo": "error",
                "mensaje": estado["error"]
            }
        elif "resultado_final" in estado:
            resultado = estado["resultado_final"]
            return {
                "tipo": "resultado",
                "mensaje": f"Te corresponde la Categoría {resultado['categoria']}",
                "detalles": {
                    **resultado,
                    "razonamiento_aplicado": estado.get("applied_rules", [])
                }
            }
        else:
            return {
                "tipo": "error",
                "mensaje": "Error al calcular el resultado final"
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
    print(f"Estado actual: {estado}")
    
    # Manejar pregunta dinámica para precio unitario
    if respuesta.pregunta_id == "precio_unitario":
        try:
            precio_max = datos_categorias["venta"]["A"]["precio_unitario_maximo"]
            # Actualizar la regla dinámicamente
            knowledge_base["actividad_servicios_NO"]["action"]["pregunta"]["texto"] = f"¿El precio unitario de los productos que vas a vender supera los ${precio_max:,.2f}?"
        except:
            pass
    
    # MOTOR DE INFERENCIA: Consultar la Base de Conocimiento
    for rule_name, rule in knowledge_base.items():
        print(f"\nEvaluando regla: {rule_name}")
        
        # Evaluar si la regla se activa
        if evaluar_condicion(rule_name, rule, estado, respuesta, respuesta.valor_numerico):
            print(f"✓ Regla {rule_name} activada")
            
            # Registrar la regla aplicada para explicación
            estado["applied_rules"].append(rule_name)
            
            # Ejecutar post_action_func si existe
            if "post_action_func" in rule:
                try:
                    if respuesta.valor_numerico is not None:
                        estado = rule["post_action_func"](estado, respuesta.valor_numerico)
                    else:
                        estado = rule["post_action_func"](estado, respuesta.respuesta)
                    print(f"Post-acción ejecutada para {rule_name}")
                except Exception as e:
                    print(f"Error ejecutando post-acción en {rule_name}: {e}")
            
            # Ejecutar la acción principal
            resultado = ejecutar_accion(rule_name, rule["action"], estado, respuesta, respuesta.valor_numerico)
            
            if resultado:
                print(f"Resultado generado: {resultado['tipo']}")
                print(f"Reglas aplicadas en esta sesión: {estado.get('applied_rules', [])}")
                return resultado
            else:
                print(f"No se pudo generar resultado para regla {rule_name}")
        else:
            print(f"✗ Regla {rule_name} no activada")
    
    # Si ninguna regla se activó, es un error
    print("ERROR: Ninguna regla se activó")
    raise HTTPException(status_code=400, detail="Pregunta no reconocida o secuencia inválida")

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
    inicializar_datos()
    return {"mensaje": "Datos actualizados correctamente"}

# Montar la carpeta static para archivos estáticos
current_dir = os.path.dirname(os.path.abspath(__file__))
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, 'static')), name="static")

@app.get("/")
def root():
    return FileResponse(os.path.join(current_dir, 'templates', 'index.html'))

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
