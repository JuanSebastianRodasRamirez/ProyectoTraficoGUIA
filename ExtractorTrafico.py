#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EXTRACTOR DE TRÁFICO
===============================================

- OpenStreetMap (OSM) para datos de calles, intersecciones y semáforos
- Estimaciones de tráfico basadas en análisis de patrones

Autor: Juan Sebastian Rodas Ramirez
"""

import osmnx as ox
import networkx as nx
from datetime import datetime
import folium
import pandas as pd
import json
import warnings
warnings.filterwarnings('ignore')

class ExtractorTrafico:
    def __init__(self, ciudad: str = "Cali, Colombia"):
        self.ciudad = ciudad
        self.G = None
        self.estadisticas = {}
        
    def extraer_datos_basicos(self):
        """Extrae datos básicos de la red vial"""
        print(f"📍 Descargando red vial de {self.ciudad}...")
        
        try:
            # Descargar grafo de la ciudad
            self.G = ox.graph_from_place(self.ciudad, network_type="drive")
            
            # Obtener estadísticas básicas
            num_nodos = len(self.G.nodes)
            num_calles = len(self.G.edges)
            
            print(f"✅ Red vial obtenida:")
            print(f"   • Intersecciones: {num_nodos:,}")
            print(f"   • Segmentos de calles: {num_calles:,}")
            
            # Guardar estadísticas
            self.estadisticas['intersecciones'] = num_nodos
            self.estadisticas['segmentos_calles'] = num_calles
            
            return True
            
        except Exception as e:
            print(f"❌ Error descargando datos: {e}")
            return False
    
    def analizar_intersecciones(self):
        """Analiza las intersecciones por complejidad"""
        print("🔀 Analizando intersecciones...")
        
        if self.G is None:
            print("❌ Primero debe cargar los datos")
            return
        
        # Analizar grado de cada nodo (número de conexiones)
        grados = dict(self.G.degree())
        
        # Clasificar intersecciones
        intersecciones_simples = sum(1 for g in grados.values() if g <= 2)
        intersecciones_t = sum(1 for g in grados.values() if g == 3)
        intersecciones_complejas = sum(1 for g in grados.values() if g >= 4)
        
        print(f"✅ Análisis de intersecciones:")
        print(f"   • Simples (≤2 conexiones): {intersecciones_simples:,}")
        print(f"   • En T (3 conexiones): {intersecciones_t:,}")
        print(f"   • Complejas (≥4 conexiones): {intersecciones_complejas:,}")
        
        # Guardar estadísticas
        self.estadisticas['intersecciones_simples'] = intersecciones_simples
        self.estadisticas['intersecciones_t'] = intersecciones_t
        self.estadisticas['intersecciones_complejas'] = intersecciones_complejas
        
        return {
            'simples': intersecciones_simples,
            'en_t': intersecciones_t,
            'complejas': intersecciones_complejas
        }
    
    def extraer_calles_principales(self):
        """Extrae información de calles principales"""
        print("🛣️  Identificando calles principales...")
        
        if self.G is None:
            print("❌ Primero debe cargar los datos")
            return
        
        try:
            # Convertir a GeoDataFrame para análisis
            _, edges_gdf = ox.graph_to_gdfs(self.G)
            
            # Diccionario para traducir tipos de vías al español
            traduccion_vias = {
                'residential': 'Residencial',
                'tertiary': 'Terciaria',
                'secondary': 'Secundaria',
                'primary': 'Principal',
                'trunk': 'Troncal',
                'unclassified': 'Sin clasificar',
                'primary_link': 'Enlace principal',
                'secondary_link': 'Enlace secundario',
                'tertiary_link': 'Enlace terciario',
                'trunk_link': 'Enlace troncal',
                'service': 'Servicio',
                'living_street': 'Calle residencial',
                'pedestrian': 'Peatonal',
                'footway': 'Sendero peatonal',
                'cycleway': 'Ciclovía',
                'track': 'Pista',
                'path': 'Sendero',
                'steps': 'Escalones',
                'motorway': 'Autopista',
                'motorway_link': 'Enlace autopista'
            }
            
            # Contar tipos de vías
            tipos_vias = {}
            calles_nombradas = 0
            longitud_total = 0
            
            for _, edge in edges_gdf.iterrows():
                # Tipo de vía
                highway_type = edge.get('highway', 'unknown')
                if isinstance(highway_type, list):
                    highway_type = highway_type[0] if highway_type else 'unknown'
                
                # Traducir al español
                tipo_español = traduccion_vias.get(highway_type, highway_type.title())
                tipos_vias[tipo_español] = tipos_vias.get(tipo_español, 0) + 1
                
                # Contar calles con nombre
                name = edge.get('name')
                if name and str(name).lower() not in ['nan', 'none', '']:
                    calles_nombradas += 1
                
                # Sumar longitud
                length = edge.get('length', 0)
                if isinstance(length, (int, float)) and length > 0:
                    longitud_total += length
            
            print(f"✅ Análisis de calles:")
            print(f"   • Calles con nombre: {calles_nombradas:,}")
            print(f"   • Longitud total: {longitud_total/1000:.1f} km")
            
            # Mostrar tipos principales
            tipos_ordenados = sorted(tipos_vias.items(), key=lambda x: x[1], reverse=True)
            print(f"   • Tipos de vías principales:")
            for tipo, cantidad in tipos_ordenados[:5]:
                print(f"     - {tipo}: {cantidad:,}")
            
            # Guardar estadísticas
            self.estadisticas['calles_nombradas'] = calles_nombradas
            self.estadisticas['longitud_total_km'] = round(longitud_total/1000, 1)
            self.estadisticas['tipos_vias'] = dict(tipos_ordenados[:10])
            
            return tipos_vias
            
        except Exception as e:
            print(f"⚠️  Error analizando calles: {e}")
            return {}
    
    def buscar_semaforos_osm(self):
        """Busca semáforos marcados en OSM"""
        print("🚦 Buscando semáforos en OSM...")
        
        try:
            # Buscar elementos marcados como semáforos
            tags = {"highway": "traffic_signals"}
            semaforos = ox.geometries_from_place(self.ciudad, tags)
            
            num_semaforos_osm = len(semaforos)
            print(f"✅ Semáforos encontrados en OSM: {num_semaforos_osm}")
            
            # Estimar semáforos adicionales basado en intersecciones complejas
            intersecciones_complejas = self.estadisticas.get('intersecciones_complejas', 0)
            semaforos_estimados = min(intersecciones_complejas, int(intersecciones_complejas * 0.3))
            
            total_semaforos = num_semaforos_osm + semaforos_estimados
            
            print(f"   • Confirmados en OSM: {num_semaforos_osm}")
            print(f"   • Estimados adicionales: {semaforos_estimados}")
            print(f"   • Total estimado: {total_semaforos}")
            
            # Guardar estadísticas
            self.estadisticas['semaforos_osm'] = num_semaforos_osm
            self.estadisticas['semaforos_estimados'] = semaforos_estimados
            self.estadisticas['semaforos_total'] = total_semaforos
            
            return total_semaforos
            
        except Exception as e:
            print(f"⚠️  Error buscando semáforos: {e}")
            # Estimación basada solo en intersecciones
            intersecciones_complejas = self.estadisticas.get('intersecciones_complejas', 0)
            semaforos_estimados = int(intersecciones_complejas * 0.25)
            
            print(f"   • Estimación basada en intersecciones: {semaforos_estimados}")
            
            self.estadisticas['semaforos_osm'] = 0
            self.estadisticas['semaforos_estimados'] = semaforos_estimados
            self.estadisticas['semaforos_total'] = semaforos_estimados
            
            return semaforos_estimados
    
    def estimar_trafico_actual(self):
        """Estima condiciones de tráfico basado en hora y tipos de vía"""
        print("🚗 Estimando condiciones de tráfico...")
        
        hora_actual = datetime.now().hour
        dia_semana = datetime.now().weekday()  # 0=Lunes, 6=Domingo
        
        # Factores base por hora
        if 7 <= hora_actual <= 9:
            factor_hora = 1.0
            periodo = "Hora pico matutina"
        elif 12 <= hora_actual <= 14:
            factor_hora = 0.8
            periodo = "Hora almuerzo"
        elif 17 <= hora_actual <= 19:
            factor_hora = 1.0
            periodo = "Hora pico vespertina"
        elif 20 <= hora_actual <= 22:
            factor_hora = 0.6
            periodo = "Noche activa"
        else:
            factor_hora = 0.3
            periodo = "Horario nocturno/madrugada"
        
        # Factor por día de la semana
        if dia_semana < 5:  # Lunes a viernes
            factor_dia = 1.0
            tipo_dia = "Día laboral"
        elif dia_semana == 5:  # Sábado
            factor_dia = 0.7
            tipo_dia = "Sábado"
        else:  # Domingo
            factor_dia = 0.5
            tipo_dia = "Domingo"
        
        # Calcular nivel de tráfico general
        nivel_trafico = factor_hora * factor_dia
        
        if nivel_trafico >= 0.8:
            descripcion_trafico = "Alto - Congestión esperada"
        elif nivel_trafico >= 0.5:
            descripcion_trafico = "Medio - Flujo moderado"
        else:
            descripcion_trafico = "Bajo - Flujo libre"
        
        print(f"✅ Estimación de tráfico:")
        print(f"   • Hora: {datetime.now().strftime('%H:%M')} - {periodo}")
        print(f"   • Día: {tipo_dia}")
        print(f"   • Nivel general: {descripcion_trafico}")
        print(f"   • Factor numérico: {nivel_trafico:.2f}")
        
        # Guardar estadísticas
        self.estadisticas['trafico'] = {
            'hora': datetime.now().strftime('%H:%M'),
            'periodo': periodo,
            'tipo_dia': tipo_dia,
            'nivel_numerico': round(nivel_trafico, 2),
            'descripcion': descripcion_trafico,
            'factor_hora': factor_hora,
            'factor_dia': factor_dia
        }
        
        return nivel_trafico
    
    def generar_reporte_completo(self):
        """Genera un reporte completo con todos los datos"""
        print("\n📋 Generando reporte completo...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"reporte_trafico{timestamp}.txt"
        
        reporte = f"""
{'='*80}
    REPORTE DE ANÁLISIS DE TRÁFICO
    Ciudad: {self.ciudad.upper()}
    Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'='*80}

📍 FUENTES DE DATOS:
• OpenStreetMap (OSM)
• OSMnx - Análisis de redes urbanas
• NetworkX - Análisis de grafos
• Algoritmos de estimación de tráfico

🏙️  INFORMACIÓN GENERAL DE LA CIUDAD:
• Total de intersecciones: {self.estadisticas.get('intersecciones', 0):,}
• Total de segmentos de calles: {self.estadisticas.get('segmentos_calles', 0):,}
• Calles con nombre identificado: {self.estadisticas.get('calles_nombradas', 0):,}
• Longitud total de red vial: {self.estadisticas.get('longitud_total_km', 0)} km

🔀 ANÁLISIS DE INTERSECCIONES:
• Intersecciones simples (≤2 conexiones): {self.estadisticas.get('intersecciones_simples', 0):,}
• Intersecciones en T (3 conexiones): {self.estadisticas.get('intersecciones_t', 0):,}
• Intersecciones complejas (≥4 conexiones): {self.estadisticas.get('intersecciones_complejas', 0):,}

🛣️  TIPOS DE VÍAS IDENTIFICADAS:
"""
        
        if 'tipos_vias' in self.estadisticas:
            for tipo, cantidad in self.estadisticas['tipos_vias'].items():
                reporte += f"• {tipo}: {cantidad:,} segmentos\n"
        
        reporte += f"""
🚦 ANÁLISIS DE SEMÁFOROS:
• Semáforos confirmados en OSM: {self.estadisticas.get('semaforos_osm', 0)}
• Semáforos estimados adicionales: {self.estadisticas.get('semaforos_estimados', 0)}
• Total estimado de semáforos: {self.estadisticas.get('semaforos_total', 0)}

🚗 ANÁLISIS DE TRÁFICO ACTUAL:
• Hora de análisis: {self.estadisticas.get('trafico', {}).get('hora', 'N/A')}
• Período del día: {self.estadisticas.get('trafico', {}).get('periodo', 'N/A')}
• Tipo de día: {self.estadisticas.get('trafico', {}).get('tipo_dia', 'N/A')}
• Nivel de tráfico: {self.estadisticas.get('trafico', {}).get('descripcion', 'N/A')}
• Factor numérico: {self.estadisticas.get('trafico', {}).get('nivel_numerico', 0)}

📊 METODOLOGÍA UTILIZADA:
• Red vial extraída de OpenStreetMap
• Intersecciones analizadas por grado de conectividad
• Semáforos identificados por etiquetas OSM y estimación basada en intersecciones
• Tráfico estimado por patrones horarios y tipos de vía

⚠️  LIMITACIONES:
• Tráfico basado en estimaciones, no datos en tiempo real
• Calidad de datos OSM varía por región
• Semáforos parcialmente estimados
• No incluye eventos especiales o incidentes

💡 RECOMENDACIONES:
• Los datos son más precisos en áreas urbanas bien mapeadas
• Para tráfico en tiempo real, considerar APIs oficiales de tráfico
• Verificar semáforos estimados con observación directa
• Actualizar análisis periódicamente

{'='*80}
SISTEMA DE ANÁLISIS DE TRÁFICO URBANO
OpenStreetMap | OSMnx | NetworkX | Folium
Generado: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
{'='*80}
"""
        
        # Guardar reporte
        try:
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(reporte)
            print(f"📄 Reporte guardado en: {nombre_archivo}")
            
            # Mostrar resumen en consola
            print(f"\n📊 RESUMEN FINAL:")
            print(f"   🔹 Intersecciones analizadas: {self.estadisticas.get('intersecciones', 0):,}")
            print(f"   🔹 Calles identificadas: {self.estadisticas.get('calles_nombradas', 0):,}")
            print(f"   🔹 Semáforos total: {self.estadisticas.get('semaforos_total', 0)}")
            print(f"   🔹 Nivel de tráfico: {self.estadisticas.get('trafico', {}).get('descripcion', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Error guardando reporte: {e}")
    
    def crear_mapa_resumen(self):
        """Crea un mapa con resumen de datos principales"""
        print("🗺️  Creando mapa resumen...")
        
        if self.G is None:
            print("❌ No hay datos para el mapa")
            return
        
        try:
            # Obtener centro de la ciudad
            nodos_gdf, _ = ox.graph_to_gdfs(self.G)
            centro_lat = nodos_gdf.y.mean()
            centro_lon = nodos_gdf.x.mean()
            
            # Crear mapa
            m = folium.Map(location=[centro_lat, centro_lon], zoom_start=11)
            
            # Agregar algunas intersecciones importantes (cada 100 para no saturar)
            intersecciones_muestra = nodos_gdf.iloc[::100]
            
            for _, nodo in intersecciones_muestra.iterrows():
                # Calcular grado del nodo
                node_id = nodo.name
                grado = self.G.degree[node_id] if node_id in self.G else 2
                
                # Color según complejidad
                if grado >= 4:
                    color = "red"
                    radius = 4
                elif grado == 3:
                    color = "orange"
                    radius = 2
                else:
                    color = "blue"
                    radius = 1
                
                folium.CircleMarker(
                    location=[nodo.y, nodo.x],
                    radius=radius,
                    color=color,
                    fill=True,
                    popup=f"Intersección: {grado} conexiones"
                ).add_to(m)
            
            # Agregar información en el mapa
            info_html = f'''
            <div style="position: fixed; 
                        top: 10px; left: 10px; width: 300px; height: 150px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:12px; padding: 10px">
            <h4>Análisis de Tráfico - {self.ciudad}</h4>
            <b>Intersecciones:</b> {self.estadisticas.get('intersecciones', 0):,}<br>
            <b>Calles:</b> {self.estadisticas.get('calles_nombradas', 0):,}<br>
            <b>Semáforos:</b> {self.estadisticas.get('semaforos_total', 0)}<br>
            <b>Tráfico:</b> {self.estadisticas.get('trafico', {}).get('descripcion', 'N/A')}<br>
            <br>
            🔴 Intersección compleja<br>
            🟠 Intersección en T<br>
            🔵 Intersección simple
            </div>
            '''
            m.get_root().html.add_child(folium.Element(info_html))
            
            # Guardar mapa
            nombre_mapa = f"mapa_trafico{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            m.save(nombre_mapa)
            print(f"🗺️  Mapa guardado como: {nombre_mapa}")
            
        except Exception as e:
            print(f"⚠️  Error creando mapa: {e}")
    
    def ejecutar_analisis_completo(self):
        """Ejecuta el análisis completo de la ciudad"""
        print("🚀 INICIANDO ANÁLISIS COMPLETO")
        print("="*50)
        
        try:
            # Paso 1: Extraer datos básicos
            if not self.extraer_datos_basicos():
                return False
            
            # Paso 2: Analizar intersecciones
            self.analizar_intersecciones()
            
            # Paso 3: Analizar calles
            self.extraer_calles_principales()
            
            # Paso 4: Buscar semáforos
            self.buscar_semaforos_osm()
            
            # Paso 5: Estimar tráfico
            self.estimar_trafico_actual()
            
            # Paso 6: Generar reporte
            self.generar_reporte_completo()
            
            # Paso 7: Crear mapa
            self.crear_mapa_resumen()
            
            print("\n🎉 ANÁLISIS COMPLETADO EXITOSAMENTE")
            print("📁 Revisa los archivos generados")
            
            return True
            
        except Exception as e:
            print(f"❌ Error en el análisis: {e}")
            return False

def main():
    """Función principal"""
    print("🚦 EXTRACTOR DE TRÁFICO URBANO")
    print("="*50)
    print("Análisis de redes viales y estimación de tráfico")
    print("="*50)
    
    # Menú de ciudades
    ciudades = {
        '1': 'Cali, Colombia',
        '2': 'Bogotá, Colombia', 
        '3': 'Medellín, Colombia',
        '4': 'Barranquilla, Colombia',
        '5': 'Cartagena, Colombia'
    }
    
    print("\nSelecciona una ciudad para analizar:")
    for key, ciudad in ciudades.items():
        print(f"  {key}. {ciudad}")
    
    try:
        seleccion = input("\nIngresa el número (1-5): ").strip()
        
        if seleccion in ciudades:
            ciudad_seleccionada = ciudades[seleccion]
            print(f"\n🏙️  Analizando: {ciudad_seleccionada}")
            print("⏳ Este proceso puede tomar unos minutos...")
            
            # Crear y ejecutar extractor
            extractor = ExtractorTrafico(ciudad_seleccionada)
            exito = extractor.ejecutar_analisis_completo()
            
            if exito:
                print(f"\n✅ ANÁLISIS EXITOSO PARA {ciudad_seleccionada}")
            else:
                print(f"\n❌ Error en el análisis de {ciudad_seleccionada}")
                
        else:
            print("❌ Selección inválida")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Análisis interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")

if __name__ == "__main__":
    main()