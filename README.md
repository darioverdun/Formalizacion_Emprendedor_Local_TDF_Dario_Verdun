# Sistema Experto para la Formalización de Emprendedores en Tierra del Fuego



## Materia  
Desarrollo de Sistemas de Inteligencia Artificial  

Profesor: Martín Mirabete  
Alumno: Dario Emmanuel Verdun  
Experto entrevistado: Contador Público Nacional matriculado  

---

## Título del dominio  
Formalización del emprendedor local en Tierra del Fuego

---

## Objetivo del proyecto

Este proyecto tiene como finalidad el desarrollo de un sistema experto que brinde orientación a emprendedores en el proceso de formalización de sus actividades económicas. Mediante un enfoque basado en reglas, el sistema simula el conocimiento de un profesional en ciencias económicas, ayudando a los usuarios a identificar el régimen fiscal más adecuado según sus características individuales, actividad económica, ingresos estimados y otras variables clave.

El sistema actúa como una herramienta de apoyo al asesoramiento, permitiendo a los emprendedores comprender sus obligaciones fiscales y los pasos necesarios para regularizar su situación.

---

## Arquitectura del Sistema Experto

### Componentes Principales

#### 1. Base de Conocimiento (Knowledge Base)
- Ubicación en código: variable global `knowledge_base` 
- Estructura: diccionario de reglas con formato estandarizado
- Contenido: más de 20 reglas que representan el conocimiento del dominio fiscal
- Formato de reglas:
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

#### 2. Motor de Inferencia (Inference Engine)
- Ubicación en código: función `procesar_respuesta()`
- Funcionalidad:
  - Consulta la base de conocimiento
  - Evalúa condiciones mediante funciones auxiliares
  - Ejecuta acciones y post-acciones
  - Controla el flujo del razonamiento

#### 3. Memoria de Trabajo (Working Memory)
- Ubicación en código: variable `sesiones[sesion_id]`
- Contiene:
  - Estado actual de la sesión
  - Respuestas del usuario
  - Variables intermedias (categoría, tipo de actividad, etc.)
  - Lista de reglas aplicadas (`applied_rules`)

#### 4. Capacidad de Explicación
- Implementación: campo `applied_rules` en cada sesión
- Funcionalidad: registra todas las reglas activadas
- Presentación: incluida en el resultado final
- Visualización: disponible tanto en casos exitosos como negativos

#### 5. Interfaz de Usuario
- Frontend: archivo HTML con JavaScript (`templates/index.html`)
- Diseño:
  - Chat interactivo
  - Panel lateral con estados en tiempo real
  - Diseño responsive
  - Fondo temático con bandera de Tierra del Fuego
- API REST (FastAPI):
  - `POST /iniciar_sesion`
  - `POST /responder/{sesion_id}`
  - `GET /reiniciar/{sesion_id}`
  - `GET /actualizar_datos`

---

## Funciones Auxiliares

### Evaluación de Condiciones Complejas
- `evaluar_precio_unitario_maximo()`
- `evaluar_ingresos_limite()`
- `evaluar_supera_parametro()`

### Cálculos y Post-Acciones
- `establecer_tipo_actividad()`
- `calcular_categoria_por_ingresos()`
- `avanzar_categoria_por_parametro()`
- `calcular_pagos_finales()`

---

## Contexto del problema

Muchos emprendedores comienzan su actividad de manera informal debido a la falta de información clara sobre los trámites requeridos y los organismos involucrados. Esta informalidad puede limitar su acceso a créditos, generar sanciones involuntarias y dificultar su crecimiento a largo plazo.

Este proyecto busca aportar una solución a esta problemática a través de una herramienta automatizada y accesible.

---

## Relevancia

- Mejora el acceso a información contable y fiscal confiable
- Reduce errores comunes en la elección del régimen tributario
- Favorece la inclusión de nuevos emprendimientos en el sistema formal
- Contribuye al desarrollo económico local

---

## Aporte del Sistema Experto

- Asesoramiento tributario personalizado
- Simulación del razonamiento de un contador público
- Sugerencias sobre trámites nacionales y provinciales
- Advertencias sobre incompatibilidades sociales o laborales
- Mejora del cumplimiento fiscal inicial
- Capacidad de explicación: muestra qué reglas se aplicaron
- Interfaz moderna con estados en tiempo real
- Actualización automática de datos fiscales (web scraping AFIP)

---

## Representación y Organización del Conocimiento

La estructura del conocimiento se basa en reglas de producción (si-entonces), organizadas por jurisdicción.

### Hechos considerados

- Tipo de persona (física o jurídica)
- Actividad económica
- Ingresos anuales estimados
- Domicilio fiscal
- Situación laboral
- Inscripciones previas
- Condición social
- Comercio exterior

### Reglas de ejemplo

Si la persona es física  
Y los ingresos son menores al límite del régimen simplificado  
Entonces sugerir inscripción en el régimen simplificado

Si la persona es jurídica  
Entonces excluir del régimen simplificado y sugerir régimen general

Si el usuario recibe ayuda social  
Entonces advertir sobre posibles incompatibilidades

---

## Criterios de Decisión

- Límite de ingresos
- Tipo de actividad
- Jurisdicción fiscal
- Situación laboral y condición social
- Actividades de importación/exportación

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

Se utiliza encadenamiento hacia adelante: el sistema evalúa automáticamente los datos del usuario y aplica las reglas correspondientes en cascada, generando una recomendación precisa y personalizada.

---

## Arquitectura del Sistema

- Base de Conocimiento: reglas y hechos generales
- Base de Hechos: datos ingresados por el usuario
- Motor de Inferencia: evalúa condiciones y aplica reglas
- Interfaz de Usuario: facilita la interacción

---

## Guía de Instalación y Configuración

### Requisitos Previos
- Python 3.10 o superior
- pip
- Navegador web moderno

### Estructura de Archivos
```
/
├── data/
│   ├── aref.json
│   ├── categorias.json
│   └── pagos.json
├── static/
│   └── img/
│       └── Bandera_de_la_Provincia_de_Tierra_del_Fuego.svg.png
├── templates/
│   └── index.html
├── api.py
├── sistema_experto_5_cop_json.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── .gitignore
└── README.md
```

### Instalación
```bash
git clone [URL]
cd [nombre]
python -m venv venv
# En Windows
venv\Scripts\activate
# En Linux/Mac
source venv/bin/activate
pip install -r requirements.txt
```

### Ejecución
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
# o
python api.py
```

Ir a `http://localhost:8000`

---

## Actualización de Datos

Visitar `/actualizar_datos` en la API. Los datos se guardan automáticamente.

---

## Deployment en la Web

### Plataformas Compatibles
- Railway
- Render
- Heroku
- Vercel (requiere ajuste)

### Archivos
- `Procfile`
- `runtime.txt`
- `requirements.txt`
- `api.py`

### Deploy
```bash
git add .
git commit -m "Deploy"
git push origin main
```

Conectar el repositorio a Railway o Render. El deploy se hace automáticamente.

### Variables de Entorno
- `PORT`
- `PYTHON_VERSION`

### URL
- Railway: `https://tu-proyecto.railway.app`
- Render: `https://tu-proyecto.onrender.com`
- Heroku: `https://tu-app.herokuapp.com`

---

## Documentación Adicional

- arbol de decision/Arbol_Nacional_Arca_Categorización_Emprendedor_Completo.pdf
- arbol de decision/Arbol_Nacional_Arca_Categorización_Emprendedor_Simplificado.pdf

---

## Conclusión

Este sistema experto combina inteligencia artificial y conocimiento contable para brindar una herramienta útil y accesible. Su objetivo es reducir la informalidad, promover el cumplimiento fiscal y apoyar el desarrollo de pequeños emprendimientos.


