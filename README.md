# Sistema Experto para la Formalización de Emprendedores en Tierra del Fuego

## 🚀 ÚLTIMA ACTUALIZACIÓN: DEPLOYMENT FORZADO PARA RENDER - 29/06/2025 ✅

## Materia  
Desarrollo de Sistemas de Inteligencia Artificial  

**Profesor:** Martín Mirabete  
**Alumno:** Dario Emmanuel Verdun  
**Experto entrevistado:** Contador Público Nacional matriculado  

---

## Título del dominio  
Formalización del emprendedor local en Tierra del Fuego

---

## Objetivo del proyecto

Este proyecto tiene como finalidad el desarrollo de un sistema experto que brinde orientación a emprendedores en el proceso de formalización de sus actividades económicas. Mediante un enfoque basado en reglas, el sistema simula el conocimiento de un profesional en ciencias económicas, ayudando a los usuarios a identificar el régimen fiscal más adecuado según sus características individuales, actividad económica, ingresos estimados y otras variables clave.

El sistema actúa como una herramienta de apoyo al asesoramiento, permitiendo a los emprendedores comprender sus obligaciones fiscales y los pasos necesarios para regularizar su situación.

---

## Arquitectura del Sistema Experto

### Componentes Principales (Basado en la Clase 3 - Sistemas Expertos)

#### 1. **Base de Conocimiento (Knowledge Base)**
- **Ubicación en código:** Variable global `knowledge_base` 
- **Estructura:** Diccionario de reglas con formato estandarizado
- **Contenido:** 20+ reglas que representan el conocimiento del dominio fiscal
- **Formato de reglas:**
  ```python
  "nombre_regla": {
      "condition": {
          "pregunta_id": "identificador",
          "respuesta": "valor_esperado",
          "eval_func": función_evaluación_opcional
      },
      "action": {
          "tipo": "pregunta|resultado|resultado_final",
          "pregunta": objeto_pregunta_opcional,
          "mensaje": mensaje_resultado_opcional
      },
      "post_action_func": función_post_proceso_opcional
  }
  ```

#### 2. **Motor de Inferencia (Inference Engine)**
- **Ubicación en código:** Función `procesar_respuesta()`
- **Funcionalidad:** 
  - Consulta la Base de Conocimiento para encontrar reglas aplicables
  - Evalúa condiciones complejas mediante funciones auxiliares
  - Ejecuta acciones y post-acciones según las reglas activadas
  - Mantiene el control del flujo de razonamiento

#### 3. **Memoria de Trabajo (Working Memory)**
- **Ubicación en código:** Variable `sesiones[sesion_id]`
- **Contenido:**
  - Estado actual de la sesión
  - Respuestas del usuario
  - Variables intermedias (categoría, tipo de actividad, etc.)
  - **Lista de reglas aplicadas** (`applied_rules`) para explicación

#### 4. **Capacidad de Explicación**
- **Implementación:** Campo `applied_rules` en cada sesión
- **Funcionalidad:** Registro de todas las reglas que se "dispararon" durante el proceso
- **Presentación:** Incluido en el resultado final como `razonamiento_aplicado`
- **Visualización:** Mostrado tanto en casos exitosos como negativos
- **Interfaz:** Badges visuales en el frontend que muestran las reglas aplicadas

#### 5. **Interfaz de Usuario**
- **Frontend:** Archivo HTML con JavaScript (`templates/index.html`)
- **Diseño:** Sistema experto moderno con panel lateral de componentes
- **Características visuales:**
  - Estados en tiempo real de los 4 componentes del sistema experto
  - Bandera de Tierra del Fuego como fondo temático
  - Chat interactivo con mensajes diferenciados
  - Badges de reglas aplicadas en los resultados
  - Diseño responsive y profesional
- **API REST:** Endpoints FastAPI para comunicación
- **Endpoints principales:**
  - `POST /iniciar_sesion` - Inicia nueva consulta
  - `POST /responder/{sesion_id}` - Procesa respuestas del usuario
  - `GET /reiniciar/{sesion_id}` - Reinicia sesión
  - `GET /actualizar_datos` - Actualiza datos fiscales

### Funciones Auxiliares del Sistema Experto

#### Evaluación de Condiciones Complejas:
- `evaluar_precio_unitario_maximo()` - Verifica límites de precio para venta
- `evaluar_ingresos_limite()` - Verifica si los ingresos exceden límites permitidos
- `evaluar_supera_parametro()` - Evalúa parámetros de superficie, energía, alquileres

#### Cálculos y Post-Acciones:
- `establecer_tipo_actividad()` - Define si es servicios o venta
- `calcular_categoria_por_ingresos()` - Determina categoría por ingresos
- `avanzar_categoria_por_parametro()` - Avanza categorías por límites de parámetros
- `calcular_pagos_finales()` - Calcula pagos nacionales y provinciales

---

## Contexto del problema

Muchos emprendedores comienzan su actividad de manera informal debido a la falta de información clara sobre los trámites requeridos y los organismos involucrados. Esta informalidad puede limitar su acceso a créditos, generar sanciones involuntarias y dificultar su crecimiento a largo plazo.

Este proyecto busca aportar una solución a esta problemática a través de una herramienta automatizada y accesible.

---

## Relevancia

La implementación de este sistema puede generar un impacto positivo en distintos aspectos:

- Mejora el acceso a información contable y fiscal confiable.
- Reduce errores comunes en la elección del régimen tributario.
- Favorece la inclusión de nuevos emprendimientos en el sistema formal.
- Contribuye al desarrollo económico local mediante la regularización de actividades.

---

## Aporte del Sistema Experto

- Asesoramiento tributario personalizado a través de preguntas y respuestas.
- Simulación del razonamiento de un contador público.
- Sugerencias sobre trámites ante organismos nacionales y provinciales.
- Advertencias sobre incompatibilidades con planes sociales o situaciones laborales.
- Mejora del cumplimiento fiscal inicial y prevención de errores frecuentes.
- **Capacidad de explicación:** El sistema puede mostrar qué reglas se aplicaron durante el proceso de razonamiento tanto en casos exitosos como negativos.
- **Interfaz moderna:** Diseño visual que refleja la arquitectura académica del sistema experto con estados en tiempo real.
- **Actualización automática:** Obtiene datos fiscales actualizados mediante web scraping de AFIP.

---

## Representación y Organización del Conocimiento

La estructura del conocimiento se basa en **reglas de producción (si-entonces)**, organizadas modularmente por jurisdicción (nacional y provincial).

### Hechos considerados

- Tipo de persona (física o jurídica)
- Actividad económica
- Ingresos anuales estimados
- Domicilio fiscal
- Situación laboral (relación de dependencia, autónomo)
- Inscripciones previas
- Condición social (beneficios o subsidios)
- Actividades de comercio exterior

### Reglas de ejemplo

SI la persona es física
Y los ingresos son menores al límite del régimen simplificado
ENTONCES sugerir inscripción en el régimen simplificado

SI la persona es jurídica
ENTONCES excluir del régimen simplificado y sugerir régimen general

SI el usuario recibe ayuda social
ENTONCES advertir sobre posibles incompatibilidades


---

## Criterios de Decisión

- Límite de ingresos
- Tipo de actividad (permitida o excluida del régimen simplificado)
- Jurisdicción fiscal (local o multilateral)
- Situación laboral y condición social
- Actividades de importación/exportación
- Ente otros

---

## Estructura del Conocimiento

### Módulo Nacional

- Monotributo vs Régimen General
- Exclusiones del Monotributo
- Obligaciones nacionales: IVA, Ganancias

### Módulo Provincial

- Inscripción en Ingresos Brutos
- Régimen Simplificado vs General
- Convenio Multilateral si corresponde

---

## Método de Inferencia

Se utilizará **encadenamiento hacia adelante**, permitiendo que el sistema evalúe automáticamente los datos proporcionados por el usuario y aplique las reglas correspondientes en cascada, generando una recomendación precisa y personalizada.

---

## Arquitectura del Sistema

- **Base de Conocimiento**: reglas y hechos generales
- **Base de Hechos**: datos ingresados por el usuario
- **Motor de Inferencia**: evalúa condiciones y aplica reglas
- **Interfaz de Usuario**: facilita la interacción con el sistema

---

## 🛠️ Guía de Instalación y Configuración

### Requisitos Previos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Navegador web moderno

### Estructura de Archivos

```
/
├── data/               # Archivos JSON con datos del sistema
│   ├── aref.json      # Datos de AREF (actualizados)
│   ├── categorias.json # Categorías del monotributo (web scraping)
│   └── pagos.json     # Información de pagos (web scraping)
├── static/            # Archivos estáticos
│   └── img/          # Imágenes del sistema
│       └── Bandera_de_la_Provincia_de_Tierra_del_Fuego.svg.png
├── templates/         # Plantillas HTML
│   └── index.html    # Interfaz principal (rediseñada)
├── api.py            # API principal con sistema experto refactorizado
├── sistema_experto_5_cop_json.py  # Módulo de web scraping
├── requirements.txt   # Dependencias del proyecto (actualizadas)
├── Procfile          # Configuración para deployment en la web
├── runtime.txt       # Versión de Python para deployment
├── .gitignore        # Archivos ignorados por Git
└── README.md         # Documentación completa
```

### Pasos de Instalación

1. Clonar el repositorio:
```bash
git clone [URL del repositorio]
cd [nombre del repositorio]
```

2. Crear y activar un entorno virtual:
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate
```

3. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

### Ejecución del Sistema

1. Iniciar el servidor:
```bash
# Opción 1: Usando uvicorn directamente
uvicorn api:app --host 0.0.0.0 --port 8000

# Opción 2: Ejecutando el archivo api.py
python api.py
```

2. Abrir el navegador y acceder a:
```
http://localhost:8000
```

### Características del Sistema en Funcionamiento

- **Datos actualizados:** Al iniciar, el sistema descarga automáticamente las categorías y límites más recientes desde AFIP
- **Precios dinámicos:** Las preguntas incluyen valores actualizados (ej: precio unitario máximo $466,361.15)
- **Explicación en tiempo real:** Visualización de reglas aplicadas en el panel lateral
- **Estados de componentes:** Monitor visual del estado de la Base de Conocimiento, Motor de Inferencia, Memoria de Trabajo y Capacidad de Explicación

### Actualización de Datos

El sistema puede actualizar automáticamente los datos de categorías y pagos:
- Acceder a `/actualizar_datos` en la API
- Los datos se guardarán en los archivos JSON correspondientes

---

## 🌐 Deployment en la Web

### Plataformas Compatibles

El sistema está configurado para deploy automático en:

- **Railway** (Recomendado): Deploy directo desde GitHub
- **Render**: Tier gratuito con buena performance
- **Heroku**: Plataforma clásica con tier gratuito
- **Vercel**: Para aplicaciones estáticas (requiere configuración adicional)

### Archivos de Deployment Incluidos

- `Procfile`: Configuración para ejecutar el servidor web
- `runtime.txt`: Especifica la versión de Python (3.11.0)
- `requirements.txt`: Dependencias actualizadas y optimizadas
- `api.py`: Incluye punto de entrada para ejecución directa

### Pasos para Deploy en Railway/Render

1. **Subir código a GitHub**:
```bash
git add .
git commit -m "Sistema experto completo con deployment config"
git push origin main
```

2. **Conectar repositorio**:
   - Ir a Railway.app o Render.com
   - Conectar cuenta de GitHub
   - Seleccionar el repositorio

3. **Deploy automático**:
   - La plataforma detectará automáticamente `Procfile`
   - Instalará dependencias desde `requirements.txt`
   - Iniciará el servidor web

### Variables de Entorno (Opcional)

Si necesitas configurar variables de entorno:
- `PORT`: Puerto del servidor (automático en la mayoría de plataformas)
- `PYTHON_VERSION`: Versión de Python (especificado en runtime.txt)

### URL de Acceso

Una vez deployado, tu sistema experto estará disponible en:
- Railway: `https://tu-proyecto.railway.app`
- Render: `https://tu-proyecto.onrender.com`
- Heroku: `https://tu-app.herokuapp.com`

### Documentación Adicional

Para más detalles sobre el funcionamiento del sistema, consultar:
- `arbol de decision/Arbol_Nacional_Arca_Categorización_Emprendedor_Completo.pdf`
- `arbol de decision/Arbol_Nacional_Arca_Categorización_Emprendedor_Simplificado.pdf`

---

## Conclusión

Este sistema experto combina inteligencia artificial y conocimiento contable para brindar una herramienta útil y accesible. Su objetivo es reducir la informalidad, promover el cumplimiento fiscal y apoyar el desarrollo de pequeños emprendimientos, especialmente en contextos donde el asesoramiento profesional no está siempre al alcance de todos.

#   D E P L O Y M E N T   F O R Z A D O   2 0 2 5 - 0 6 - 2 9   0 0 : 0 5 : 3 3 
