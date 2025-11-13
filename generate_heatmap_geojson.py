#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar imagem PNG do mapa de calor do estado de São Paulo
usando GeoJSON para os limites exatos do estado.
"""

import csv
from collections import Counter
import plotly.graph_objects as go
import pandas as pd
import geopy.geocoders
from geopy.geocoders import Nominatim
import time
import json
import os
import requests
import base64
import io
from PIL import Image

def download_sp_geojson(output_file='sp_boundaries.geojson'):
    """Baixa o GeoJSON dos municípios de São Paulo do repositório oficial."""
    # URL do GeoJSON dos municípios de São Paulo (código 35)
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-35-mun.json"
    
    print("Baixando GeoJSON dos municípios de São Paulo...")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            geojson_data = response.json()
            
            # Salvar o GeoJSON completo (todos os municípios)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(geojson_data, f, ensure_ascii=False, indent=2)
            
            num_municipios = len(geojson_data.get('features', []))
            print(f"GeoJSON salvo como '{output_file}'")
            print(f"Total de municípios carregados: {num_municipios}")
            return geojson_data
        else:
            print(f"Erro ao baixar: Status {response.status_code}")
    except Exception as e:
        print(f"Erro ao baixar GeoJSON: {e}")
    
    # Se não conseguir baixar, criar um GeoJSON simplificado
    print("Criando GeoJSON simplificado do estado de São Paulo...")
    sp_geojson = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "properties": {"name": "São Paulo"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [-53.1, -20.8],
                    [-51.0, -20.5],
                    [-48.0, -22.0],
                    [-48.0, -24.0],
                    [-48.5, -25.0],
                    [-47.0, -25.0],
                    [-46.0, -24.5],
                    [-45.0, -23.5],
                    [-44.5, -22.0],
                    [-53.1, -20.8]
                ]]
            }
        }]
    }
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sp_geojson, f, ensure_ascii=False, indent=2)
    return sp_geojson

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
    cached_data = {}
    
    # Carregar cache se existir
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
            time.sleep(1)  # Rate limiting
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

def create_minimap_overview(geojson_data, lat_range, lon_range, temp_file='minimap_temp.png'):
    """
    Cria um minimapa (overview map) mostrando o estado de São Paulo completo
    com um retângulo indicando a área de zoom do mapa principal.
    
    Args:
        geojson_data: GeoJSON com os municípios de São Paulo
        lat_range: Tupla (min, max) com o range de latitude do mapa principal
        lon_range: Tupla (min, max) com o range de longitude do mapa principal
        temp_file: Nome do arquivo temporário para salvar o minimapa
    
    Returns:
        Caminho do arquivo temporário com o minimapa
    """
    # Criar figura para o minimapa
    minimap_fig = go.Figure()
    
    # Calcular limites reais do estado a partir do GeoJSON
    all_lats = []
    all_lons = []
    
    # Adicionar contorno de TODOS os municípios para formar o estado completo
    if geojson_data and 'features' in geojson_data:
        print(f"Desenhando contorno do estado de São Paulo ({len(geojson_data['features'])} feature(s)) no minimapa...")
        for idx, feature in enumerate(geojson_data['features']):
            geometry = feature.get('geometry', {})
            
            if geometry.get('type') == 'Polygon':
                coords = geometry['coordinates'][0]
                lons = [coord[0] for coord in coords]
                lats = [coord[1] for coord in coords]
                
                # Coletar coordenadas para calcular limites
                all_lons.extend(lons)
                all_lats.extend(lats)
                
                minimap_fig.add_trace(go.Scattergeo(
                    lon=lons,
                    lat=lats,
                    mode='lines',
                    line=dict(width=0.8, color='#0066cc'),
                    fill='toself',
                    fillcolor='rgba(230, 242, 255, 0.4)',
                    showlegend=False,
                    hoverinfo='skip'
                ))
            elif geometry.get('type') == 'MultiPolygon':
                for polygon in geometry['coordinates']:
                    coords = polygon[0]
                    lons = [coord[0] for coord in coords]
                    lats = [coord[1] for coord in coords]
                    
                    # Coletar coordenadas para calcular limites
                    all_lons.extend(lons)
                    all_lats.extend(lats)
                    
                    minimap_fig.add_trace(go.Scattergeo(
                        lon=lons,
                        lat=lats,
                        mode='lines',
                        line=dict(width=0.8, color='#0066cc'),
                        fill='toself',
                        fillcolor='rgba(230, 242, 255, 0.4)',
                        showlegend=False,
                        hoverinfo='skip'
                    ))
    
    # Calcular limites reais do estado
    if all_lats and all_lons:
        sp_lat_min = min(all_lats)
        sp_lat_max = max(all_lats)
        sp_lon_min = min(all_lons)
        sp_lon_max = max(all_lons)
        
        # Adicionar margem de 5% para melhor visualização
        lat_margin = (sp_lat_max - sp_lat_min) * 0.05
        lon_margin = (sp_lon_max - sp_lon_min) * 0.05
        
        sp_lat_min -= lat_margin
        sp_lat_max += lat_margin
        sp_lon_min -= lon_margin
        sp_lon_max += lon_margin
        
        # Calcular centro
        sp_center_lat = (sp_lat_min + sp_lat_max) / 2
        sp_center_lon = (sp_lon_min + sp_lon_max) / 2
        
        print(f"Limites do estado SP: Lat [{sp_lat_min:.2f}, {sp_lat_max:.2f}], Lon [{sp_lon_min:.2f}, {sp_lon_max:.2f}]")
        print(f"Centro do estado SP: ({sp_center_lat:.2f}, {sp_center_lon:.2f})")
    else:
        # Valores padrão se não conseguir calcular
        sp_lat_min, sp_lat_max = -26.0, -19.0
        sp_lon_min, sp_lon_max = -54.0, -42.0
        sp_center_lat, sp_center_lon = -23.0, -47.5
    
    # Desenhar retângulo que representa a área de zoom do mapa principal (Mapa Mayor)
    # Coordenadas do retângulo (canto inferior esquerdo, superior direito, etc.)
    zoom_lat_min, zoom_lat_max = lat_range
    zoom_lon_min, zoom_lon_max = lon_range
    
    print(f"Área do mapa principal (zoom): Lat [{zoom_lat_min:.2f}, {zoom_lat_max:.2f}], Lon [{zoom_lon_min:.2f}, {zoom_lon_max:.2f}]")
    
    # Criar retângulo fechado (5 pontos para fechar o polígono)
    rect_lons = [zoom_lon_min, zoom_lon_max, zoom_lon_max, zoom_lon_min, zoom_lon_min]
    rect_lats = [zoom_lat_min, zoom_lat_min, zoom_lat_max, zoom_lat_max, zoom_lat_min]
    
    # Adicionar retângulo vermelho bem visível mostrando a área do mapa principal
    minimap_fig.add_trace(go.Scattergeo(
        lon=rect_lons,
        lat=rect_lats,
        mode='lines',
        line=dict(width=3, color='red'),  # Linha mais grossa e vermelha
        fill='toself',
        fillcolor='rgba(255, 0, 0, 0.2)',  # Preenchimento mais visível
        showlegend=False,
        hoverinfo='skip',
        name='Área do Mapa Principal'
    ))
    
    # Configurar layout do minimapa
    minimap_fig.update_layout(
        title=dict(
            text='Localização no Estado<br><sub style="font-size:8px;">Retângulo vermelho: área do mapa principal</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=12, color='#333333')
        ),
        geo=dict(
            scope='south america',
            center=dict(lat=sp_center_lat, lon=sp_center_lon),  # Centro calculado do estado
            projection_scale=16,  # Escala ajustada para garantir que todo o estado apareça
            showland=True,
            landcolor='rgb(255, 255, 255)',
            countrycolor='rgb(200, 200, 200)',
            coastlinecolor='rgb(200, 200, 200)',
            lataxis=dict(range=[sp_lat_min, sp_lat_max]),  # Limites calculados do estado
            lonaxis=dict(range=[sp_lon_min, sp_lon_max]),  # Limites calculados do estado
            bgcolor='white',
            showlakes=False,
            showrivers=False,
            showocean=False,
            showcountries=True,
            countrywidth=1.5,  # Borda do país mais visível
            showsubunits=False,
            framecolor='rgb(150, 150, 150)',  # Borda do mapa mais visível
            framewidth=2  # Borda mais grossa
        ),
        width=400,  # Tamanho aumentado para melhor visibilidade
        height=350,
        margin=dict(l=15, r=15, t=50, b=15),  # Margens ajustadas
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    # Salvar minimapa como imagem temporária
    print(f"Salvando minimapa temporário em '{temp_file}'...")
    minimap_fig.write_image(temp_file, width=400, height=350, scale=2)
    print(f"Minimapa salvo: {os.path.getsize(temp_file)} bytes")
    return temp_file

def create_heatmap_with_geojson(geocoded_cities, geojson_data, output_file='heatmap_sao_paulo.png'):
    """Cria imagem PNG do mapa de calor usando GeoJSON para os limites do estado."""
    
    # Preparar dados das cidades
    city_data = []
    for city, data in geocoded_cities.items():
        city_data.append({
            'Cidade': city,
            'Latitude': data['lat'],
            'Longitude': data['lon'],
            'Frequência': data['count']
        })
    
    df = pd.DataFrame(city_data)
    
    # Criar figura
    fig = go.Figure()
    
    # Adicionar contorno dos municípios usando GeoJSON
    # O GeoJSON contém todos os municípios de São Paulo
    if geojson_data and 'features' in geojson_data:
        print(f"Desenhando {len(geojson_data['features'])} municípios...")
        for idx, feature in enumerate(geojson_data['features']):
            geometry = feature.get('geometry', {})
            properties = feature.get('properties', {})
            municipio_name = properties.get('name', 'Município')
            
            if geometry.get('type') == 'Polygon':
                coords = geometry['coordinates'][0]
                lons = [coord[0] for coord in coords]
                lats = [coord[1] for coord in coords]
                
                fig.add_trace(go.Scattergeo(
                    lon=lons,
                    lat=lats,
                    mode='lines',
                    line=dict(width=1, color='#0066cc'),
                    fill='toself',
                    fillcolor='rgba(230, 242, 255, 0.15)',
                    name='Municípios',
                    showlegend=(idx == 0),  # Mostrar legenda apenas uma vez
                    legendgroup='municipios',
                    hoverinfo='skip'
                ))
            elif geometry.get('type') == 'MultiPolygon':
                for polygon in geometry['coordinates']:
                    coords = polygon[0]
                    lons = [coord[0] for coord in coords]
                    lats = [coord[1] for coord in coords]
                    
                    fig.add_trace(go.Scattergeo(
                        lon=lons,
                        lat=lats,
                        mode='lines',
                        line=dict(width=1, color='#0066cc'),
                        fill='toself',
                        fillcolor='rgba(230, 242, 255, 0.15)',
                        name='Municípios',
                        showlegend=False,
                        legendgroup='municipios',
                        hoverinfo='skip'
                    ))
    
    # Criar dados expandidos para densidade
    expanded_data = []
    for _, row in df.iterrows():
        for _ in range(min(int(row['Frequência']), 30)):
            expanded_data.append({
                'Latitude': row['Latitude'],
                'Longitude': row['Longitude'],
                'Frequência': row['Frequência'],
                'Cidade': row['Cidade']
            })
    
    df_expanded = pd.DataFrame(expanded_data)
    
    # Adicionar pontos de densidade para criar efeito de heatmap
    fig.add_trace(go.Scattergeo(
        lon=df_expanded['Longitude'],
        lat=df_expanded['Latitude'],
        mode='markers',
        marker=dict(
            size=10,
            color=df_expanded['Frequência'],
            colorscale='Hot',
            showscale=True,
            colorbar=dict(
                title=dict(text="Frequência", font=dict(size=16)),
                x=1.02,
                len=0.7
            ),
            opacity=0.7,
            line=dict(width=0),
            cmin=0,
            cmax=df['Frequência'].max()
        ),
        name='Densidade',
        hovertemplate='Frequência: %{marker.color:.0f}<extra></extra>'
    ))
    
    # Adicionar pontos das cidades principais
    top_cities = df.nlargest(15, 'Frequência')
    fig.add_trace(go.Scattergeo(
        lon=top_cities['Longitude'],
        lat=top_cities['Latitude'],
        text=top_cities['Cidade'] + '<br>Freq: ' + top_cities['Frequência'].astype(str),
        mode='markers+text',
        marker=dict(
            size=top_cities['Frequência'] / 4 + 10,
            color='darkred',
            line=dict(width=2, color='black'),
            opacity=0.9
        ),
        textfont=dict(size=11, color='black', family='Arial Black'),
        textposition='top center',
        name='Cidades Principais',
        hovertemplate='<b>%{text}</b><extra></extra>',
        showlegend=False
    ))
    
    # Definir ranges de latitude e longitude do mapa principal (para o minimapa)
    lat_range = (-25.5, -19.5)
    lon_range = (-53, -43)
    
    # Criar minimapa (overview map) antes de configurar o layout principal
    print("Criando minimapa (overview map)...")
    minimap_file = create_minimap_overview(geojson_data, lat_range, lon_range)
    
    # Configurar layout do mapa focando no estado de São Paulo
    fig.update_layout(
        title=dict(
            text='Mapa de Calor - Estado de São Paulo<br><sub>Baseado na Frequência de Cidades</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=24, color='#0066cc', family='Arial')
        ),
        geo=dict(
            scope='south america',
            center=dict(lat=-23.5505, lon=-46.6333),
            projection_scale=8.5,
            showland=True,
            landcolor='rgb(250, 250, 250)',
            countrycolor='rgb(200, 200, 200)',
            coastlinecolor='rgb(200, 200, 200)',
            lataxis=dict(range=[-25.5, -19.5]),
            lonaxis=dict(range=[-53, -43]),
            bgcolor='white',
            showlakes=True,
            lakecolor='rgb(255, 255, 255)',
            showrivers=True,
            rivercolor='rgb(230, 245, 255)',
            showocean=True,
            oceancolor='rgb(230, 245, 255)',
            showcountries=True,
            countrywidth=2,
            showsubunits=True,
            subunitwidth=1.5,
            subunitcolor='rgb(180, 180, 180)',
            framecolor='rgb(100, 100, 100)',
            framewidth=2
        ),
        width=2000,
        height=1600,
        margin=dict(l=0, r=0, t=120, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    # Salvar mapa principal primeiro (sem minimapa via add_layout_image)
    # O add_layout_image pode não funcionar bem com write_image, então vamos compor manualmente
    temp_main_file = output_file.replace('.png', '_temp_main.png')
    print(f"\nGerando imagem PNG do mapa principal...")
    fig.write_image(temp_main_file, width=2000, height=1600, scale=2)
    print(f"Mapa principal salvo: {temp_main_file}")
    
    # Compor a imagem final com o minimapa usando PIL (composição manual)
    if os.path.exists(minimap_file) and os.path.exists(temp_main_file):
        try:
            # Carregar imagens
            main_img = Image.open(temp_main_file)
            minimap_img = Image.open(minimap_file)
            
            print(f"Mapa principal: {main_img.size}")
            print(f"Minimapa: {minimap_img.size}")
            
            # Redimensionar minimapa para ~20% do tamanho do mapa principal
            minimap_size = (int(main_img.width * 0.20), int(main_img.height * 0.20))
            minimap_resized = minimap_img.resize(minimap_size, Image.Resampling.LANCZOS)
            
            # Criar cópia do mapa principal para composição
            final_img = main_img.copy()
            
            # Calcular posição do minimapa (canto inferior direito)
            # Margem de 20 pixels da borda
            x_position = final_img.width - minimap_resized.width - 20
            y_position = final_img.height - minimap_resized.height - 20
            
            print(f"Posicionando minimapa em: ({x_position}, {y_position})")
            
            # Colar minimapa no mapa principal
            # Usar alpha composite para manter transparência se houver
            if minimap_resized.mode == 'RGBA':
                final_img.paste(minimap_resized, (x_position, y_position), minimap_resized)
            else:
                final_img.paste(minimap_resized, (x_position, y_position))
            
            # Salvar imagem final
            final_img.save(output_file, 'PNG', quality=95)
            print(f"Imagem final com minimapa salva: {output_file}")
            
            # Limpar arquivos temporários
            if os.path.exists(temp_main_file):
                os.remove(temp_main_file)
            # Manter minimap_temp.png para debug se necessário
            # os.remove(minimap_file)
            
        except Exception as e:
            print(f"Erro ao compor imagem com minimapa: {e}")
            import traceback
            traceback.print_exc()
            print("Usando apenas o mapa principal...")
            # Se der erro, usar apenas o mapa principal
            import shutil
            shutil.copy(temp_main_file, output_file)
            if os.path.exists(temp_main_file):
                os.remove(temp_main_file)
    else:
        print("Aviso: Arquivos temporários não encontrados, usando apenas mapa principal")
        if os.path.exists(temp_main_file):
            import shutil
            shutil.copy(temp_main_file, output_file)
            os.remove(temp_main_file)
    
    print(f"Total de cidades mapeadas: {len(geocoded_cities)}")

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
        print("GeoJSON não encontrado. Tentando baixar...")
        geojson_data = download_sp_geojson(geojson_file)
    
    # Carregar e contar cidades
    print("\nCarregando dados do CSV...")
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
    
    # Criar imagem
    create_heatmap_with_geojson(geocoded_cities, geojson_data)

if __name__ == '__main__':
    main()

