# Mapa de Calor - Estado de São Paulo

Este documento contém código para gerar um mapa de calor do estado de São Paulo baseado na frequência de cidades no arquivo CSV.

## Análise dos Dados

O arquivo `Regiões e cidades - Página1.csv` contém dados de cidades organizadas por regiões:
- ABC
- Baixada Santista
- Registro
- SJC (São José dos Campos)
- SP
- Cidades Região SP fora o município

### Top 20 Cidades Mais Frequentes:
1. São Paulo: 142 ocorrências
2. São José dos Campos: 70 ocorrências
3. Santos: 70 ocorrências
4. São Bernardo do Campo: 48 ocorrências
5. Santo André: 39 ocorrências
6. Diadema: 32 ocorrências
7. Registro: 25 ocorrências
8. São Vicente: 19 ocorrências
9. Praia Grande: 18 ocorrências
10. Bertioga: 16 ocorrências
11. Jacareí: 16 ocorrências
12. Mauá: 16 ocorrências
13. Peruibe: 16 ocorrências
14. Guarujá: 15 ocorrências
15. Pariquera-Açu: 12 ocorrências
16. Cubatão: 11 ocorrências
17. São Caetano do Sul: 10 ocorrências
18. Barra do Turvo: 9 ocorrências
19. Caçapava: 9 ocorrências
20. Eldorado: 9 ocorrências

## Código para Gerar o Mapa de Calor

### Opção 1: Usando Folium (Mapa Interativo)

```python
import csv
from collections import Counter
import folium
from folium.plugins import HeatMap
import geopy.geocoders
from geopy.geocoders import Nominatim
import time

# Ler o CSV e contar frequências
cities = []
with open('Regiões e cidades - Página1.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # Pular cabeçalho
    for row in reader:
        for city in row:
            city_clean = city.strip()
            if city_clean:
                cities.append(city_clean)

# Contar frequências
city_counts = Counter(cities)

# Configurar geocodificador
geolocator = Nominatim(user_agent="heatmap_sp")

# Coordenadas do estado de São Paulo (centro)
sp_map = folium.Map(location=[-23.5505, -46.6333], zoom_start=7)

# Preparar dados para o heatmap
heat_data = []
geocoded_cities = {}

print("Geocodificando cidades...")
for city, count in city_counts.items():
    # Adicionar "SP, Brasil" para melhorar a precisão
    location_query = f"{city}, São Paulo, Brasil"
    
    try:
        if city not in geocoded_cities:
            location = geolocator.geocode(location_query, timeout=10)
            if location:
                geocoded_cities[city] = (location.latitude, location.longitude)
                # Adicionar ponto múltiplas vezes baseado na frequência
                for _ in range(min(count, 50)):  # Limitar para performance
                    heat_data.append([location.latitude, location.longitude])
            time.sleep(1)  # Rate limiting
        else:
            lat, lon = geocoded_cities[city]
            for _ in range(min(count, 50)):
                heat_data.append([lat, lon])
    except Exception as e:
        print(f"Erro ao geocodificar {city}: {e}")
        continue

# Adicionar heatmap
if heat_data:
    HeatMap(heat_data, radius=15, blur=10, max_zoom=1).add_to(sp_map)

# Adicionar marcadores para as cidades mais frequentes
for city, count in list(city_counts.most_common(10)):
    if city in geocoded_cities:
        lat, lon = geocoded_cities[city]
        folium.CircleMarker(
            location=[lat, lon],
            radius=min(count / 5, 20),
            popup=f"{city}: {count} ocorrências",
            color='red',
            fill=True,
            fillColor='red'
        ).add_to(sp_map)

# Salvar mapa
sp_map.save('heatmap_sao_paulo.html')
print("Mapa salvo como 'heatmap_sao_paulo.html'")
```

### Opção 2: Usando Plotly (Visualização Estatística)

```python
import csv
from collections import Counter
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import geopy.geocoders
from geopy.geocoders import Nominatim
import time

# Ler o CSV e contar frequências
cities = []
with open('Regiões e cidades - Página1.csv', 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # Pular cabeçalho
    for row in reader:
        for city in row:
            city_clean = city.strip()
            if city_clean:
                cities.append(city_clean)

# Contar frequências
city_counts = Counter(cities)

# Geocodificar cidades
geolocator = Nominatim(user_agent="heatmap_sp")
city_data = []

print("Geocodificando cidades...")
for city, count in city_counts.items():
    location_query = f"{city}, São Paulo, Brasil"
    try:
        location = geolocator.geocode(location_query, timeout=10)
        if location:
            city_data.append({
                'Cidade': city,
                'Latitude': location.latitude,
                'Longitude': location.longitude,
                'Frequência': count
            })
        time.sleep(1)
    except Exception as e:
        print(f"Erro ao geocodificar {city}: {e}")
        continue

# Criar DataFrame
df = pd.DataFrame(city_data)

# Criar mapa de calor
fig = go.Figure()

# Adicionar pontos de calor
fig.add_trace(go.Scattergeo(
    lon=df['Longitude'],
    lat=df['Latitude'],
    text=df['Cidade'] + ': ' + df['Frequência'].astype(str) + ' ocorrências',
    mode='markers',
    marker=dict(
        size=df['Frequência'] * 2,
        color=df['Frequência'],
        colorscale='Reds',
        showscale=True,
        colorbar=dict(title="Frequência"),
        line=dict(width=1, color='black')
    ),
    name='Cidades'
))

# Configurar layout
fig.update_layout(
    title='Mapa de Calor - Estado de São Paulo<br>Baseado na Frequência de Cidades',
    geo=dict(
        scope='south america',
        center=dict(lat=-23.5505, lon=-46.6333),
        projection_scale=8,
        showland=True,
        landcolor='rgb(243, 243, 243)',
        countrycolor='rgb(204, 204, 204)',
        lataxis=dict(range=[-25, -20]),
        lonaxis=dict(range=[-52, -44])
    ),
    height=800
)

# Salvar como HTML
fig.write_html('heatmap_sao_paulo_plotly.html')
print("Mapa salvo como 'heatmap_sao_paulo_plotly.html'")
```

### Opção 3: Script Completo com Tratamento de Erros

```python
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
            for city in row:
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
    heat_data = []
    for city, data in geocoded_cities.items():
        lat = data['lat']
        lon = data['lon']
        count = data['count']
        # Adicionar múltiplos pontos baseado na frequência
        for _ in range(min(count, 30)):
            heat_data.append([lat, lon])
    
    # Adicionar heatmap
    if heat_data:
        HeatMap(
            heat_data,
            radius=20,
            blur=15,
            max_zoom=1,
            gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'orange', 1: 'red'}
        ).add_to(sp_map)
    
    # Adicionar marcadores para top 20 cidades
    sorted_cities = sorted(geocoded_cities.items(), 
                          key=lambda x: x[1]['count'], 
                          reverse=True)[:20]
    
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
    
    # Adicionar legenda
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: 90px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <h4>Mapa de Calor - SP</h4>
    <p><i class="fa fa-circle" style="color:blue"></i> Baixa frequência</p>
    <p><i class="fa fa-circle" style="color:red"></i> Alta frequência</p>
    </div>
    '''
    sp_map.get_root().html.add_child(folium.Element(legend_html))
    
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
```

## Instruções de Uso

### Pré-requisitos

Instale as dependências necessárias:

```bash
pip install folium geopy plotly pandas
```

### Executar o Script

1. **Opção 1 (Folium - Recomendado):**
   ```bash
   python3 -c "$(cat << 'EOF'
   # Cole aqui o código da Opção 3
   EOF
   )"
   ```

2. **Ou salve o código da Opção 3 em um arquivo `generate_heatmap.py` e execute:**
   ```bash
   python3 generate_heatmap.py
   ```

3. **O script irá:**
   - Ler o arquivo CSV
   - Contar frequências de cada cidade
   - Geocodificar as cidades (com cache para evitar requisições repetidas)
   - Gerar um mapa HTML interativo (`heatmap_sao_paulo.html`)

### Visualizar o Mapa

Abra o arquivo `heatmap_sao_paulo.html` em um navegador web para visualizar o mapa de calor interativo.

## Observações

- O geocodificador pode levar algum tempo para processar todas as cidades
- Um arquivo `city_coordinates.json` será criado para cache das coordenadas
- Cidades não encontradas serão ignoradas
- O mapa mostra áreas de maior concentração em vermelho/laranja e menor em azul/verde

