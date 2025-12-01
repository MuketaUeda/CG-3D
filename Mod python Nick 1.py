"""
================================================================================
TRABALHO DE COMPUTAÇÃO GRÁFICA 3D
================================================================================

Sistema interativo de renderização 3D com múltiplos modelos de iluminação,
câmera em primeira pessoa e sistema de extrusão de polígonos.

Características principais:
- 3 modelos de iluminação: Flat, Gouraud e Phong
- Algoritmo Scanline com Phong Shading implementado no cubo
- Câmera em primeira pessoa com controle de mouse
- Sistema de extrusão de perfis 2D para objetos 3D
- 5 objetos 3D pré-definidos + extrusão customizada

Autor: Gabriel B. Rosati e Nicolas 
Tecnologias: Python 3.x, PyOpenGL, OpenGL 3.3
================================================================================
"""
import sys
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# ==========================================
# VARIÁVEIS GLOBAIS
# ==========================================
# Estado do Objeto
rot_x, rot_y = 0.0, 0.0
pos_x, pos_y, pos_z = 0.0, 0.0, 0.0
scale = 1.0

# Estado da Luz
luz_x, luz_y, luz_z = 5.0, 5.0, 5.0

# Estado da Câmera/Visualização
projecao_ortografica = False  # False=Perspectiva, True=Ortográfica

# Estado da Câmera em Primeira Pessoa
modo_camera = False  # False=Controla Objeto, True=Controla Câmera
camera_x, camera_y, camera_z = 0.0, 0.0, 10.0
camera_yaw = 0.0    # Rotação horizontal (esquerda/direita)
camera_pitch = 0.0  # Rotação vertical (cima/baixo)
velocidade_camera = 0.1
sensibilidade_mouse = 0.1
ultimo_mouse_x = 0
ultimo_mouse_y = 0
mouse_capturado = False

# Estado da Iluminação
# 0: Flat, 1: Gouraud (Suave), 2: Phong (Scanline no cubo)
modelo_iluminacao = 0

# Estado de Renderização
modo_wireframe = False

# Estado do Objeto Selecionado
# 1=Esfera, 2=Cubo, 3=Cone, 4=Torus, 5=Teapot, 6=Modo Extrusão
objeto_selecionado = 1  # Começa com esfera
modo_extrusao = False

# Estado do Modo Extrusão
perfil_extrusao = []
altura_extrusao = 2.0
num_segmentos_extrusao = 20
extrusao_ativa = False

# Mostrar comandos na tela
mostrar_comandos = True


# ==========================================
# INIT E CONFIGURAÇÃO DE LUZ
# ==========================================
def init():
    """Configurações iniciais do OpenGL"""
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)

    # Normais renormalizadas automaticamente
    glEnable(GL_NORMALIZE)
    
    # Luz
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    
    luz_ambiente = [0.2, 0.2, 0.2, 1.0]
    luz_difusa   = [0.7, 0.7, 0.7, 1.0]
    luz_especular= [1.0, 1.0, 1.0, 1.0]
    
    glLightfv(GL_LIGHT0, GL_AMBIENT, luz_ambiente)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, luz_difusa)
    glLightfv(GL_LIGHT0, GL_SPECULAR, luz_especular)
    
    # Materiais
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)


def configurar_iluminacao_renderizacao():
    """
    Configura o modelo de iluminação do OpenGL (pipeline fixa).
    
    3 Modelos Implementados:
    
    0 - FLAT SHADING:
        - Uma cor por face (glShadeModel(GL_FLAT))
        - Sem reflexo especular
        - Visual "facetado", mostra claramente as faces
        
    1 - GOURAUD SHADING:
        - Cores interpoladas suavemente entre vértices (GL_SMOOTH)
        - Sem reflexo especular
        - Visual suave, mas sem brilho
        
    2 - PHONG SHADING (simulado):
        - Para objetos padrão: usa GL_SMOOTH + material especular forte
        - Para CUBO: usa scanline Phong implementado via software
        - Reflexos especulares precisos e realistas
        
    Nota: O cubo no modo 2 NÃO usa esta função, usa scanline_phong_triangle().
    """
    global modelo_iluminacao
    
    if modelo_iluminacao == 0: 
        # FLAT SHADING - Uma cor por face
        glShadeModel(GL_FLAT)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])  # Sem especular
        glMaterialf(GL_FRONT, GL_SHININESS, 0)
        
    elif modelo_iluminacao == 1:
        # GOURAUD - Interpolação suave de cores, sem especular
        glShadeModel(GL_SMOOTH)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])  # Sem especular
        glMaterialf(GL_FRONT, GL_SHININESS, 0)
        
    elif modelo_iluminacao == 2:
        # PHONG - Interpolação suave + reflexo especular forte
        glShadeModel(GL_SMOOTH)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1, 1, 1, 1])  # Especular máximo
        glMaterialf(GL_FRONT, GL_SHININESS, 60.0)  # Alto brilho


# ==========================================
# PROJEÇÃO 3D → 2D
# ==========================================
def project_to_screen(x, y, z):
    """
    Projeta um ponto 3D para coordenadas de janela 2D (pixels).
    
    Usa as matrizes de modelview e projeção atuais do OpenGL para
    transformar coordenadas 3D do mundo em coordenadas de tela.
    
    Args:
        x, y, z: Coordenadas 3D no espaço do mundo
        
    Returns:
        tuple: (winX, winY, winZ) coordenadas de janela
               - winX, winY: posição em pixels na tela
               - winZ: profundidade (para z-buffer)
               
    Nota: O eixo Y é invertido para corresponder ao sistema de
          coordenadas de janela (origem no canto superior esquerdo).
    """
    model = glGetDoublev(GL_MODELVIEW_MATRIX)
    proj = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)

    winX, winY, winZ = gluProject(x, y, z, model, proj, viewport)
    # Inverte o Y para sistema de janela (Y cresce para baixo)
    winY = viewport[3] - winY
    return winX, winY, winZ


# ==========================================
# ILUMINAÇÃO PHONG POR PIXEL
# ==========================================
def phong_shading_point(position, normal, base_color):
    """
    Calcula a iluminação Phong para um único ponto/pixel.
    
    Implementa o modelo de iluminação de Phong completo:
    I = Ia·ka + Id·kd·(N·L) + Is·ks·(R·V)^shininess
    
    Componentes:
    - Ambiente (Ia): Luz de fundo constante
    - Difusa (Id): Reflexão difusa proporcional ao ângulo da luz (Lambert)
    - Especular (Is): Reflexo brilhante dependente do ângulo de visão
    
    Args:
        position: [x, y, z] posição 3D do ponto no espaço do mundo
        normal: [nx, ny, nz] vetor normal (interpolado) no ponto
        base_color: (r, g, b) cor base do material
        
    Returns:
        tuple: (r, g, b) cor final iluminada do ponto
        
    Nota: Esta função é chamada para CADA PIXEL no algoritmo scanline,
          tornando-a computacionalmente cara mas visualmente precisa.
    """
    global luz_x, luz_y, luz_z, modo_camera
    global camera_x, camera_y, camera_z

    # Vetor L (luz)
    L = [luz_x - position[0], luz_y - position[1], luz_z - position[2]]
    L_len = math.sqrt(L[0]**2 + L[1]**2 + L[2]**2)
    if L_len != 0:
        L = [L[0]/L_len, L[1]/L_len, L[2]/L_len]

    # Normal N
    N = list(normal)
    N_len = math.sqrt(N[0]**2 + N[1]**2 + N[2]**2)
    if N_len != 0:
        N = [N[0]/N_len, N[1]/N_len, N[2]/N_len]
    else:
        N = [0.0, 0.0, 1.0]

    # Vetor para a câmera V
    if modo_camera:
        eye = [camera_x, camera_y, camera_z]
    else:
        eye = [0.0, 0.0, 10.0]

    V = [eye[0] - position[0], eye[1] - position[1], eye[2] - position[2]]
    V_len = math.sqrt(V[0]**2 + V[1]**2 + V[2]**2)
    if V_len != 0:
        V = [V[0]/V_len, V[1]/V_len, V[2]/V_len]

    # Coeficientes Phong
    ka = 0.2
    kd = 0.7
    ks = 0.8
    shininess = 32.0

    # Ambiente
    I = ka

    # Difuso
    NdotL = max(0.0, N[0]*L[0] + N[1]*L[1] + N[2]*L[2])
    I += kd * NdotL

    # Especular
    if NdotL > 0:
        R = [
            2*NdotL*N[0] - L[0],
            2*NdotL*N[1] - L[1],
            2*NdotL*N[2] - L[2]
        ]
        RdotV = max(0.0, R[0]*V[0] + R[1]*V[1] + R[2]*V[2])
        I += ks * (RdotV ** shininess)

    I = min(1.0, max(0.0, I))

    return (I*base_color[0], I*base_color[1], I*base_color[2])


# ==========================================
# SCANLINE PHONG EM TRIÂNGULO
# ==========================================
def scanline_phong_triangle(p1, n1, p2, n2, p3, n3, base_color):
    """
    Renderiza um triângulo usando o algoritmo Scanline com Phong Shading.
    
    Este é um algoritmo de rasterização IMPLEMENTADO EM SOFTWARE (CPU),
    ao contrário do pipeline de hardware do OpenGL. Permite controle total
    sobre o processo de iluminação por pixel.
    
    ALGORITMO:
    1. Projeção: Converte vértices 3D (p1, p2, p3) para coordenadas de tela
    2. Ordenação: Ordena vértices por coordenada Y (de cima para baixo)
    3. Varredura Y (Scanline):
       - Para cada linha y do triângulo:
         a) Calcula intersecções com as 3 arestas
         b) Interpola posições 3D (P) e normais (N) nas intersecções
    4. Varredura X (dentro de cada scanline):
       - Para cada pixel x entre as intersecções:
         a) Interpola P e N horizontalmente
         b) Calcula iluminação Phong para P e N interpolados
         c) Desenha o pixel com a cor calculada
    
    Args:
        p1, p2, p3: Vértices do triângulo [x, y, z] no espaço 3D
        n1, n2, n3: Normais dos vértices [nx, ny, nz]
        base_color: Cor base do material (r, g, b)
        
    Complexidade: O(pixels_do_triângulo) - cada pixel é processado individualmente
    
    Resultado: Iluminação Phong precisa com reflexos especulares suaves e realistas.
    """
    s1 = project_to_screen(*p1)
    s2 = project_to_screen(*p2)
    s3 = project_to_screen(*p3)

    verts = sorted(
        [(s1, p1, n1), (s2, p2, n2), (s3, p3, n3)],
        key=lambda v: v[0][1]
    )

    (x1, y1, _), P1, N1 = verts[0]
    (x2, y2, _), P2, N2 = verts[1]
    (x3, y3, _), P3, N3 = verts[2]

    y_min = int(math.floor(y1))
    y_max = int(math.ceil(y3))

    def edge_intersection(sA, PA, NA, sB, PB, NB, y):
        xA, yA, _ = sA
        xB, yB, _ = sB
        if yA == yB:
            return None
        if (y < min(yA, yB)) or (y >= max(yA, yB)):
            return None
        t = (y - yA) / (yB - yA)
        x = xA + t * (xB - xA)
        P = [PA[i] + t*(PB[i]-PA[i]) for i in range(3)]
        N = [NA[i] + t*(NB[i]-NA[i]) for i in range(3)]
        return x, P, N

    # Desliga iluminação fixa (vamos colorir "na mão")
    glDisable(GL_LIGHTING)

    for y in range(y_min, y_max + 1):
        intersecoes = []

        e = edge_intersection(verts[0][0], P1, N1, verts[1][0], P2, N2, y)
        if e is not None:
            intersecoes.append(e)

        e = edge_intersection(verts[1][0], P2, N2, verts[2][0], P3, N3, y)
        if e is not None:
            intersecoes.append(e)

        e = edge_intersection(verts[2][0], P3, N3, verts[0][0], P1, N1, y)
        if e is not None:
            intersecoes.append(e)

        if len(intersecoes) < 2:
            continue

        intersecoes.sort(key=lambda x: x[0])
        xL, PL, NL = intersecoes[0]
        xR, PR, NR = intersecoes[1]

        if xL == xR:
            continue

        x_start = int(math.floor(xL))
        x_end = int(math.ceil(xR))

        glBegin(GL_POINTS)
        for x in range(x_start, x_end + 1):
            t = (x - xL) / (xR - xL + 1e-9)

            P = [PL[i] + t*(PR[i]-PL[i]) for i in range(3)]
            N = [NL[i] + t*(NR[i]-NL[i]) for i in range(3)]

            # Normaliza N
            L = math.sqrt(N[0]*N[0] + N[1]*N[1] + N[2]*N[2])
            if L != 0:
                N = [N[0]/L, N[1]/L, N[2]/L]
            else:
                N = [0.0, 0.0, 1.0]

            cor = phong_shading_point(P, N, base_color)
            glColor3f(*cor)
            glVertex3f(P[0], P[1], P[2])
        glEnd()

    glEnable(GL_LIGHTING)


# ==========================================
# CUBO COM SCANLINE PHONG
# ==========================================
def desenhar_cubo_scanline_phong():
    """Cubo de lado 2 ([-1,1]) desenhado com Phong por scanline."""
    base_color = (0.0, 0.5, 1.0)

    def face(p0, p1, p2, p3, N):
        scanline_phong_triangle(p0, N, p1, N, p2, N, base_color)
        scanline_phong_triangle(p0, N, p2, N, p3, N, base_color)

    # Frente (z=1)
    N = [0.0, 0.0, 1.0]
    face([-1.0,-1.0, 1.0],
         [ 1.0,-1.0, 1.0],
         [ 1.0, 1.0, 1.0],
         [-1.0, 1.0, 1.0], N)

    # Trás (z=-1)
    N = [0.0, 0.0,-1.0]
    face([ 1.0,-1.0,-1.0],
         [-1.0,-1.0,-1.0],
         [-1.0, 1.0,-1.0],
         [ 1.0, 1.0,-1.0], N)

    # Direita (x=1)
    N = [1.0, 0.0, 0.0]
    face([ 1.0,-1.0, 1.0],
         [ 1.0,-1.0,-1.0],
         [ 1.0, 1.0,-1.0],
         [ 1.0, 1.0, 1.0], N)

    # Esquerda (x=-1)
    N = [-1.0, 0.0, 0.0]
    face([-1.0,-1.0,-1.0],
         [-1.0,-1.0, 1.0],
         [-1.0, 1.0, 1.0],
         [-1.0, 1.0,-1.0], N)

    # Topo (y=1)
    N = [0.0, 1.0, 0.0]
    face([-1.0, 1.0, 1.0],
         [ 1.0, 1.0, 1.0],
         [ 1.0, 1.0,-1.0],
         [-1.0, 1.0,-1.0], N)

    # Base (y=-1)
    N = [0.0,-1.0, 0.0]
    face([-1.0,-1.0,-1.0],
         [ 1.0,-1.0,-1.0],
         [ 1.0,-1.0, 1.0],
         [-1.0,-1.0, 1.0], N)


# ==========================================
# AUXILIARES PARA EXTRUSÃO
# ==========================================
def calcular_normal_face(p1, p2, p3):
    """
    Calcula o vetor normal de uma face triangular.
    
    Usa o produto vetorial (cross product) de dois vetores da face:
    N = (p2 - p1) × (p3 - p1)
    
    O vetor normal é perpendicular à superfície e aponta "para fora" da face.
    Essencial para cálculos de iluminação (determina quanto de luz atinge a face).
    
    Args:
        p1, p2, p3: Vértices do triângulo [x, y, z] em ordem anti-horária
        
    Returns:
        list: [nx, ny, nz] vetor normal NORMALIZADO (comprimento = 1)
              Se degenera (área zero), retorna [0, 0, 1]
    """
    # Calcula dois vetores da face
    v1 = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]
    v2 = [p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]]
    
    # Produto vetorial: v1 × v2
    nx = v1[1] * v2[2] - v1[2] * v2[1]
    ny = v1[2] * v2[0] - v1[0] * v2[2]
    nz = v1[0] * v2[1] - v1[1] * v2[0]
    
    # Normaliza (transforma em vetor unitário)
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length > 0:
        return [nx/length, ny/length, nz/length]
    return [0, 0, 1]  # Fallback para face degenerada


def desenhar_perfil_2d():
    """Desenha o perfil 2D como linhas no plano XY"""
    global perfil_extrusao
    
    if len(perfil_extrusao) < 2:
        return
    
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 0.0)  # Amarelo
    glLineWidth(2.0)
    
    glBegin(GL_LINE_STRIP)
    for ponto in perfil_extrusao:
        glVertex3f(ponto[0], ponto[1], 0.0)
    glEnd()
    
    glEnable(GL_LIGHTING)
    glLineWidth(1.0)


def desenhar_extrusao():
    """
    Renderiza um objeto 3D gerado por extrusão linear de um perfil 2D.
    
    PROCESSO DE EXTRUSÃO:
    1. Perfil 2D: Lista de pontos (x, y) no plano XY
    2. Fechamento: Conecta o último ponto ao primeiro automaticamente
    3. Replicação: Copia o perfil em múltiplos níveis ao longo do eixo Z
    4. Geração de Faces:
       - Laterais: Conecta pontos correspondentes entre níveis (quads → triângulos)
       - Base: Triangulação em leque a partir do ponto [0]
       - Topo: Triangulação em leque a partir do ponto [0]
    
    ESTADOS:
    - extrusao_ativa = False: Mostra apenas o perfil 2D (linhas amarelas)
    - extrusao_ativa = True: Renderiza o objeto 3D completo
    
    MODOS DE RENDERIZAÇÃO:
    - Wireframe: Desenha apenas arestas (anéis + verticais)
    - Sólido: Renderiza faces triangulares com iluminação
    
    LIMITAÇÃO: A triangulação em leque funciona melhor para perfis convexos.
               Perfis côncavos ou auto-intersectantes podem gerar artefatos visuais.
               
    Usa: Pipeline fixo do OpenGL (sem scanline)
    """
    global perfil_extrusao, altura_extrusao
    global num_segmentos_extrusao, modo_wireframe, extrusao_ativa
    
    # Se a extrusão não está ativa, mostra apenas o perfil 2D
    if not extrusao_ativa:
        desenhar_perfil_2d()
        return
    
    if len(perfil_extrusao) < 3:
        desenhar_perfil_2d()
        return
    
    # Fecha perfil
    perfil = perfil_extrusao.copy()
    if perfil[0] != perfil[-1]:
        perfil.append(perfil[0])
    
    num_pontos = len(perfil)
    num_seg = num_segmentos_extrusao
    
    if modo_wireframe:
        glDisable(GL_LIGHTING)
        # Anéis
        for i in range(num_seg + 1):
            z = (i / num_seg) * altura_extrusao
            glBegin(GL_LINE_LOOP)
            for ponto in perfil:
                glVertex3f(ponto[0], ponto[1], z)
            glEnd()
        
        # Verticais
        for ponto in perfil:
            glBegin(GL_LINE_STRIP)
            for i in range(num_seg + 1):
                z = (i / num_seg) * altura_extrusao
                glVertex3f(ponto[0], ponto[1], z)
            glEnd()
        glEnable(GL_LIGHTING)
    else:
        # Faces sólidas (OpenGL normal)
        glBegin(GL_TRIANGLES)
        
        # Faces laterais
        for i in range(num_seg):
            z1 = (i / num_seg) * altura_extrusao
            z2 = ((i + 1) / num_seg) * altura_extrusao
            
            for j in range(num_pontos - 1):
                p1 = [perfil[j][0],     perfil[j][1],     z1]
                p2 = [perfil[j+1][0],   perfil[j+1][1],   z1]
                p3 = [perfil[j][0],     perfil[j][1],     z2]
                p4 = [perfil[j+1][0],   perfil[j+1][1],   z2]
                
                n1 = calcular_normal_face(p1, p2, p3)
                n2 = calcular_normal_face(p2, p4, p3)
                
                glNormal3f(*n1)
                glVertex3f(*p1); glVertex3f(*p2); glVertex3f(*p3)
                
                glNormal3f(*n2)
                glVertex3f(*p2); glVertex3f(*p4); glVertex3f(*p3)
        
        # Base inferior
        if num_pontos > 2:
            z_base = 0.0
            for j in range(1, num_pontos - 1):
                p1 = [perfil[0][0], perfil[0][1], z_base]
                p2 = [perfil[j][0], perfil[j][1], z_base]
                p3 = [perfil[j+1][0], perfil[j+1][1], z_base]
                
                normal = calcular_normal_face(p1, p3, p2)
                glNormal3f(*normal)
                glVertex3f(*p1); glVertex3f(*p2); glVertex3f(*p3)
        
        # Face superior (topo)
        if num_pontos > 2:
            z_topo = altura_extrusao
            for j in range(1, num_pontos - 1):
                p1 = [perfil[0][0], perfil[0][1], z_topo]
                p2 = [perfil[j][0], perfil[j][1], z_topo]
                p3 = [perfil[j+1][0], perfil[j+1][1], z_topo]
                
                normal = calcular_normal_face(p1, p2, p3)
                glNormal3f(*normal)
                glVertex3f(*p1); glVertex3f(*p2); glVertex3f(*p3)
        
        glEnd()


def adicionar_ponto_perfil(x, y):
    """Adiciona um ponto ao perfil de extrusão"""
    global perfil_extrusao
    perfil_extrusao.append((x, y))
    print(f"Ponto adicionado: ({x:.2f}, {y:.2f}). Total: {len(perfil_extrusao)} pontos")


def limpar_perfil():
    """Limpa o perfil de extrusão"""
    global perfil_extrusao
    perfil_extrusao = []
    print("Perfil limpo")


# ==========================================
# OBJETOS PADRÃO + EXTRUSÃO
# ==========================================
def desenhar_objeto():
    """Desenha o objeto padrão selecionado ou extrusão."""
    global objeto_selecionado, modo_wireframe, modo_extrusao, modelo_iluminacao
    
    if modo_extrusao:
        desenhar_extrusao()
        return
    
    glColor3f(0.0, 0.5, 1.0) # Azul
    
    if objeto_selecionado == 1:  # Esfera
        if modo_wireframe:
            glutWireSphere(1.0, 10, 10)
        else:
            glutSolidSphere(1.0, 20, 20)
    
    elif objeto_selecionado == 2:  # Cubo
        if modo_wireframe:
            glutWireCube(2.0)
        else:
            # Em modo Phong, usamos nosso cubo com scanline
            if modelo_iluminacao == 2:
                desenhar_cubo_scanline_phong()
            else:
                glutSolidCube(2.0)
    
    elif objeto_selecionado == 3:  # Cone
        if modo_wireframe:
            glutWireCone(1.0, 2.0, 15, 15)
        else:
            glutSolidCone(1.0, 2.0, 15, 15)
    
    elif objeto_selecionado == 4:  # Torus
        if modo_wireframe:
            glutWireTorus(0.5, 1.0, 15, 15)
        else:
            glutSolidTorus(0.5, 1.0, 15, 15)
    
    elif objeto_selecionado == 5:  # Teapot
        if modo_wireframe:
            glutWireTeapot(1.0)
        else:
            # Teapot
            glutSolidTeapot(1.0)


# ==========================================
# CÂMERA EM PRIMEIRA PESSOA
# ==========================================
def atualizar_camera():
    """
    Atualiza a matriz de visualização para câmera em primeira pessoa.
    
    Sistema de rotação:
    - Yaw (rotação horizontal): Ângulo ao redor do eixo Y (esquerda/direita)
    - Pitch (rotação vertical): Ângulo ao redor do eixo X (cima/baixo)
    
    Converte ângulos Euler (yaw, pitch) em vetor de direção usando trigonometria:
    - direcao_x = cos(pitch) * sin(yaw)
    - direcao_y = sin(pitch)
    - direcao_z = cos(pitch) * cos(yaw)
    
    Calcula ponto de foco (look_at) = posição_câmera + direção
    
    Aplica transformação usando gluLookAt(eye, center, up)
    """
    global camera_x, camera_y, camera_z, camera_yaw, camera_pitch
    
    yaw_rad = math.radians(camera_yaw)
    pitch_rad = math.radians(camera_pitch)
    
    direcao_x = math.cos(pitch_rad) * math.sin(yaw_rad)
    direcao_y = math.sin(pitch_rad)
    direcao_z = math.cos(pitch_rad) * math.cos(yaw_rad)
    
    look_at_x = camera_x + direcao_x
    look_at_y = camera_y + direcao_y
    look_at_z = camera_z + direcao_z
    
    gluLookAt(camera_x, camera_y, camera_z,
              look_at_x, look_at_y, look_at_z,
              0.0, 1.0, 0.0)


def mover_camera_frente():
    """Move a câmera para frente na direção em que está olhando (tecla W)."""
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    yaw_rad = math.radians(camera_yaw)
    # Move apenas no plano XZ (horizontal), Y permanece constante
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera


def mover_camera_tras():
    """Move a câmera para trás, oposto à direção de visão (tecla S)."""
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    yaw_rad = math.radians(camera_yaw)
    camera_x -= math.sin(yaw_rad) * velocidade_camera
    camera_z -= math.cos(yaw_rad) * velocidade_camera


def mover_camera_esquerda():
    """Movimento lateral para a esquerda (strafe) - tecla A."""
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    # Adiciona 90° ao yaw para obter direção perpendicular (esquerda)
    yaw_rad = math.radians(camera_yaw + 90)
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera


def mover_camera_direita():
    """Movimento lateral para a direita (strafe) - tecla D."""
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    # Subtrai 90° do yaw para obter direção perpendicular (direita)
    yaw_rad = math.radians(camera_yaw - 90)
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera


# ==========================================
# HUD / TEXTOS
# ==========================================
def desenhar_texto_2d(x, y, texto):
    glRasterPos2f(x, y)
    for ch in texto:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))


def desenhar_hud():
    global mostrar_comandos, modo_camera, modelo_iluminacao
    global modo_wireframe, projecao_ortografica, modo_extrusao, extrusao_ativa, objeto_selecionado

    if not mostrar_comandos:
        return

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)

    glOrtho(0, width, 0, height, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)

    glColor3f(1.0, 1.0, 1.0)

    y = height - 20
    x = 10

    modo_str = "CAMERA" if modo_camera else "OBJETO"
    modos_ilum = ["Flat", "Gouraud", "Phong"]
    ilum_str = modos_ilum[modelo_iluminacao]
    wire_str = "Wireframe" if modo_wireframe else "Solido"
    proj_str = "Ortografica" if projecao_ortografica else "Perspectiva"
    extru_str = "OFF"
    if modo_extrusao:
        extru_str = "Perfil 2D" if not extrusao_ativa else "Extrusao 3D"

    obj_nomes = {
        1: "Esfera",
        2: "Cubo",
        3: "Cone",
        4: "Torus",
        5: "Teapot"
    }
    obj_str = obj_nomes.get(objeto_selecionado, "-")
    if modo_extrusao:
        obj_str = "Extrusao"

    linhas = [
        f"Modo: {modo_str}   |   Objeto: {obj_str}",
        f"Iluminacao [M]: {ilum_str}   |   Renderizacao [F]: {wire_str}   |   Projecao [P]: {proj_str}",
        f"[0] Camera/Objeto  |  [1-5] Objetos  |  [6] Modo Extrusao ({extru_str})",
        "[WASD] (Obj: rotacao / Cam: movimento)  |  Setas: mover objeto",
        "[IJKL/UO] mover luz   |   [T] mostrar/ocultar ajuda na tela",
        "[Extrusao] Clique: adiciona ponto  |  [E] ativa extrusao  |  [C] limpa  |  [H/N] altura"
    ]

    for linha in linhas:
        desenhar_texto_2d(x, y, linha)
        y -= 20

    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)

    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


# ==========================================
# DISPLAY / RENDER (Loop Principal)
# ==========================================
def display():
    """
    Função principal de renderização, chamada a cada frame.
    
    PIPELINE DE RENDERIZAÇÃO:
    1. Limpa buffers (cor + profundidade)
    2. Configura câmera (fixa ou primeira pessoa)
    3. Posiciona fonte de luz
    4. Desenha indicador visual da luz (esfera amarela)
    5. Configura modelo de iluminação
    6. Aplica transformações no objeto (translação, rotação, escala)
    7. Desenha o objeto selecionado
    8. Desenha HUD (texto 2D) por cima
    9. Troca buffers (double buffering)
    """
    global modo_camera, luz_x, luz_y, luz_z
    global pos_x, pos_y, pos_z, rot_x, rot_y, scale
    
    # 1. Limpa a tela e o buffer de profundidade
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # 2. Configura câmera
    if modo_camera:
        # Câmera em primeira pessoa (FPS)
        atualizar_camera()
    else:
        # Câmera fixa olhando para a origem
        gluLookAt(0.0, 0.0, 10.0,  # Posição da câmera
                  0.0, 0.0, 0.0,   # Ponto focal (origem)
                  0.0, 1.0, 0.0)   # Vetor "up" (Y positivo)
    
    # 3. Posiciona a fonte de luz (deve ser após configurar câmera)
    posicao_luz = [luz_x, luz_y, luz_z, 1.0]  # w=1.0 = luz posicional
    glLightfv(GL_LIGHT0, GL_POSITION, posicao_luz)
    
    # 4. Desenha esfera amarela para visualizar posição da luz
    glPushMatrix()
    glTranslatef(luz_x, luz_y, luz_z)
    glDisable(GL_LIGHTING)  # Esfera não é afetada por iluminação
    glColor3f(1.0, 1.0, 0.0)  # Amarelo
    glutSolidSphere(0.2, 10, 10)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    
    # 5. Configura modelo de iluminação (Flat/Gouraud/Phong)
    configurar_iluminacao_renderizacao()
    
    # 6-7. Aplica transformações e desenha o objeto
    glPushMatrix()
    glTranslatef(pos_x, pos_y, pos_z)  # Posição
    glRotatef(rot_x, 1.0, 0.0, 0.0)    # Rotação X
    glRotatef(rot_y, 0.0, 1.0, 0.0)    # Rotação Y
    glScalef(scale, scale, scale)       # Escala uniforme
    
    desenhar_objeto()  # Desenha objeto selecionado
    
    glPopMatrix()

    # 8. Desenha HUD (interface 2D) por cima da cena 3D
    desenhar_hud()

    # 9. Troca buffers (exibe frame renderizado)
    glutSwapBuffers()


# ==========================================
# RESHAPE
# ==========================================
def reshape(w, h):
    global projecao_ortografica
    
    if h == 0: 
        h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    
    aspecto = float(w) / float(h)
    
    if projecao_ortografica:
        if w <= h:
            glOrtho(-10, 10, -10/aspecto, 10/aspecto, 0.1, 100.0)
        else:
            glOrtho(-10*aspecto, 10*aspecto, -10, 10, 0.1, 100.0)
    else:
        gluPerspective(45, aspecto, 0.1, 100.0)
        
    glMatrixMode(GL_MODELVIEW)


# ==========================================
# KEYBOARD
# ==========================================
def keyboard(key, x, y):
    global rot_x, rot_y, scale, projecao_ortografica, modelo_iluminacao
    global luz_x, luz_y, luz_z, modo_wireframe
    global objeto_selecionado, modo_extrusao, extrusao_ativa
    global modo_camera, mouse_capturado
    global camera_x, camera_y, camera_z, camera_yaw, camera_pitch
    global ultimo_mouse_x, ultimo_mouse_y
    global altura_extrusao
    global mostrar_comandos
    
    # Alternar entre modo câmera e modo objeto
    if key == b'0':
        modo_camera = not modo_camera
        mouse_capturado = modo_camera
        if modo_camera:
            print("Modo: CÂMERA (WASD + Mouse)")
            dx = 0.0 - camera_x
            dy = 0.0 - camera_y
            dz = 0.0 - camera_z
            dist_horizontal = math.sqrt(dx * dx + dz * dz)
            camera_yaw = math.degrees(math.atan2(dx, dz))
            camera_pitch = math.degrees(math.atan2(dy, dist_horizontal))
            glutSetCursor(GLUT_CURSOR_NONE)
            ultimo_mouse_x = glutGet(GLUT_WINDOW_WIDTH) // 2
            ultimo_mouse_y = glutGet(GLUT_WINDOW_HEIGHT) // 2
            glutWarpPointer(ultimo_mouse_x, ultimo_mouse_y)
        else:
            print("Modo: OBJETO (WASD move objeto)")
            glutSetCursor(GLUT_CURSOR_INHERIT)
        glutPostRedisplay()
        return
    
    # Seleção de Objetos Padrões
    if key == b'1':
        objeto_selecionado = 1
        modo_extrusao = False
        extrusao_ativa = False
        print("Objeto: Esfera")
    elif key == b'2':
        objeto_selecionado = 2
        modo_extrusao = False
        extrusao_ativa = False
        print("Objeto: Cubo")
    elif key == b'3':
        objeto_selecionado = 3
        modo_extrusao = False
        extrusao_ativa = False
        print("Objeto: Cone")
    elif key == b'4':
        objeto_selecionado = 4
        modo_extrusao = False
        extrusao_ativa = False
        print("Objeto: Torus")
    elif key == b'5':
        objeto_selecionado = 5
        modo_extrusao = False
        extrusao_ativa = False
        print("Objeto: Teapot")
    elif key == b'6':
        modo_extrusao = True
        extrusao_ativa = False
        print("Modo Extrusão ativado - Clique com o mouse para adicionar pontos ao perfil")
        print("Controles: [E] Ativar/Desativar extrusão 3D | [C] Limpar perfil | [H] Aumentar altura | [N] Diminuir altura")
    
    # WASD
    if modo_camera:
        if key in (b'w', b'W'):
            mover_camera_frente()
        elif key in (b's', b'S'):
            mover_camera_tras()
        elif key in (b'a', b'A'):
            mover_camera_esquerda()
        elif key in (b'd', b'D'):
            mover_camera_direita()
    else:
        if key in (b'w', b'W'):
            rot_x -= 5.0
        elif key in (b's', b'S'):
            rot_x += 5.0
        elif key in (b'a', b'A'):
            rot_y -= 5.0
        elif key in (b'd', b'D'):
            rot_y += 5.0
    
    # Escala
    if key == b'+': 
        scale += 0.1
    elif key == b'-': 
        scale = max(0.1, scale - 0.1)
    
    # Luz
    elif key in (b'i', b'I'): luz_y += 0.5
    elif key in (b'k', b'K'): luz_y -= 0.5
    elif key in (b'j', b'J'): luz_x -= 0.5
    elif key in (b'l', b'L'): luz_x += 0.5
    elif key in (b'u', b'U'): luz_z -= 0.5
    elif key in (b'o', b'O'): luz_z += 0.5
    
    # Projeção
    elif key in (b'p', b'P'):
        projecao_ortografica = not projecao_ortografica
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        
    # Iluminação
    elif key in (b'm', b'M'):
        modelo_iluminacao = (modelo_iluminacao + 1) % 3
        nomes = ["Flat", "Gouraud", "Phong"]
        print(f"Modo Iluminacao: {nomes[modelo_iluminacao]}")
    
    # Wireframe
    elif key in (b'f', b'F'):
        modo_wireframe = not modo_wireframe
        print(f"Renderização: {'Wireframe' if modo_wireframe else 'Solid'}")

    # HUD
    elif key in (b't', b'T'):
        mostrar_comandos = not mostrar_comandos

    # Controles do Modo Extrusão
    if modo_extrusao:
        if key in (b'e', b'E'):
            extrusao_ativa = not extrusao_ativa
            if extrusao_ativa:
                print("Extrusão 3D ATIVADA")
            else:
                print("Extrusão 3D DESATIVADA - Modo edição de perfil 2D")
            glutPostRedisplay()
        elif key in (b'c', b'C'):
            limpar_perfil()
            extrusao_ativa = False
            glutPostRedisplay()
        elif key in (b'h', b'H'):
            altura_extrusao += 0.2
            print(f"Altura extrusão: {altura_extrusao:.2f}")
            glutPostRedisplay()
        elif key in (b'n', b'N'):
            altura_extrusao = max(0.1, altura_extrusao - 0.2)
            print(f"Altura extrusão: {altura_extrusao:.2f}")
            glutPostRedisplay()

    glutPostRedisplay()


def mouse_motion(x, y):
    """Função chamada quando o mouse se move no modo câmera"""
    global camera_yaw, camera_pitch, ultimo_mouse_x, ultimo_mouse_y
    global mouse_capturado, sensibilidade_mouse, modo_camera
    
    if not modo_camera or not mouse_capturado:
        return
    
    dx = x - ultimo_mouse_x
    dy = y - ultimo_mouse_y
    
    camera_yaw -= dx * sensibilidade_mouse
    camera_pitch -= dy * sensibilidade_mouse
    
    camera_pitch = max(-89.0, min(89.0, camera_pitch))
    
    centro_x = glutGet(GLUT_WINDOW_WIDTH) // 2
    centro_y = glutGet(GLUT_WINDOW_HEIGHT) // 2
    
    if abs(x - centro_x) > 50 or abs(y - centro_y) > 50:
        glutWarpPointer(centro_x, centro_y)
        ultimo_mouse_x = centro_x
        ultimo_mouse_y = centro_y
    else:
        ultimo_mouse_x = x
        ultimo_mouse_y = y
    
    glutPostRedisplay()


def special_keys(key, x, y):
    global pos_x, pos_y
    if key == GLUT_KEY_UP: pos_y += 0.1
    elif key == GLUT_KEY_DOWN: pos_y -= 0.1
    elif key == GLUT_KEY_LEFT: pos_x -= 0.1
    elif key == GLUT_KEY_RIGHT: pos_x += 0.1
    glutPostRedisplay()


def mouse_click_extrusao(button, state, x, y):
    """
    Manipula cliques do mouse para adicionar pontos ao perfil de extrusão.
    
    Converte coordenadas de clique (pixels) para coordenadas do mundo 3D:
    1. Normaliza x, y de pixels para [-1, 1]
    2. Ajusta pela proporção da tela (aspect ratio)
    3. Escala para o tamanho da cena (baseado em projeção ortográfica/perspectiva)
    4. Adiciona o ponto (x_world, y_world) ao perfil 2D
    
    Apenas no modo extrusão (tecla [6]) e com botão esquerdo do mouse.
    """
    global modo_extrusao, projecao_ortografica
    
    if not modo_extrusao:
        return
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        width = glutGet(GLUT_WINDOW_WIDTH)
        height = glutGet(GLUT_WINDOW_HEIGHT)
        aspecto = float(width) / float(height)
        
        x_norm = (x / width) * 2.0 - 1.0
        y_norm = ((height - y) / height) * 2.0 - 1.0
        
        escala = 5.0
        if projecao_ortografica:
            if width <= height:
                x_world = x_norm * escala
                y_world = y_norm * (escala / aspecto)
            else:
                x_world = x_norm * (escala * aspecto)
                y_world = y_norm * escala
        else:
            x_world = x_norm * escala * aspecto
            y_world = y_norm * escala
        
        adicionar_ponto_perfil(x_world, y_world)
        glutPostRedisplay()


# ==========================================
# MAIN
# ==========================================
def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Trabalho CG 3D - Phong Scanline no Cubo")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutPassiveMotionFunc(mouse_motion)
    glutMouseFunc(mouse_click_extrusao)
    
    print("--- CONTROLES ---")
    print("[0] Alternar entre Modo Câmera e Modo Objeto")
    print("[1-5] Selecionar Objeto Padrão | [6] Modo Extrusão")
    print("[WASD] Girar Objeto (Modo Objeto) | Mover Câmera (Modo Câmera)")
    print("[Mouse] Olhar ao redor (Modo Câmera) | Clique para adicionar pontos (Modo Extrusão)")
    print("[Setas] Mover Objeto")
    print("[IJKL] Mover Luz     | [UO] Luz Z (Fundo/Frente)")
    print("[M] Modo Iluminação (Flat/Gouraud/Phong)")
    print("[P] Projeção         | [F] Wireframe/Solid")
    print("[T] Mostrar/Ocultar comandos na tela")
    print("--- MODO EXTRUSÃO ---")
    print("[Clique Esquerdo] Adicionar ponto ao perfil")
    print("[E] Ativar/Desativar extrusão 3D (ver perfil 2D ou objeto 3D)")
    print("[C] Limpar perfil | [H] Aumentar altura | [N] Diminuir altura")
    
    glutMainLoop()


if __name__ == "__main__":
    main()
