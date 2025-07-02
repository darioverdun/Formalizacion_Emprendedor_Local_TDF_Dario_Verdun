# Sistema Experto Emprendedor Fueguino - Monotributo

Sistema experto modular basado en reglas para determinar la categoría de Monotributo correspondiente para emprendedores de Tierra del Fuego, Argentina.

## Estructura Modular del Proyecto

```
SISTEMA EXPERTO EMPRENDEDOR FUEGUINO/
├── api.py                           # API FastAPI principal (ENTRADA)
├── src/                             # Código fuente modular
│   ├── monotributo_scraper.py       # Módulo de scraping AFIP
│   ├── data_manager.py              # Gestión de archivos JSON
│   └── knowledge_base/              # Base de conocimiento
│       └── rules.json               # Reglas del sistema experto
├── data/                            # Datos y hechos del sistema
│   ├── aref.json                    # Datos provinciales AREF
│   ├── categorias.json              # Categorías Monotributo (cache)
│   └── pagos.json                   # Pagos Monotributo (cache)
├── frontend/                        # Interfaz de usuario
│   ├── static/img/                  # Imágenes
│   └── templates/                   # Plantillas HTML
│       └── index.html               # Interfaz web
├── docs/                            # Documentación
│   └── README.md                    # Documentación técnica
├── requirements.txt                 # Dependencias Python
└── README.md                        # Este archivo
```

## Arquitectura Modular

### Módulos Principales

#### `api.py` - API Principal
- **Función**: Punto de entrada de la aplicación web
- **Responsabilidad**: Motor de inferencia, endpoints REST, lógica del sistema experto
- **Dependencias**: Todos los demás módulos

#### `monotributo_data.py` - Gestión Unificada de Datos
- **Función**: Coordina la obtención y gestión de todos los datos
- **Responsabilidad**: Estrategia de datos (web → local → fallback)
- **Características**:
  - Carga inteligente de datos
  - Verificación de integridad
  - Fallback automático
  - Estadísticas del sistema

#### `monotributo_scraper.py` - Scraping Especializado
- **Función**: **CÓDIGO DE SCRAPING PURO**
- **Responsabilidad**: Extracción de datos desde AFIP
- **Características**:
  - Scraping robusto con pandas
  - Limpieza automática de datos
  - Manejo de errores web
  - Testing independiente

#### `data_manager.py` - Gestión de Archivos
- **Función**: Operaciones de archivos JSON locales
- **Responsabilidad**: CRUD de datos locales
- **Características**:
  - Carga/guardado de JSON
  - Metadatos de actualización
  - Verificación de integridad
  - Información de archivos

### Base de Conocimiento Separada

#### `src/knowledge_base/rules.json`
- **Función**: Reglas del sistema experto en formato JSON
- **Ventajas**:
  - Reglas separadas del código
  - Modificación sin recompilación
  - Estructura clara y legible
  - Explicaciones incluidas

## Inicio Rápido

### Método 1: Ejecución Directa (Recomendado)
```bash
# Ejecutar la API principal
python api.py

# La aplicación estará disponible en:
# http://localhost:8000
```

### Método 2: Con uvicorn explícito
```bash
# Usando uvicorn directamente
python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Para desarrollo con auto-reload
python -m uvicorn api:app --reload
```

### Método 3: Módulos Independientes (Testing)
```bash
cd src

# Probar solo el scraping
python monotributo_scraper.py

# Probar gestión de datos
python data_manager.py

# Probar sistema completo de datos (si existe)
python monotributo_data.py
```

## Testing y Verificación

Cada módulo incluye funciones de testing:

```bash
cd src

# Test de scraping
python monotributo_scraper.py

# Test de gestión de datos
python data_manager.py

# Test completo del sistema (si disponible)
python monotributo_data.py
```

## API REST para Desarrolladores

### Punto de Entrada Principal

**Base URL**: `http://localhost:8000` (desarrollo) o tu servidor en producción

**Documentación automática**: `GET /docs` (Swagger UI) y `GET /redoc` (ReDoc)

### Endpoints Disponibles

#### 1. **`POST /iniciar_sesion`** - Iniciar Nueva Sesión
Inicia una nueva sesión del sistema experto y obtiene la primera pregunta.

**Request**:
```http
POST /iniciar_sesion
Content-Type: application/json
```

**Response**:
```json
{
  "sesion_id": "abc123-def456-ghi789",
  "siguiente_pregunta": {
    "id": "persona_juridica",
    "texto": "¿Sos persona jurídica (empresa o sociedad)?",
    "opciones": ["SÍ", "NO (Persona Física)"],
    "tipo": "opcion"
  }
}
```

#### 2. **`POST /responder/{sesion_id}`** - Procesar Respuesta
Envía una respuesta del usuario al motor de inferencia y obtiene la siguiente pregunta o resultado.

**Request**:
```http
POST /responder/abc123-def456-ghi789
Content-Type: application/json

{
  "pregunta_id": "persona_juridica",
  "respuesta": "NO (Persona Física)",
  "valor_numerico": null
}
```

**Response (Siguiente Pregunta)**:
```json
{
  "tipo": "pregunta",
  "pregunta": {
    "id": "actividad_servicios",
    "texto": "¿Tu actividad principal es la prestación de servicios?",
    "opciones": ["SÍ (Prestación de servicios)", "NO (Venta de productos)"],
    "tipo": "opcion"
  }
}
```

**Response (Resultado Final)**:
```json
{
  "tipo": "resultado",
  "mensaje": "Te corresponde la Categoría B",
  "detalles": {
    "categoria": "B",
    "tipo_actividad": "servicios",
    "pagos_nacionales": {
      "impuesto": "15000.00",
      "sipa": "8500.00",
      "obra_social": "3200.00"
    },
    "pagos_provinciales": {
      "aref": "2500.00"
    },
    "total_nacional": 26700.00,
    "total_provincial": 2500.00,
    "total_general": 29200.00,
    "en_relacion_dependencia": false,
    "razonamiento_aplicado": [
      {
        "regla": "actividad_servicios_SI",
        "descripcion": "Establece tipo de actividad como servicios",
        "explicacion": "Como respondiste que tu actividad principal es prestación de servicios, se determina que perteneces al régimen de servicios del Monotributo.",
        "tipo": "activada"
      }
    ]
  }
}
```

#### 3. **`GET /info_sistema`** - Estado del Sistema
Obtiene información completa sobre el estado del sistema experto.

**Response**:
```json
{
  "reglas_cargadas": 25,
  "reglas_disponibles": ["persona_juridica_SI", "actividad_servicios_SI", "..."],
  "datos_categorias_disponibles": true,
  "datos_pagos_disponibles": true,
  "datos_aref_disponibles": true,
  "sistema": "Sistema Experto Monotributo v2.0 - Modular"
}
```

#### 4. **`GET /actualizar_datos`** - Actualizar Datos
Fuerza la actualización de datos desde AFIP.

#### 5. **`GET /reiniciar/{sesion_id}`** - Reiniciar Sesión
Reinicia una sesión existente y devuelve nueva sesión con primera pregunta.

#### 6. **`GET /`** - Interfaz Web
Sirve la interfaz web HTML para uso interactivo.

### Integración Completa - Ejemplos de Código

#### Python (requests)
```python
import requests

class SistemaExpertoClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.sesion_id = None
        
    def iniciar_sesion(self):
        """Inicia una nueva sesión"""
        response = requests.post(f"{self.base_url}/iniciar_sesion")
        data = response.json()
        self.sesion_id = data["sesion_id"]
        return data["siguiente_pregunta"]
    
    def responder(self, pregunta_id, respuesta, valor_numerico=None):
        """Envía una respuesta al sistema experto"""
        if not self.sesion_id:
            raise Exception("Debe iniciar sesión primero")
            
        payload = {
            "pregunta_id": pregunta_id,
            "respuesta": respuesta,
            "valor_numerico": valor_numerico
        }
        
        response = requests.post(
            f"{self.base_url}/responder/{self.sesion_id}", 
            json=payload
        )
        return response.json()
    
    def consulta_completa_automatica(self, respuestas_predefinidas):
        """Ejecuta una consulta completa con respuestas predefinidas"""
        pregunta = self.iniciar_sesion()
        
        for respuesta_data in respuestas_predefinidas:
            if pregunta["id"] == respuesta_data["pregunta_id"]:
                resultado = self.responder(
                    pregunta["id"], 
                    respuesta_data["respuesta"],
                    respuesta_data.get("valor_numerico")
                )
                
                if resultado["tipo"] == "resultado":
                    return resultado
                elif resultado["tipo"] == "pregunta":
                    pregunta = resultado["pregunta"]
                else:
                    raise Exception(f"Error: {resultado}")
        
        return None

# Ejemplo de uso
cliente = SistemaExpertoClient()

# Respuestas de ejemplo para un emprendedor de servicios
respuestas = [
    {"pregunta_id": "persona_juridica", "respuesta": "NO (Persona Física)"},
    {"pregunta_id": "actividad_servicios", "respuesta": "SÍ (Prestación de servicios)"},
    {"pregunta_id": "ingresos_anuales", "respuesta": "Con ingresos", "valor_numerico": 2500000},
    {"pregunta_id": "superficie_cat_B", "respuesta": "NO (No supera el límite / Desconozco)"},
    {"pregunta_id": "energia_cat_B", "respuesta": "NO (No supera el límite / Desconozco)"},
    {"pregunta_id": "alquileres_cat_B", "respuesta": "NO (No supera el límite / Desconozco)"},
    {"pregunta_id": "relacion_dependencia", "respuesta": "NO (Solo actividad independiente)"}
]

resultado = cliente.consulta_completa_automatica(respuestas)
print(f"Categoría: {resultado['detalles']['categoria']}")
print(f"Total a pagar: ${resultado['detalles']['total_general']}")
```

#### JavaScript (Node.js/Browser)
```javascript
class SistemaExpertoClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.sesionId = null;
    }
    
    async iniciarSesion() {
        const response = await fetch(`${this.baseUrl}/iniciar_sesion`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        this.sesionId = data.sesion_id;
        return data.siguiente_pregunta;
    }
    
    async responder(preguntaId, respuesta, valorNumerico = null) {
        if (!this.sesionId) throw new Error('Debe iniciar sesión primero');
        
        const response = await fetch(`${this.baseUrl}/responder/${this.sesionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                pregunta_id: preguntaId,
                respuesta: respuesta,
                valor_numerico: valorNumerico
            })
        });
        
        return await response.json();
    }
    
    async consultaCompleta(respuestasPredefinidas) {
        let pregunta = await this.iniciarSesion();
        
        for (const respuestaData of respuestasPredefinidas) {
            if (pregunta.id === respuestaData.pregunta_id) {
                const resultado = await this.responder(
                    pregunta.id, 
                    respuestaData.respuesta,
                    respuestaData.valor_numerico
                );
                
                if (resultado.tipo === 'resultado') {
                    return resultado;
                } else if (resultado.tipo === 'pregunta') {
                    pregunta = resultado.pregunta;
                } else {
                    throw new Error(`Error: ${JSON.stringify(resultado)}`);
                }
            }
        }
        
        return null;
    }
}

// Ejemplo de uso
const cliente = new SistemaExpertoClient();

// Uso con async/await
(async () => {
    try {
        const respuestas = [
            { pregunta_id: "persona_juridica", respuesta: "NO (Persona Física)" },
            { pregunta_id: "actividad_servicios", respuesta: "SÍ (Prestación de servicios)" },
            { pregunta_id: "ingresos_anuales", respuesta: "Con ingresos", valor_numerico: 2500000 }
            // ... más respuestas
        ];
        
        const resultado = await cliente.consultaCompleta(respuestas);
        console.log(`Categoría: ${resultado.detalles.categoria}`);
        console.log(`Total: $${resultado.detalles.total_general}`);
    } catch (error) {
        console.error('Error:', error);
    }
})();
```

#### cURL (Terminal/Scripts)
```bash
# 1. Iniciar sesión
curl -X POST http://localhost:8000/iniciar_sesion \
  -H "Content-Type: application/json"

# 2. Responder primera pregunta
curl -X POST http://localhost:8000/responder/SESSION_ID \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta_id": "persona_juridica",
    "respuesta": "NO (Persona Física)",
    "valor_numerico": null
  }'

# 3. Obtener información del sistema
curl http://localhost:8000/info_sistema
```

### Estructura de Datos

#### Tipos de Preguntas
- **`"opcion"`**: Pregunta de múltiple opción con opciones predefinidas
- **`"numerica"`**: Pregunta que requiere un valor numérico

#### Tipos de Respuesta
- **`"pregunta"`**: El sistema devuelve la siguiente pregunta
- **`"resultado"`**: El sistema devuelve el resultado final
- **`"error"`**: Error en el procesamiento

#### Estructura del Razonamiento
Cada resultado incluye `razonamiento_aplicado` con:
- **`regla`**: Nombre técnico de la regla aplicada
- **`descripcion`**: Descripción técnica de la regla
- **`explicacion`**: Explicación en lenguaje natural para el usuario
- **`tipo`**: Tipo de regla ("activada" o "heredada")

### Manejo de Errores

#### Códigos de Estado HTTP
- **`200`**: Operación exitosa
- **`400`**: Datos inválidos o secuencia incorrecta
- **`404`**: Sesión no encontrada
- **`500`**: Error interno del servidor

#### Ejemplo de Error
```json
{
  "detail": "Sesión no encontrada"
}
```

### Flujo de Integración Recomendado

1. **Iniciar sesión** → Obtener `sesion_id` y primera pregunta
2. **Bucle de preguntas**:
   - Mostrar pregunta al usuario
   - Enviar respuesta al sistema
   - Si `tipo == "pregunta"` → continuar bucle
   - Si `tipo == "resultado"` → procesar resultado final
   - Si `tipo == "error"` → manejar error
3. **Procesar resultado** → Extraer categoría, pagos y razonamiento

### Testing y Desarrollo

```bash
# Verificar que el sistema está funcionando
curl http://localhost:8000/info_sistema

# Probar flujo completo con datos de prueba
curl -X POST http://localhost:8000/iniciar_sesion | jq
```

### Casos de Uso Comunes

1. **Calculadora de Monotributo**: Integrar en formularios web
2. **Chatbots**: Usar las explicaciones del razonamiento
3. **Sistemas de gestión**: Automatizar cálculos para clientes
4. **Apps móviles**: Consumir API REST desde aplicaciones
5. **Servicios empresariales**: Integrar en plataformas de contabilidad

## Flujo de Datos

```mermaid
graph TD
    A[Inicio] --> B[monotributo_data.py]
    B --> C{Datos web disponibles?}
    C -->|Sí| D[monotributo_scraper.py]
    C -->|No| E[data_manager.py]
    D --> F[Verificar integridad]
    E --> F
    F --> G{Datos válidos?}
    G -->|Sí| H[api.py - Sistema listo]
    G -->|No| I[Usar datos por defecto]
    I --> H
```

## **Limpieza de Archivos Completada**

### **Archivos Eliminados** (Julio 2025)

Durante la reorganización se eliminaron los siguientes archivos innecesarios:

- `src/api.py` - **Duplicado obsoleto** (versión con `monotributo_data.py`)
- `src/monotributo_data.py` - **Módulo obsoleto** (reemplazado por módulos separados)
- `src/console_interface.py` - **No utilizado** (API web no requiere interfaz de consola)
- `test_github.txt` - **Archivo de prueba** 
- `__pycache__/` (varias carpetas) - **Archivos temporales de Python**
- `tests/` (carpeta vacía) - **Sin contenido**

### **Estructura Final Optimizada**

```
SISTEMA EXPERTO EMPRENDEDOR FUEGUINO/
├── api.py                           # API Principal (FastAPI)
├── src/                             # Módulos especializados
│   ├── monotributo_scraper.py       # Scraping de AFIP
│   ├── data_manager.py              # Gestión de datos locales
│   ├── monotributo_data.py          # Módulo unificado de datos
│   └── knowledge_base/              # Base de conocimiento
│       └── rules.json               # Reglas del sistema experto
├── data/                            # Datos del sistema
├── frontend/                        # Interfaz web
├── docs/                            # Documentación
├── requirements.txt                 # Dependencias Python
└── README.md                        # Este archivo
```

## Refactorización Pendiente

### Módulo Legacy: `sistema_experto_legacy_monolitico.py`

**Estado**: Obsoleto - Reemplazado por arquitectura modular

El archivo `sistema_experto_legacy_monolitico.py` (renombrado desde `sistema_experto_5_cop_json.py`) contiene la **implementación monolítica original** con todas las funcionalidades integradas:

- **Scraping de datos** de AFIP con pandas
- **Gestión de archivos JSON** locales  
- **Sistema experto por consola** con lógica de preguntas/respuestas
- **Interfaz de línea de comandos** completa

**Migración Completada**: Las funcionalidades han sido separadas en módulos especializados:

```python
# ANTES (legacy):
from sistema_experto_5_cop_json import (
    obtener_datos_monotributo_web,
    cargar_datos_json_locales,
    guardar_datos_json_locales
)

# AHORA (modular):
from monotributo_scraper import obtener_datos_monotributo_web
from data_manager import cargar_datos_json_locales, guardar_datos_json_locales
```

**Recomendación**: El archivo legacy puede ser eliminado una vez confirmada la migración total.

**Refactorización necesaria**: Estas funciones ya están implementadas en los nuevos módulos modulares:
- `monotributo_scraper.py` → `obtener_datos_monotributo_web()`
- `data_manager.py` → `cargar_datos_json_locales()` y `guardar_datos_json_locales()`

**Acción recomendada**: Actualizar `api.py` para usar los nuevos módulos modulares.

## Características Clave

### Modularidad
- Separación clara de responsabilidades
- Módulos independientes y testables
- Fácil mantenimiento y extensión

### Scraping Robusto
- Extracción automatizada desde AFIP
- Manejo de estructuras complejas
- Limpieza inteligente de datos

### Gestión Inteligente de Datos
- Estrategia de fallback automática
- Verificación de integridad
- Cache local con metadatos

### Sistema Experto Avanzado
- Reglas separadas en JSON
- Explicaciones detalladas
- Motor de inferencia robusto

## Desarrollo

### Agregar Nuevas Reglas
Edita `src/knowledge_base/rules.json`:
```json
{
  "nueva_regla": {
    "condition": {...},
    "action": {...},
    "description": "Descripción de la regla",
    "explanation": "Explicación para el usuario"
  }
}
```

### Extender el Scraping
Modifica `src/monotributo_scraper.py` para agregar nuevos sitios o datos.

### Personalizar Datos
Agrega nuevos archivos JSON en la carpeta `data/`.

## Monitoreo

El sistema incluye endpoints de monitoreo:
- `/info_sistema` - Estado completo
- `/actualizar_datos` - Actualización manual
- Logs detallados en consola

## Licencia

Proyecto académico - Tecnicatura en Desarrollo de Sistemas de IA

---

## Conclusión

Esta refactorización logra:
- **Separación del scraping** en módulos independientes
- **Modularidad completa** del sistema
- **Base de conocimiento separada** del código
- **Explicaciones mejoradas** del razonamiento
- **Testing independiente** de cada módulo
- **Compatibilidad mantenida** con funcionalidad existente
- **API REST completamente documentada** para desarrolladores
- **Ejemplos de integración** en múltiples lenguajes
- **Arquitectura modular profesional** lista para producción

El sistema ahora es **más mantenible, escalable y profesional**, con **documentación completa para desarrolladores externos**.

## Próximos Pasos

### Mejoras Técnicas Sugeridas
1. **Autenticación API**: Implementar tokens de acceso para uso empresarial
2. **Rate Limiting**: Limitar requests por IP/usuario
3. **Persistencia de Sesiones**: Usar Redis o base de datos para sesiones
4. **Logging Avanzado**: Implementar logging estructurado con niveles
5. **Tests Automatizados**: Crear suite completa de tests unitarios e integración
6. **Documentación OpenAPI**: Expandir documentación automática con más ejemplos
7. **Webhooks**: Notificaciones automáticas cuando cambian los datos de AFIP
8. **Versionado API**: Implementar versionado para cambios futuros
9. **Métricas**: Agregar endpoints de métricas para monitoring
10. **Docker Compose**: Configuración completa para desarrollo y producción

### Casos de Uso Avanzados
- **Integración con sistemas contables** (Tango, Bejerman, etc.)
- **Chatbots de WhatsApp/Telegram** que usen el sistema experto
- **Aplicaciones móviles** para emprendedores
- **Plugins para e-commerce** (Shopify, WooCommerce, etc.)
- **Servicios de consultoría automatizada**

---

**Desarrollado por**: Tecnicatura en Desarrollo de Sistemas de IA  
**Licencia**: Proyecto Académico  
**Contacto**: Para consultas sobre integración y desarrollo