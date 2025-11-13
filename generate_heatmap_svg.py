#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar mapa de calor do estado de São Paulo em formato SVG
usando GeoJSON para os limites exatos do estado.
"""

import csv
from collections import Counter
import folium
from folium.plugins import HeatMap
import geopy.geocoders
from geopy.geocoders import Nominatim
import time
import json
import os
import requests

def download_sp_geojson(output_file='sp_boundaries.geojson'):
    """Baixa o GeoJSON dos municípios de São Paulo do repositório oficial."""
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-35-mun.json"
    
    print("Baixando GeoJSON dos municípios de São Paulo...")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            geojson_data = response.json()
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, ensure_ascii=False, indent=2)
            num_municipios = len(geojson_data.get('features', []))
            print(f"GeoJSON salvo como '{output_file}'")
            print(f"Total de municípios carregados: {num_municipios}")
            return geojson_data
    except Exception as e:
        print(f"Erro ao baixar GeoJSON: {e}")
    return None

def load_geojson(filename):
    """Carrega GeoJSON de um arquivo."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def load_cities_from_csv(filename):
    """Carrega cidades do CSV e retorna contador de frequências."""
    cities = []
    with open(filename, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # Pular cabeçalho
        for row in reader:
            # Ignorar a última coluna (índice 5): "Cidades Região SP fora o município"
            for city in row[:-1]:  # Excluir última coluna
                city_clean = city.strip()
                if city_clean:
                    cities.append(city_clean)
    return Counter(cities)

def geocode_cities(city_counts, cache_file='city_coordinates.json'):
    """Geocodifica cidades usando cache."""
    geocoded = {}
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            geocoded = json.load(f)
    
    geolocator = Nominatim(user_agent="heatmap_sp")
    
    print(f"Geocodificando {len(city_counts)} cidades...")
    for i, (city, count) in enumerate(city_counts.items(), 1):
        if city in geocoded:
            continue
            
        location_query = f"{city}, São Paulo, Brasil"
        try:
            location = geolocator.geocode(location_query, timeout=10)
            if location:
                geocoded[city] = {
                    'lat': location.latitude,
                    'lon': location.longitude,
                    'count': count
                }
                print(f"[{i}/{len(city_counts)}] {city}: ({location.latitude}, {location.longitude})")
            else:
                print(f"[{i}/{len(city_counts)}] Não encontrado: {city}")
            time.sleep(1)
        except Exception as e:
            print(f"Erro ao geocodificar {city}: {e}")
            continue
    
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(geocoded, f, ensure_ascii=False, indent=2)
    
    return geocoded

def create_heatmap_svg(geocoded_cities, geojson_data, output_file='heatmap_sao_paulo.html'):
    """Cria mapa de calor usando Folium com GeoJSON, que pode ser exportado como SVG."""
    
    # Criar mapa centrado em São Paulo
    sp_map = folium.Map(
        location=[-23.5505, -46.6333],
        zoom_start=7,
        tiles='CartoDB positron'
    )
    
    # Adicionar contorno do estado usando GeoJSON
    if geojson_data and 'features' in geojson_data:
        folium.GeoJson(
            geojson_data,
            style_function=lambda feature: {
                'fillColor': '#e6f2ff',
                'color': '#0066cc',
                'weight': 3,
                'fillOpacity': 0.2,
            },
            tooltip='Estado de São Paulo'
        ).add_to(sp_map)
    
    # Preparar dados para heatmap
    heat_data = []
    for city, data in geocoded_cities.items():
        lat = data['lat']
        lon = data['lon']
        count = data['count']
        for _ in range(min(count, 40)):
            heat_data.append([lat, lon])
    
    # Adicionar heatmap
    if heat_data:
        HeatMap(
            heat_data,
            radius=25,
            blur=20,
            max_zoom=1,
            gradient={
                0.2: 'blue',
                0.4: 'cyan',
                0.6: 'lime',
                0.8: 'yellow',
                1.0: 'red'
            },
            min_opacity=0.3
        ).add_to(sp_map)
    
    # Adicionar marcadores para cidades principais
    sorted_cities = sorted(geocoded_cities.items(), 
                          key=lambda x: x[1]['count'], 
                          reverse=True)[:15]
    
    for city, data in sorted_cities:
        lat = data['lat']
        lon = data['lon']
        count = data['count']
        radius = min(count / 3, 15)
        
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            popup=f"<b>{city}</b><br>Frequência: {count}",
            tooltip=f"{city}: {count} ocorrências",
            color='darkred',
            fill=True,
            fillColor='red',
            fillOpacity=0.6,
            weight=2
        ).add_to(sp_map)
    
    # Adicionar legenda
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 250px; height: 150px; 
                background-color: white; border:3px solid #0066cc; z-index:9999; 
                font-size:14px; padding: 15px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2);">
    <h4 style="margin-top:0; color: #0066cc;">Mapa de Calor - SP</h4>
    <p style="margin:5px 0;"><span style="color:blue;">●</span> Baixa frequência</p>
    <p style="margin:5px 0;"><span style="color:yellow;">●</span> Média frequência</p>
    <p style="margin:5px 0;"><span style="color:red;">●</span> Alta frequência</p>
    <p style="margin:5px 0; font-size:12px; color:#666;">Círculos vermelhos: Top 15 cidades</p>
    </div>
    '''
    sp_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Salvar HTML
    sp_map.save(output_file)
    print(f"Mapa HTML salvo como '{output_file}'")
    print(f"\nPara exportar como SVG:")
    print(f"1. Abra '{output_file}' no navegador")
    print(f"2. Use as ferramentas de desenvolvedor (F12)")
    print(f"3. Ou use um conversor online de HTML para SVG")
    print(f"\nTotal de cidades mapeadas: {len(geocoded_cities)}")

def main():
    """Função principal."""
    csv_file = 'Regiões e cidades - Página1.csv'
    geojson_file = 'SP_simplified.geojson'
    
    if not os.path.exists(csv_file):
        print(f"Erro: Arquivo '{csv_file}' não encontrado!")
        return
    
    # Carregar ou baixar GeoJSON
    geojson_data = load_geojson(geojson_file)
    if not geojson_data:
        print(f"GeoJSON '{geojson_file}' não encontrado. Baixando...")
        geojson_data = download_sp_geojson(geojson_file)
        if not geojson_data:
            print("Erro: Não foi possível carregar o GeoJSON!")
            return
    
    # Carregar e contar cidades
    print("Carregando dados do CSV...")
    city_counts = load_cities_from_csv(csv_file)
    print(f"Total de cidades únicas: {len(city_counts)}")
    
    # Geocodificar cidades
    geocoded_cities = geocode_cities(city_counts)
    
    if not geocoded_cities:
        print("Erro: Nenhuma cidade foi geocodificada!")
        return
    
    # Criar mapa
    create_heatmap_svg(geocoded_cities, geojson_data)

if __name__ == '__main__':
    main()

