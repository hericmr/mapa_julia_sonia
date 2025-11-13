# Mapa de Calor - Estado de São Paulo

Visualização interativa e estática de frequências de cidades no estado de São Paulo usando mapas de calor (heatmaps).

## 📋 Descrição

Este projeto gera mapas de calor baseados em dados de frequência de cidades do estado de São Paulo. Inclui visualizações interativas (HTML/Leaflet) e estáticas (PNG).

## 🚀 Funcionalidades

- **Mapa Interativo Dinâmico** (`heatmap_sao_paulo.html`): Heatmap que filtra cidades de baixa frequência baseado no nível de zoom
- **Mapa Estático** (`index.html`): Visualização fixa como imagem de livro de geografia (usado para GitHub Pages)
- **Imagem PNG** (`heatmap_sao_paulo.png`): Mapa estático com minimap no canto inferior direito
- **Gradiente de cores profissional**: Escala de temperatura (azul → ciano → verde → amarelo → laranja → vermelho)
- **Contorno do estado**: GeoJSON simplificado do estado de São Paulo
- **Caixa informativa**: Lista de cidades e ocorrências no canto superior direito

## 📦 Instalação

```bash
pip install -r requirements.txt
```

## 🎯 Uso

### Gerar mapa interativo dinâmico
```bash
python3 generate_heatmap.py
```

### Gerar mapa estático
```bash
python3 generate_static_heatmap.py
```

### Gerar imagem PNG com minimap
```bash
python3 generate_heatmap_geojson.py
```

## 📁 Estrutura de Arquivos

- `generate_heatmap.py` - Gera mapa interativo com filtragem dinâmica
- `generate_static_heatmap.py` - Gera mapa estático fixo
- `generate_heatmap_geojson.py` - Gera imagem PNG com minimap
- `city_coordinates.json` - Coordenadas geocodificadas das cidades
- `SP_simplified.geojson` - Contorno simplificado do estado de São Paulo
- `Regiões e cidades - Página1.csv` - Dados de origem das cidades

## 🌐 Visualização Online

O mapa estático está disponível via GitHub Pages em: https://hericmr.github.io/mapa_julia_sonia/

O arquivo `index.html` é automaticamente usado como página inicial pelo GitHub Pages.

## 📊 Dados

Os dados são baseados em frequências de cidades do estado de São Paulo, processados a partir do arquivo CSV e geocodificados usando Nominatim.

## 🎨 Características Visuais

- **Borda preta minimalista** nas caixas informativas
- **Gradiente de temperatura** profissional
- **Minimap** mostrando contexto do estado completo
- **Legenda** com valores mínimo e máximo

## 📝 Licença

Este projeto é de uso pessoal.

