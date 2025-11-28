#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar mapa de calor estático (como imagem de livro de geografia)
sem controles de zoom e com contorno do estado de São Paulo via GeoJSON.
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
    cached_data = {}
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
    
    geolocator = Nominatim(user_agent="heatmap_sp")
    
    print(f"Geocodificando {len(city_counts)} cidades...")
    for i, (city, count) in enumerate(city_counts.items(), 1):
        if city in cached_data:
            # Usar dados do cache, mas atualizar o count
            geocoded[city] = {
                'lat': cached_data[city]['lat'],
                'lon': cached_data[city]['lon'],
                'count': count
            }
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
                cached_data[city] = {
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
    
    # Salvar cache atualizado (incluindo novas cidades)
    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cached_data, f, ensure_ascii=False, indent=2)
    
    # Retornar apenas as cidades que estão em city_counts (filtradas)
    return geocoded

def load_geojson(filename):
    """Carrega GeoJSON de um arquivo."""
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def create_static_heatmap(geocoded_cities, geojson_data, output_file='index.html'):
    """
    Cria mapa de calor estático (como imagem de livro) sem controles de zoom.
    """
    # Criar mapa centrado em São Paulo - Zoom habilitado mas dados estáticos (sem filtragem dinâmica)
    sp_map = folium.Map(
        location=[-23.5505, -46.6333],
        zoom_start=7,
        tiles='CartoDB positron',  # Estilo mais limpo para impressão/livro
        zoom_control=True,  # Habilitar controles de zoom
        scroll_wheel_zoom=True,  # Habilitar zoom com scroll
        dragging=True,  # Habilitar arrastar o mapa
        touch_zoom=True,  # Habilitar zoom touch
        double_click_zoom=True,  # Habilitar zoom duplo clique
        box_zoom=True,  # Habilitar zoom por caixa
        keyboard=True,  # Habilitar controles de teclado
        attribution_control=False  # Remover atribuição para visualização mais limpa
    )
    
    # Adicionar contorno do estado de São Paulo usando GeoJSON
    if geojson_data and 'features' in geojson_data:
        print(f"Adicionando contorno do estado de São Paulo ({len(geojson_data['features'])} feature(s))...")
        folium.GeoJson(
            geojson_data,
            style_function=lambda feature: {
                'fillColor': '#e8e8e8',  # Light gray - solid color for scientific publication printing
                'color': '#333333',      # Dark gray border for better visibility
                'weight': 2,
                'fillOpacity': 1.0,       # Solid fill (no transparency) for print
            },
            tooltip='Estado de São Paulo'
        ).add_to(sp_map)
    
    # Preparar dados para heatmap - MOSTRAR TODAS as ocorrências
    counts = [data['count'] for data in geocoded_cities.values()]
    if counts:
        max_count = max(counts)
        min_count = min(counts)
        total_occurrences = sum(counts)
    else:
        max_count = 1
        min_count = 1
        total_occurrences = 0
    
    print(f"Frequência mínima: {min_count}")
    print(f"Frequência máxima: {max_count}")
    print(f"Total de ocorrências: {total_occurrences}")
    print(f"Incluindo TODAS as {len(geocoded_cities)} cidades no mapa")
    
    heat_data = []
    for city, data in geocoded_cities.items():
        lat = data['lat']
        lon = data['lon']
        count = data['count']
        
        # Adicionar TODAS as cidades, sem filtragem
        # Adicionar pontos proporcionais à frequência (sem limite artificial)
        # Mais pontos para áreas de alta frequência para garantir que vermelho se sobreponha
        num_points = max(1, int(count * 2.5))  # 2.5 pontos por unidade de frequência (aumentado)
        for _ in range(num_points):
            heat_data.append([lat, lon])
    
    print(f"Pontos no heat map: {len(heat_data)}")
    
    # Adicionar heatmap - SEM max_zoom para manter visível em todos os níveis de zoom
    # Os dados permanecem os mesmos independente do zoom (sem filtragem dinâmica)
    if heat_data:
        HeatMap(
            heat_data,
            radius=40,  # Raio otimizado para melhor cobertura e transição suave
            blur=30,   # Blur aumentado para transição mais suave entre intensidades
            max_zoom=18,  # Permitir zoom alto mas manter dados fixos
            min_opacity=0.4,  # Opacidade mínima aumentada para melhor visibilidade
            max_zoom_intensity=1.8,  # Intensidade ajustada para melhor contraste
            # Gradiente científico sequencial (YlOrRd - Yellow-Orange-Red)
            # Paleta perceptualmente uniforme, adequada para publicações científicas
            # Baseada em ColorBrewer - usando cores hexadecimais (Folium requer formato hex)
            gradient={
                0.0: 'transparent',           # Transparente no início
                0.15: '#ffffb2',              # Amarelo muito claro (baixa intensidade)
                0.3: '#fed976',               # Amarelo claro
                0.45: '#feb24c',             # Amarelo-alaranjado
                0.6: '#fd8d3c',              # Laranja médio
                0.75: '#fc4e2a',             # Laranja-avermelhado
                0.9: '#e31a1c',              # Vermelho médio
                1.0: '#b10026'               # Vermelho escuro (alta intensidade)
            }
        ).add_to(sp_map)
    
    # Adicionar marcadores apenas para cidades principais (opcional, muito transparentes)
    # Marcadores muito sutis para não interferir com o heatmap
    # O heatmap já mostra a intensidade através das cores
    sorted_cities = sorted(geocoded_cities.items(), 
                          key=lambda x: x[1]['count'], 
                          reverse=True)
    
    # Adicionar apenas marcadores muito sutis para as top cidades (opcional)
    # Comentado para deixar apenas o heatmap visível
    # for city, data in sorted_cities[:10]:  # Apenas top 10
    #     lat = data['lat']
    #     lon = data['lon']
    #     count = data['count']
    #     
    #     folium.CircleMarker(
    #         location=[lat, lon],
    #         radius=3,  # Muito pequeno
    #         popup=f"<b>{city}</b><br>Município de trabalho: {count}",
    #         tooltip=f"{city}: {count} ocorrências",
    #         color='darkred',
    #         fill=True,
    #         fillColor='red',
    #         fillOpacity=0.2,  # Muito transparente
    #         weight=1
    #     ).add_to(sp_map)
    
    # Adicionar legenda profissional com gradiente de temperatura (lado esquerdo)
    if counts:
        legend_html = f'''
    <div style="position: fixed; 
                bottom: 30px; left: 30px; width: 280px; height: 180px; 
                background-color: white; border:2px solid #333; z-index:9999; 
                font-size:13px; padding: 15px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.3)">
    <h4 style="margin-top: 0; margin-bottom: 10px; color: #333;">Mapa de Calor - Município de trabalho</h4>
    <div style="height: 20px; background: linear-gradient(to right, 
        rgba(255, 255, 178, 0.4), 
        rgba(254, 217, 118, 0.5), 
        rgba(254, 178, 76, 0.6), 
        rgba(253, 141, 60, 0.7), 
        rgba(252, 78, 42, 0.85), 
        rgba(227, 26, 28, 0.95), 
        rgba(177, 0, 38, 1.0)); 
        border: 1px solid #ccc; margin: 10px 0; border-radius: 4px;"></div>
    <div style="display: flex; justify-content: space-between; font-size: 11px; color: #666;">
        <span>Baixa ({min_count})</span>
        <span>Alta ({max_count})</span>
    </div>
    <hr style="margin: 10px 0; border: none; border-top: 1px solid #ddd;">
    <p style="margin: 5px 0; font-size: 11px; color: #666;">
        <strong>Total de cidades:</strong> {len(geocoded_cities)}
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
            <strong>Total de ocorrências:</strong> <span style="font-weight: bold; color: #333;">{total_occurrences:,}</span><br>
            <strong>Cidades únicas:</strong> <span style="font-weight: bold; color: #333;">{len(geocoded_cities)}</span>
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
    
    # Adicionar CSS personalizado - zoom habilitado mas estilo limpo
    static_css = '''
    <style>
        /* Mapa com zoom habilitado mas dados estáticos (sem filtragem dinâmica) */
        .leaflet-container {
            background-color: #f5f5f5;
        }
        .leaflet-attribution {
            display: none !important;
        }
        body {
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .folium-map {
            width: 100vw;
            height: 100vh;
            border: 2px solid #333;
            box-shadow: inset 0 0 10px rgba(0,0,0,0.1);
        }
        /* Estilo de livro de geografia */
        html {
            background-color: #f5f5f5;
        }
        /* Garantir que o polígono do estado fique atrás do heatmap e marcadores */
        .leaflet-pane.leaflet-overlay-pane svg path[fill="#e8e8e8"] {
            z-index: 100 !important;
        }
        /* Canvas do heatmap deve ficar na frente com z-index alto para vermelho se sobrepor */
        .leaflet-heatmap-layer {
            z-index: 500 !important;
        }
        .leaflet-heatmap-layer canvas {
            z-index: 500 !important;
        }
        /* Marcadores devem ficar na frente de tudo */
        .leaflet-marker-pane {
            z-index: 600 !important;
        }
        .leaflet-marker-icon {
            z-index: 600 !important;
        }
    </style>
    <script>
        // Garantir que o polígono do estado fique atrás após o carregamento
        window.addEventListener('load', function() {
            setTimeout(function() {
                var overlays = document.querySelectorAll('.leaflet-overlay-pane svg');
                overlays.forEach(function(svg) {
                    var paths = svg.querySelectorAll('path[fill="#e8e8e8"]');
                    if (paths.length > 0) {
                        svg.style.zIndex = '100';
                    }
                });
                // Heatmap canvas deve ficar na frente com z-index alto para vermelho se sobrepor
                var heatmapLayer = document.querySelector('.leaflet-heatmap-layer');
                if (heatmapLayer) {
                    heatmapLayer.style.zIndex = '500';
                }
                var heatmapCanvas = document.querySelector('.leaflet-heatmap-layer canvas');
                if (heatmapCanvas) {
                    heatmapCanvas.style.zIndex = '500';
                    // Garantir que o canvas seja renderizado por último
                    heatmapCanvas.style.pointerEvents = 'none';
                }
                // Garantir que todas as camadas do heatmap tenham z-index alto
                var allHeatmapLayers = document.querySelectorAll('.leaflet-heatmap-layer');
                allHeatmapLayers.forEach(function(layer) {
                    layer.style.zIndex = '500';
                });
            }, 500);
        });
    </script>
    '''
    sp_map.get_root().html.add_child(folium.Element(static_css))
    
    # Salvar HTML estático
    sp_map.save(output_file)
    print(f"\nMapa estático salvo como '{output_file}'")
    print(f"Total de cidades mapeadas: {len(geocoded_cities)}")
    print("\nCaracterísticas do mapa estático:")
    print("- Zoom habilitado (pode aproximar/afastar)")
    print("- Dados fixos (heat map e marcadores não mudam com zoom)")
    print("- Sem clustering dinâmico (marcadores sempre visíveis)")
    print("- Contorno completo do estado de São Paulo")
    print("- Ideal para visualização como imagem de livro com zoom")

def main():
    """Função principal."""
    csv_file = 'Regiões e cidades - Página1.csv'
    geojson_file = 'SP_simplified.geojson'
    
    if not os.path.exists(csv_file):
        print(f"Erro: Arquivo '{csv_file}' não encontrado!")
        return
    
    # Carregar GeoJSON
    geojson_data = load_geojson(geojson_file)
    if not geojson_data:
        print(f"Erro: GeoJSON '{geojson_file}' não encontrado!")
        print("Execute primeiro: python3 generate_heatmap_geojson.py")
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
    
    if not geocoded_cities:
        print("Erro: Nenhuma cidade foi geocodificada!")
        return
    
    # Criar mapa estático
    create_static_heatmap(geocoded_cities, geojson_data)

if __name__ == '__main__':
    main()

