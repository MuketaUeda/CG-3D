# 🎨 Trabalho CG 3D - Sistema Interativo de Computação Gráfica

<div align="center">

![OpenGL](https://img.shields.io/badge/OpenGL-3.3-blue?style=for-the-badge&logo=opengl)
![Python](https://img.shields.io/badge/Python-3.x-green?style=for-the-badge&logo=python)
![PyOpenGL](https://img.shields.io/badge/PyOpenGL-Latest-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

**Sistema avançado de renderização 3D com implementação de algoritmos de iluminação e extrusão poligonal**

[Características](#-características) • [Instalação](#-instalação) • [Uso](#-como-usar) • [Controles](#-controles-completos) • [Algoritmos](#-algoritmos-implementados)

</div>

---

## 📋 Sobre o Projeto

Este projeto é uma aplicação interativa de **Computação Gráfica 3D** desenvolvida em Python usando OpenGL. Implementa técnicas avançadas de renderização, incluindo três modelos de iluminação (Flat, Gouraud e Phong), câmera em primeira pessoa, extrusão de polígonos 2D e **algoritmo Scanline com Phong Shading implementado via software**.

### 🎯 Destaques Técnicos

- ✨ **Iluminação Phong via Scanline** - Implementação manual do algoritmo scanline com interpolação de normais
- 🎮 **Câmera em Primeira Pessoa** - Movimentação WASD + controle de mouse
- 🔨 **Sistema de Extrusão** - Crie objetos 3D a partir de perfis 2D
- 🎨 **Múltiplos Modelos de Iluminação** - Flat Shading, Gouraud Shading e Phong Shading
- 🌐 **Renderização Dual** - Wireframe e sólido com controle em tempo real

---

## ✨ Características

### 🔦 Modelos de Iluminação

| Modelo | Descrição | Técnica |
|--------|-----------|---------|
| **Flat Shading** | Iluminação uniforme por face | Pipeline fixa OpenGL |
| **Gouraud Shading** | Interpolação de cores suave | Pipeline fixa OpenGL |
| **Phong Shading** | Iluminação por pixel com especular | **Scanline implementado via software** |

### 🎲 Objetos 3D Disponíveis

- 🔵 **Esfera** - Subdivisão paramétrica
- 🟦 **Cubo** - Com Phong Scanline no modo 2
- 🔺 **Cone** - Geometria procedural
- 🍩 **Torus** - Superfície de revolução
- 🫖 **Teapot** - Clássico objeto de teste da CG
- 🔨 **Extrusão Customizada** - Crie seus próprios objetos!

### 🎥 Sistema de Câmera

- **Modo Objeto**: Rotaciona o objeto no centro da cena
- **Modo Câmera**: Navegação livre em primeira pessoa (FPS style)
  - Movimentação: `W/A/S/D`
  - Rotação: Movimento do mouse
  - Cursor capturado automaticamente

### 🔧 Sistema de Extrusão

Crie objetos 3D complexos a partir de perfis 2D:

1. **Desenhe o perfil 2D** clicando na tela para adicionar pontos
2. **Visualize em tempo real** o perfil amarelo
3. **Ative a extrusão** com a tecla `[E]` para gerar o objeto 3D
4. **Ajuste a altura** com `[H]` e `[N]`

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.7 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone ou baixe o repositório**
   ```bash
   cd CG-3D
   ```

2. **Crie um ambiente virtual (recomendado)**
   ```bash
   python -m venv venv
   ```

3. **Ative o ambiente virtual**
   
   **Windows (PowerShell):**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   
   **Windows (CMD):**
   ```cmd
   venv\Scripts\activate.bat
   ```
   
   **Linux/Mac:**
   ```bash
   source venv/bin/activate
   ```

4. **Instale as dependências**
   ```bash
   pip install PyOpenGL PyOpenGL_accelerate
   ```

5. **Execute o programa**
   ```bash
   python "Mod python Nick 1.py"
   ```

### ⚠️ Solução de Problemas

**Erro de Política de Execução (Windows PowerShell):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Erro de GLUT/FreeGLUT:**
- Windows: Baixe FreeGLUT de [transmissionzero.co.uk](https://www.transmissionzero.co.uk/software/freeglut-devel/)
- Linux: `sudo apt-get install freeglut3-dev`
- Mac: `brew install freeglut`

---

## 🎮 Como Usar

### Início Rápido

1. Execute o programa
2. Use `[1-5]` para selecionar objetos pré-definidos
3. Pressione `[M]` para alternar entre modelos de iluminação
4. Pressione `[0]` para entrar no modo câmera e navegar livremente
5. Pressione `[6]` para experimentar o modo de extrusão

### 🎨 Criando Objetos com Extrusão

1. Pressione `[6]` para ativar o modo extrusão
2. **Clique com o botão esquerdo** na tela para adicionar pontos ao perfil
3. Os pontos aparecerão conectados em **amarelo** (perfil 2D)
4. Pressione `[E]` para ativar a extrusão 3D
5. Ajuste a altura com `[H]` (aumentar) e `[N]` (diminuir)
6. Pressione `[C]` para limpar e começar de novo

---

## ⌨️ Controles Completos

### 🔄 Controles Gerais

| Tecla | Função |
|-------|--------|
| `[0]` | Alternar Modo Câmera ↔ Modo Objeto |
| `[1]` | Esfera |
| `[2]` | Cubo (com Phong Scanline) |
| `[3]` | Cone |
| `[4]` | Torus |
| `[5]` | Teapot |
| `[6]` | Modo Extrusão |
| `[M]` | Ciclar Iluminação (Flat → Gouraud → Phong) |
| `[P]` | Alternar Projeção (Perspectiva ↔ Ortográfica) |
| `[F]` | Alternar Wireframe ↔ Sólido |
| `[T]` | Mostrar/Ocultar HUD |

### 🎮 Modo Objeto

| Tecla | Função |
|-------|--------|
| `[W]` | Rotacionar para cima |
| `[S]` | Rotacionar para baixo |
| `[A]` | Rotacionar para esquerda |
| `[D]` | Rotacionar para direita |
| `[↑]` | Mover para cima |
| `[↓]` | Mover para baixo |
| `[←]` | Mover para esquerda |
| `[→]` | Mover para direita |
| `[+]` | Aumentar escala |
| `[-]` | Diminuir escala |

### 🎥 Modo Câmera (FPS)

| Controle | Função |
|----------|--------|
| `[W]` | Mover para frente |
| `[S]` | Mover para trás |
| `[A]` | Mover para esquerda |
| `[D]` | Mover para direita |
| **Mouse** | Olhar ao redor |

### 💡 Controle de Luz

| Tecla | Função |
|-------|--------|
| `[I]` | Luz para cima |
| `[K]` | Luz para baixo |
| `[J]` | Luz para esquerda |
| `[L]` | Luz para direita |
| `[U]` | Luz para frente |
| `[O]` | Luz para trás |

### 🔨 Modo Extrusão

| Controle | Função |
|----------|--------|
| **Clique Esquerdo** | Adicionar ponto ao perfil |
| `[E]` | Ativar/Desativar extrusão 3D |
| `[C]` | Limpar perfil |
| `[H]` | Aumentar altura de extrusão |
| `[N]` | Diminuir altura de extrusão |

---

## 🧮 Algoritmos Implementados

### 1️⃣ Scanline com Phong Shading (Software)

Implementação manual do algoritmo de **varredura por linha** com iluminação Phong calculada **por pixel**:

**Etapas do Algoritmo:**

1. **Projeção 3D → 2D**
   - Usa `gluProject` para converter vértices 3D em coordenadas de tela
   
2. **Ordenação de Vértices**
   - Ordena os três vértices do triângulo por coordenada Y

3. **Varredura Scanline**
   - Para cada linha Y do triângulo:
     - Calcula intersecções com as arestas
     - Interpola posição 3D (P) e normal (N)
   
4. **Interpolação Horizontal**
   - Para cada pixel X entre as intersecções:
     - Interpola P e N linearmente
     - Normaliza o vetor N

5. **Cálculo Phong por Pixel**
   ```
   I = Ia·ka + Id·kd·(N·L) + Is·ks·(R·V)^n
   ```
   - Ia: Luz ambiente
   - Id: Luz difusa
   - Is: Luz especular
   - ka, kd, ks: Coeficientes do material
   - n: Shininess (brilho)

**Vantagem:** Cálculo preciso de reflexo especular por pixel, resultando em highlights mais realistas.

### 2️⃣ Extrusão Linear

Transforma um perfil 2D em um objeto 3D:

- **Input:** Lista de pontos (x, y) no plano XY
- **Processo:** 
  1. Fecha o perfil automaticamente
  2. Replica o perfil em N níveis ao longo do eixo Z
  3. Conecta pontos consecutivos formando faces laterais (quads → triângulos)
  4. Gera faces de topo e base usando triangulação em leque
- **Output:** Malha 3D com normais calculadas

**Nota:** A triangulação em leque funciona melhor para perfis convexos. Para perfis côncavos ou auto-intersectantes (como "X"), as tampas podem apresentar artefatos visuais.

### 3️⃣ Cálculo de Normais

```python
def calcular_normal_face(p1, p2, p3):
    v1 = p2 - p1
    v2 = p3 - p1
    N = v1 × v2  # Produto vetorial
    return normalize(N)
```

---

## 📁 Estrutura do Projeto

```
CG-3D/
│
├── Mod python Nick 1.py    # Código principal
├── README.md               # Este arquivo
├── LICENSE                 # Licença MIT
├── requirements.txt        # Dependências (a criar)
│
└── venv/                   # Ambiente virtual (ignorado pelo git)
    ├── Scripts/
    └── Lib/
```

---

## 🎓 Conceitos de Computação Gráfica Demonstrados

### Pipeline Gráfico
- ✅ Transformações modelview (translação, rotação, escala)
- ✅ Projeção perspectiva e ortográfica
- ✅ Clipping e viewport

### Iluminação
- ✅ Modelo de Phong (ambiente + difusa + especular)
- ✅ Flat Shading (iluminação por face)
- ✅ Gouraud Shading (interpolação de cores)
- ✅ Phong Shading (interpolação de normais)

### Geometria
- ✅ Primitivas 3D (esfera, cubo, cone, torus)
- ✅ Cálculo de normais
- ✅ Triangulação de polígonos
- ✅ Extrusão linear

### Algoritmos de Rasterização
- ✅ Scanline com interpolação
- ✅ Depth buffer (Z-buffer)
- ✅ Projeção perspectiva

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.x** - Linguagem de programação
- **PyOpenGL** - Bindings Python para OpenGL
- **PyOpenGL_accelerate** - Otimizações de performance
- **OpenGL 3.3** - API gráfica
- **GLUT** - Toolkit para janelas e entrada

---

## 📝 Notas Técnicas

### Performance

- O **algoritmo scanline** é executado em **CPU** (software rendering)
- Para melhor performance, use objetos menores no modo Phong
- O cubo é o único objeto que usa scanline no modo Phong
- Outros objetos usam o pipeline fixo do OpenGL

### Limitações Conhecidas

1. **Extrusão com perfis côncavos**: A triangulação das tampas pode gerar artefatos
   - **Solução**: Mantenha perfis convexos ou use apenas as laterais (modo wireframe)

2. **Scanline em superfícies curvas**: Implementado apenas no cubo
   - **Razão**: Complexidade de interpolação em malhas arbitrárias

3. **Mouse capturado no modo câmera**: Cursor fica invisível
   - **Solução**: Pressione `[0]` para voltar ao modo objeto

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👨‍💻 Autores

**Gabriel B. Rosati & Nicolas Zimmer**


Desenvolvido como trabalho acadêmico de Computação Gráfica.

---

## 📚 Referências

- [OpenGL Documentation](https://www.opengl.org/documentation/)
- [PyOpenGL Documentation](http://pyopengl.sourceforge.net/documentation/)
- [Learn OpenGL](https://learnopengl.com/)
- Computer Graphics: Principles and Practice (Foley, van Dam, Feiner, Hughes)
- Real-Time Rendering (Akenine-Möller, Haines, Hoffman)

---

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela! ⭐**

</div>
