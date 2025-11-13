#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar mapa de calor do estado de São Paulo
baseado na frequência de cidades no arquivo CSV.
"""

import csv
from collections import Counter
import folium
from folium.plugins import HeatMap, MarkerCluster
import geopy.geocoders
from geopy.geocoders import Nominatim
import time
import json
import os

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
    """Geocodifica cidades usando cache para evitar requisições repetidas."""
    geocoded = {}
    
    # Carregar cache se existir
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
            time.sleep(1)  # Rate limiting
        except Exception as e:
            print(f"Erro ao geocodificar {city}: {e}")
            continue
    
    # Salvar cache
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(geocoded, f, ensure_ascii=False, indent=2)
    
    return geocoded

def create_heatmap(geocoded_cities, output_file='heatmap_sao_paulo.html'):
    """Cria mapa de calor usando Folium."""
    # Criar mapa centrado em São Paulo
    sp_map = folium.Map(
        location=[-23.5505, -46.6333],
        zoom_start=7,
        tiles='OpenStreetMap'
    )
    
    # Preparar dados para heatmap
    # Filtrar cidades de baixa frequência - calcular threshold baseado na média
    counts = [data['count'] for data in geocoded_cities.values()]
    if counts:
        max_count = max(counts)
        avg_count = sum(counts) / len(counts)
        min_threshold = max(3, avg_count * 0.2)  # Mínimo de 3 ou 20% da média
    else:
        min_threshold = 3
        max_count = 1
    
    print(f"Frequência máxima: {max_count}")
    print(f"Frequência média: {avg_count:.1f}")
    print(f"Filtrando cidades com frequência mínima: {min_threshold:.1f}")
    
    heat_data = []
    filtered_cities = 0
    for city, data in geocoded_cities.items():
        lat = data['lat']
        lon = data['lon']
        count = data['count']
        
        # Filtrar apenas cidades acima do threshold
        if count >= min_threshold:
            # Adicionar pontos proporcionais à frequência (sem limite artificial)
            # Usar escala logarítmica para melhor distribuição visual
            num_points = max(1, int(count * 2))  # 2 pontos por unidade de frequência
            for _ in range(num_points):
                heat_data.append([lat, lon])
        else:
            filtered_cities += 1
    
    print(f"Cidades filtradas (baixa frequência): {filtered_cities}")
    print(f"Pontos no heat map: {len(heat_data)}")
    
    # Adicionar heatmap com gradiente profissional de temperatura
    if heat_data:
        HeatMap(
            heat_data,
            radius=30,  # Raio maior para melhor cobertura
            blur=25,   # Blur maior para transição suave
            max_zoom=18,
            min_opacity=0.3,  # Opacidade mínima para melhor visibilidade
            max_zoom_intensity=1.5,  # Intensidade máxima no zoom
            # Gradiente profissional de temperatura (frio -> quente)
            gradient={
                0.0: 'rgba(0, 0, 255, 0)',      # Transparente no início
                0.1: 'rgba(0, 100, 255, 0.3)',  # Azul frio
                0.3: 'rgba(0, 200, 255, 0.5)',  # Ciano
                0.5: 'rgba(0, 255, 200, 0.6)',  # Verde-água
                0.7: 'rgba(255, 255, 0, 0.7)',  # Amarelo
                0.85: 'rgba(255, 150, 0, 0.8)', # Laranja
                1.0: 'rgba(255, 0, 0, 1.0)'     # Vermelho quente
            }
        ).add_to(sp_map)
    
    # Adicionar marcadores para TODAS as cidades
    sorted_cities = sorted(geocoded_cities.items(), 
                          key=lambda x: x[1]['count'], 
                          reverse=True)  # Mostrar TODAS as cidades, não apenas top 20
    
    marker_cluster = MarkerCluster().add_to(sp_map)
    
    for city, data in sorted_cities:
        lat = data['lat']
        lon = data['lon']
        count = data['count']
        
        folium.Marker(
            location=[lat, lon],
            popup=f"<b>{city}</b><br>Frequência: {count}",
            tooltip=f"{city}: {count} ocorrências",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(marker_cluster)
    
    # Adicionar legenda profissional com gradiente de temperatura (lado esquerdo)
    if counts:
        max_freq = max(counts)
        min_freq = min([c for c in counts if c >= min_threshold])
        total_occurrences = sum(counts)
        legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 280px; height: 200px; 
                background-color: white; border:2px solid #333; z-index:9999; 
                font-size:13px; padding: 15px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3)">
    <h4 style="margin-top: 0; margin-bottom: 10px; color: #333;">Mapa de Calor - Frequência</h4>
    <div style="height: 20px; background: linear-gradient(to right, 
        rgba(0, 100, 255, 0.3), 
        rgba(0, 200, 255, 0.5), 
        rgba(0, 255, 200, 0.6), 
        rgba(255, 255, 0, 0.7), 
        rgba(255, 150, 0, 0.8), 
        rgba(255, 0, 0, 1.0)); 
        border: 1px solid #ccc; margin: 10px 0; border-radius: 4px;"></div>
    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #666;">
        <span>Baixa ({min_freq})</span>
        <span>Alta ({max_freq})</span>
    </div>
    <hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">
    <p style="margin: 5px 0; font-size: 11px; color: #666;">
        <strong>Total de cidades:</strong> {len(geocoded_cities)}<br>
        <strong>Cidades visíveis:</strong> {len(geocoded_cities) - filtered_cities}
    </p>
    </div>
    '''
        sp_map.get_root().html.add_child(folium.Element(legend_html))
    
    # Adicionar caixa informativa no lado direito com lista de cidades e ocorrências
    # Ordenar cidades por frequência (maior para menor)
    sorted_cities_list = sorted(geocoded_cities.items(), 
                               key=lambda x: x[1]['count'], 
                               reverse=True)
    
    # Criar lista HTML das cidades
    cities_list_html = ""
    for city, data in sorted_cities_list:
        count = data['count']
        cities_list_html += f'''
        <div style="display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px solid #eee;">
            <span style="font-size: 11px; color: #333;">{city}</span>
            <span style="font-size: 11px; font-weight: bold; color: #333;">{count}</span>
        </div>'''
    
    info_box_html = f'''
    <div style="position: fixed; 
                top: 30px; right: 30px; width: 280px; max-height: 85vh; overflow-y: auto;
                background-color: white; border:2px solid #333; z-index:9999; 
                font-size:13px; padding: 15px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3)">
    <h4 style="margin-top: 0; margin-bottom: 10px; color: #333; font-size:14px;">
        Cidades e Ocorrências
    </h4>
    <div style="margin-bottom: 10px; padding: 8px; background-color: #f5f5f5; border-radius: 4px;">
        <p style="margin: 0; font-size: 11px; color: #333;">
            <strong>Total:</strong> <span style="font-weight: bold; color: #333;">{total_occurrences:,}</span>
        </p>
    </div>
    <div style="margin-top: 10px;">
        <div style="max-height: 50vh; overflow-y: auto; padding: 5px;">
            {cities_list_html}
        </div>
    </div>
    </div>
    '''
    sp_map.get_root().html.add_child(folium.Element(info_box_html))
    
    # Salvar mapa
    sp_map.save(output_file)
    print(f"\nMapa salvo como '{output_file}'")
    print(f"Total de cidades mapeadas: {len(geocoded_cities)}")

def main():
    """Função principal."""
    csv_file = 'Regiões e cidades - Página1.csv'
    
    if not os.path.exists(csv_file):
        print(f"Erro: Arquivo '{csv_file}' não encontrado!")
        return
    
    # Carregar e contar cidades
    print("Carregando dados do CSV...")
    city_counts = load_cities_from_csv(csv_file)
    print(f"Total de cidades únicas: {len(city_counts)}")
    print(f"\nTop 10 cidades mais frequentes:")
    for city, count in city_counts.most_common(10):
        print(f"  {city}: {count}")
    
    # Geocodificar cidades
    geocoded_cities = geocode_cities(city_counts)
    
    # Criar mapa
    create_heatmap(geocoded_cities)

if __name__ == '__main__':
    main()

