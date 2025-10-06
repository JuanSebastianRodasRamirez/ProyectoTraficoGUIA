# Extractor de Tráfico (ProyectoTraficoGUIA)

Descripción
-----------

Este proyecto contiene una utilidad en Python llamada `ExtractorTraficoLegal.py` que extrae y analiza información de la red vial de una ciudad usando fuentes libres y legales (principalmente OpenStreetMap via OSMnx). El script realiza los siguientes pasos:

- Descarga la red vial (calles e intersecciones) de una ciudad.
- Analiza las intersecciones por grado (simples, en T, complejas).
- Identifica y clasifica los tipos de vías.
- Busca semáforos etiquetados en OSM y estima semáforos adicionales.
- Estima un nivel de tráfico general basado en hora y día.
- Genera un reporte de texto y un mapa HTML resumen.

Características
---------------

- Uso de OSMnx y NetworkX para análisis de redes urbanas.
- Generación automática de un reporte de texto (`reporte_trafico_legal_YYYYMMDD_HHMMSS.txt`).
- Creación de un mapa interactivo en HTML (`mapa_trafico_legal_YYYYMMDD_HHMMSS.html`) con marcadores de intersecciones.
- Menú interactivo para seleccionar ciudades predefinidas.

Requisitos
----------

- Python 3.8 o superior (se recomienda 3.10+).
- Paquetes listados en `requirements.txt`.
- En Windows, algunas dependencias geoespaciales (como `geopandas`/`osmnx`) pueden requerir wheels precompilados o instalarse desde conda para evitar problemas con paquetes binarios.

Instalación (recomendado)
-------------------------

1. Crear y activar un entorno virtual (recomendado):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Instalar dependencias desde `requirements.txt`:

```powershell
pip install --upgrade pip; pip install -r requirements.txt
```

Notas de instalación:
- Si tiene problemas instalando `geopandas`/`osmnx` en Windows, usar conda (Anaconda/Miniconda) suele simplificarlo:

```powershell
conda create -n trafico python=3.10 -y; conda activate trafico
conda install -c conda-forge geopandas osmnx folium networkx pandas numpy -y
pip install -r requirements.txt
```

Uso
---

Ejecutar el script principal desde la raíz del proyecto:

```powershell
python ExtractorTraficoLegal.py
```

El script mostrará un menú para seleccionar una ciudad (Cali, Bogotá, Medellín, Barranquilla, Cartagena). Tras seleccionar, realizará el análisis completo. Dependiendo de la conexión y el área, la descarga y el procesamiento pueden tardar varios minutos.

Archivos generados
------------------

- `reporte_trafico_legal_YYYYMMDD_HHMMSS.txt` — reporte de texto con estadísticas y conclusiones.
- `mapa_trafico_legal_YYYYMMDD_HHMMSS.html` — mapa interactivo con marcadores y un panel informativo.

Consideraciones y limitaciones
------------------------------

- El análisis de tráfico es estimado y no usa datos en tiempo real. Para datos en tiempo real se requieren APIs oficiales (p. ej. APIs municipales o servicios comerciales).
- La calidad de los resultados depende de la calidad del mapeo en OpenStreetMap en la región analizada.
- Algunos elementos (por ejemplo semáforos) pueden no estar etiquetados en OSM; el script realiza estimaciones complementarias.

Buenas prácticas
----------------

- Ejecutar en un entorno con conexión estable a Internet.
- Si va a ejecutar análisis para múltiples ciudades o varias veces, limpiar o mover los archivos generados para no confundir resultados.
- Para análisis reproducibles en servidores, usar entornos con versiones fijadas de dependencias.

Extensiones sugeridas
---------------------

- Añadir parámetros por línea de comando para elegir ciudad, nivel de detalle y carpeta de salida.
- Soportar entrada de bounding box o coordenadas para analizar sub-áreas concretas.
- Integrar fuentes de tráfico en tiempo real (APIs) para mejorar estimaciones.

Resolución de problemas
-----------------------

- Error al importar `osmnx`/`geopandas`: instalar dependencias binarias desde conda-forge o usar ruedas precompiladas.
- Tiempo de descarga muy largo: reducir el área analizada (usar bounding box o lugar más específico).

Autor
-----

Juan Sebastian Rodas Ramirez

