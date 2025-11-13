#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para gerar imagem PNG do mapa de calor do estado de São Paulo
baseado na frequência de cidades no arquivo CSV.
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

def create_heatmap_image(geocoded_cities, output_file='heatmap_sao_paulo.png'):
    """Cria imagem PNG do mapa de calor com limites do estado."""
    
    # Preparar dados
    city_data = []
    for city, data in geocoded_cities.items():
        city_data.append({
            'Cidade': city,
            'Latitude': data['lat'],
            'Longitude': data['lon'],
            'Frequência': data['count']
        })
    
    df = pd.DataFrame(city_data)
    
    # Coordenadas aproximadas dos limites do estado de São Paulo
    sp_boundaries_lat = [-20.8, -20.5, -22.0, -24.0, -25.0, -25.0, -24.5, -23.5, -22.0, -20.8]
    sp_boundaries_lon = [-53.1, -51.0, -48.0, -48.0, -48.5, -47.0, -46.0, -45.0, -44.5, -53.1]
    
    # Criar figura
    fig = go.Figure()
    
    # Adicionar contorno do estado de São Paulo
    fig.add_trace(go.Scattergeo(
        lon=sp_boundaries_lon,
        lat=sp_boundaries_lat,
        mode='lines',
        line=dict(width=3, color='#0066cc'),
        fill='toself',
        fillcolor='rgba(230, 242, 255, 0.3)',
        name='Limites do Estado',
        showlegend=False,
        hoverinfo='skip'
    ))
    
    # Criar dados expandidos para densidade (múltiplos pontos por cidade baseado na frequência)
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
            size=8,
            color=df_expanded['Frequência'],
            colorscale='Hot',
            showscale=True,
            colorbar=dict(
                title=dict(text="Frequência", font=dict(size=14)),
                x=1.02
            ),
            opacity=0.6,
            line=dict(width=0)
        ),
        name='Densidade',
        hovertemplate='Frequência: %{marker.color}<extra></extra>'
    ))
    
    # Adicionar pontos das cidades principais
    top_cities = df.nlargest(15, 'Frequência')
    fig.add_trace(go.Scattergeo(
        lon=top_cities['Longitude'],
        lat=top_cities['Latitude'],
        text=top_cities['Cidade'] + '<br>Freq: ' + top_cities['Frequência'].astype(str),
        mode='markers+text',
        marker=dict(
            size=top_cities['Frequência'] / 3 + 8,
            color=top_cities['Frequência'],
            colorscale='Reds',
            showscale=False,
            line=dict(width=2, color='darkred'),
            opacity=0.8
        ),
        textfont=dict(size=10, color='black'),
        textposition='top center',
        name='Cidades Principais',
        hovertemplate='<b>%{text}</b><extra></extra>'
    ))
    
    # Configurar layout do mapa focando no estado de São Paulo
    fig.update_layout(
        title=dict(
            text='Mapa de Calor - Estado de São Paulo<br><sub>Baseado na Frequência de Cidades</sub>',
            x=0.5,
            xanchor='center',
            font=dict(size=22, color='#0066cc')
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
        width=1800,
        height=1400,
        margin=dict(l=0, r=0, t=100, b=0),
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    # Salvar como PNG
    print(f"\nGerando imagem PNG...")
    fig.write_image(output_file, width=1800, height=1400, scale=2)
    print(f"Imagem salva como '{output_file}'")
    
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
    
    if not geocoded_cities:
        print("Erro: Nenhuma cidade foi geocodificada!")
        return
    
    # Criar imagem
    create_heatmap_image(geocoded_cities)

if __name__ == '__main__':
    main()
