# Mapa de Calor com GeoJSON - Estado de São Paulo

Este projeto gera mapas de calor do estado de São Paulo usando **GeoJSON** para os limites exatos do estado.

## Arquivos Criados

### Scripts Python

1. **`generate_heatmap_geojson.py`** ⭐ **RECOMENDADO**
   - Usa GeoJSON para desenhar os limites exatos do estado de São Paulo
   - Baixa automaticamente o GeoJSON se não existir
   - Gera imagem PNG de alta qualidade (4000x3200 pixels)
   - Usa Plotly para visualização

2. **`generate_heatmap_svg.py`**
   - Versão que gera HTML interativo (pode ser convertido para SVG)
   - Usa Folium para visualização
   - Ideal para exportação manual para SVG

3. **`generate_heatmap_image.py`**
   - Versão anterior com limites aproximados
   - Mantida para compatibilidade

### Arquivos de Dados

- **`sp_boundaries.geojson`** (~4.6 MB)
  - GeoJSON com **todos os 645 municípios** do estado de São Paulo
  - Baixado automaticamente do repositório oficial: [tbrugz/geodata-br](https://github.com/tbrugz/geodata-br)
  - URL: `https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-35-mun.json`
  - Contém polígonos detalhados de cada município, formando o contorno completo do estado

- **`city_coordinates.json`**
  - Cache de coordenadas geocodificadas das cidades
  - Evita requisições repetidas à API de geocodificação

- **`heatmap_sao_paulo.png`** (398 KB)
  - Imagem PNG gerada com os limites exatos do estado
  - Resolução: 4000x3200 pixels (2x scale)

## Como Usar

### Gerar Mapa com GeoJSON (Recomendado)

```bash
python3 generate_heatmap_geojson.py
```

Este script irá:
1. Baixar o GeoJSON do estado de São Paulo (se não existir)
2. Carregar dados do CSV
3. Geocodificar cidades (usando cache se disponível)
4. Gerar imagem PNG com limites exatos do estado

### Gerar Mapa Interativo (para exportar SVG)

```bash
python3 generate_heatmap_svg.py
```

Este script gera um arquivo HTML que pode ser:
- Visualizado no navegador
- Exportado para SVG usando ferramentas de desenvolvedor
- Convertido usando conversores online

## Formato GeoJSON

O arquivo `sp_boundaries.geojson` contém:

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "geometry": {
      "type": "MultiPolygon",
      "coordinates": [...]
    },
    "properties": {...}
  }]
}
```

### Usar seu próprio GeoJSON

Se você tiver um arquivo GeoJSON próprio:

1. Coloque o arquivo como `sp_boundaries.geojson` na pasta do projeto
2. Execute `generate_heatmap_geojson.py`
3. O script usará seu arquivo automaticamente

### Fonte do GeoJSON

O GeoJSON usado é do repositório oficial:
- **Repositório**: [tbrugz/geodata-br](https://github.com/tbrugz/geodata-br)
- **Arquivo**: `geojs-35-mun.json` (código 35 = São Paulo)
- **Conteúdo**: Todos os 645 municípios do estado de São Paulo
- **URL**: https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-35-mun.json

Outras fontes disponíveis:
- **IBGE**: Instituto Brasileiro de Geografia e Estatística
- **DataGEO**: Portal do Governo do Estado de São Paulo

## Características do Mapa Gerado

- ✅ **Limites exatos** do estado de São Paulo (645 municípios via GeoJSON oficial)
- ✅ **Heat map** baseado na frequência de cidades
- ✅ **Top 15 cidades** destacadas com círculos proporcionais
- ✅ **Escala de cores** Hot (azul → vermelho)
- ✅ **Alta resolução** (4000x3200 pixels)
- ✅ **Geocodificação** com cache para performance

## Top 10 Cidades Mais Frequentes

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

## Dependências

```bash
pip install -r requirements.txt
```

Principais bibliotecas:
- `plotly>=6.1.1` - Visualização de mapas
- `geopy>=2.3.0` - Geocodificação
- `pandas>=1.3.0` - Manipulação de dados
- `kaleido>=0.2.1` - Exportação de imagens
- `requests>=2.28.0` - Download de GeoJSON

## Exportar para SVG

### Método 1: Usando o navegador
1. Abra o arquivo HTML gerado
2. Pressione F12 (Ferramentas de Desenvolvedor)
3. Use a ferramenta de captura ou extensão de exportação SVG

### Método 2: Usando conversor online
- Upload do HTML para conversores online
- Ou use ferramentas como `html2svg`

### Método 3: Usando Python
```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Configurar Chrome headless
chrome_options = Options()
chrome_options.add_argument('--headless')
driver = webdriver.Chrome(options=chrome_options)

# Carregar HTML e exportar
driver.get('file:///path/to/heatmap_sao_paulo.html')
# Usar biblioteca para converter para SVG
```

## Estrutura de Arquivos

```
mapa de calor/
├── Regiões e cidades - Página1.csv    # Dados de entrada
├── generate_heatmap_geojson.py       # Script principal (GeoJSON)
├── generate_heatmap_svg.py           # Script para SVG
├── generate_heatmap_image.py         # Script alternativo
├── sp_boundaries.geojson             # GeoJSON do estado
├── city_coordinates.json             # Cache de geocodificação
├── heatmap_sao_paulo.png             # Imagem gerada
└── requirements.txt                  # Dependências
```

## Notas

- O GeoJSON é baixado automaticamente na primeira execução
- As coordenadas das cidades são armazenadas em cache
- O script respeita rate limiting da API de geocodificação
- Algumas cidades podem não ser encontradas (ex: nomes incorretos)

## Suporte

Para problemas ou melhorias:
1. Verifique se o GeoJSON foi baixado corretamente
2. Confirme que todas as dependências estão instaladas
3. Verifique o arquivo CSV está no formato correto

