import sys
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math

# ==========================================
# Variáveis Globais
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
camera_yaw = 0.0
camera_pitch = 0.0
velocidade_camera = 0.1
sensibilidade_mouse = 0.1
ultimo_mouse_x = 0
ultimo_mouse_y = 0
mouse_capturado = False

# Estado da Iluminação
# 0: Flat, 1: Gouraud (Suave), 2: Phong (Scanline por triângulo)
modelo_iluminacao = 0

# Estado de Renderização
modo_wireframe = False

# Estado do Objeto Selecionado
# 1=Esfera, 2=Cubo, 3=Cone, 4=Torus, 5=Teapot, 6=Modo Extrusão
objeto_selecionado = 1
modo_extrusao = False

# Estado do Modo Extrusão
perfil_extrusao = []
altura_extrusao = 2.0
num_segmentos_extrusao = 20
extrusao_ativa = False

# Mostrar comandos na tela
mostrar_comandos = True


# ============================================================
#   PROJEÇÃO 3D → 2D
# ============================================================
def project_to_screen(x, y, z):
    """Projeção ponto 3D -> coordenadas de tela (x,y)"""
    model = glGetDoublev(GL_MODELVIEW_MATRIX)
    proj = glGetDoublev(GL_PROJECTION_MATRIX)
    viewport = glGetIntegerv(GL_VIEWPORT)

    winX, winY, winZ = gluProject(x, y, z, model, proj, viewport)
    winY = viewport[3] - winY  # ajustar eixo Y
    return winX, winY, winZ


# ============================================================
#   ILUMINAÇÃO PHONG POR PIXEL (software)
# ============================================================
def phong_shading_point(position, normal, base_color):
    """Calcula iluminação Phong por pixel usando normal interpolada."""
    global luz_x, luz_y, luz_z, modo_camera
    global camera_x, camera_y, camera_z

    # Luz (L)
    L = [luz_x - position[0], luz_y - position[1], luz_z - position[2]]
    L_len = math.sqrt(L[0]**2 + L[1]**2 + L[2]**2)
    if L_len != 0:
        L = [L[0]/L_len, L[1]/L_len, L[2]/L_len]

    # Normal (N)
    N = list(normal)
    N_len = math.sqrt(N[0]**2 + N[1]**2 + N[2]**2)
    if N_len != 0:
        N = [N[0]/N_len, N[1]/N_len, N[2]/N_len]
    else:
        N = [0.0, 0.0, 1.0]

    # Posição da câmera
    if modo_camera:
        eye = [camera_x, camera_y, camera_z]
    else:
        eye = [0.0, 0.0, 10.0]

    # Coeficientes Phong
    ka = 0.2
    kd = 0.7
    ks = 0.8
    shininess = 32

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
        V = [eye[0]-position[0], eye[1]-position[1], eye[2]-position[2]]
        V_len = math.sqrt(V[0]**2 + V[1]**2 + V[2]**2)
        if V_len != 0:
            V = [V[0]/V_len, V[1]/V_len, V[2]/V_len]
        RdotV = max(0.0, R[0]*V[0] + R[1]*V[1] + R[2]*V[2])
        I += ks * (RdotV ** shininess)

    I = min(1.0, max(0.0, I))

    r = I * base_color[0]
    g = I * base_color[1]
    b = I * base_color[2]
    return (r, g, b)


# ============================================================
#   SCANLINE + PHONG PARA TRIÂNGULO
# ============================================================
def scanline_phong_triangle(p1, n1, p2, n2, p3, n3, base_color):
    """
    Triângulo em coordenadas 3D, com normais por vértice.
    1) Projeta para 2D
    2) Faz varredura em y (scanline) do triângulo
    3) Interpola posição 3D + normal
    4) Calcula iluminação Phong por pixel
    """
    # Projeção
    s1 = project_to_screen(*p1)
    s2 = project_to_screen(*p2)
    s3 = project_to_screen(*p3)

    # Ordena por y de tela
    verts = sorted([(s1, p1, n1), (s2, p2, n2), (s3, p3, n3)],
                   key=lambda v: v[0][1])

    (x1_s, y1_s, _), P1, N1 = verts[0]
    (x2_s, y2_s, _), P2, N2 = verts[1]
    (x3_s, y3_s, _), P3, N3 = verts[2]

    y_min = int(math.floor(y1_s))
    y_max = int(math.ceil(y3_s))

    # Função que verifica se scanline cruza aresta e retorna interseção
    def edge_intersection(sA, PA, NA, sB, PB, NB, y):
        xA, yA, _ = sA
        xB, yB, _ = sB
        if yA == yB:
            return None
        # Verifica se y está entre yA e yB (intervalo semi-aberto)
        if (y < min(yA, yB)) or (y >= max(yA, yB)):
            return None
        t = (y - yA) / (yB - yA)
        x = xA + t * (xB - xA)
        P = [PA[i] + t*(PB[i]-PA[i]) for i in range(3)]
        N = [NA[i] + t*(NB[i]-NA[i]) for i in range(3)]
        return x, P, N

    # Durante Phong via software, desativamos o lighting do OpenGL
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
        for x in range(x_start, x_end+1):
            t = (x - xL) / (xR - xL + 1e-9)

            P = [PL[i] + t*(PR[i]-PL[i]) for i in range(3)]
            N = [NL[i] + t*(NR[i]-NL[i]) for i in range(3)]

            # Normalizar N
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
# Inicialização OpenGL + Funções do Trabalho
# ==========================================
def init():
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)

    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    luz_ambiente = [0.2, 0.2, 0.2, 1.0]
    luz_difusa   = [0.7, 0.7, 0.7, 1.0]
    luz_especular= [1.0, 1.0, 1.0, 1.0]

    glLightfv(GL_LIGHT0, GL_AMBIENT, luz_ambiente)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, luz_difusa)
    glLightfv(GL_LIGHT0, GL_SPECULAR, luz_especular)

    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)


def configurar_iluminacao_renderizacao():
    global modelo_iluminacao

    if modelo_iluminacao == 0:  # Flat
        glShadeModel(GL_FLAT)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])
        glMaterialf(GL_FRONT, GL_SHININESS, 0)
    elif modelo_iluminacao == 1:  # Gouraud
        glShadeModel(GL_SMOOTH)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])
        glMaterialf(GL_FRONT, GL_SHININESS, 0)
    elif modelo_iluminacao == 2:  # Phong (software)
        glShadeModel(GL_SMOOTH)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1, 1, 1, 1])
        glMaterialf(GL_FRONT, GL_SHININESS, 60.0)


def calcular_normal_face(p1, p2, p3):
    v1 = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]
    v2 = [p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]]

    nx = v1[1]*v2[2] - v1[2]*v2[1]
    ny = v1[2]*v2[0] - v1[0]*v2[2]
    nz = v1[0]*v2[1] - v1[1]*v2[0]

    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length > 0:
        return [nx/length, ny/length, nz/length]
    return [0, 0, 1]


def desenhar_perfil_2d():
    global perfil_extrusao

    if len(perfil_extrusao) < 2:
        return

    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 0.0)
    glLineWidth(2.0)

    glBegin(GL_LINE_STRIP)
    for ponto in perfil_extrusao:
        glVertex3f(ponto[0], ponto[1], 0.0)
    glEnd()

    for ponto in perfil_extrusao:
        glPushMatrix()
        glTranslatef(ponto[0], ponto[1], 0.0)
        glutSolidSphere(0.05, 8, 8)
        glPopMatrix()

    glEnable(GL_LIGHTING)
    glLineWidth(1.0)


def desenhar_extrusao():
    global perfil_extrusao, altura_extrusao, num_segmentos_extrusao
    global modo_wireframe, extrusao_ativa, modelo_iluminacao

    base_color = (0.0, 0.8, 0.3)

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
    num_segmentos = num_segmentos_extrusao

    if modo_wireframe:
        glDisable(GL_LIGHTING)
        glColor3f(*base_color)

        for i in range(num_segmentos + 1):
            z = (i / num_segmentos) * altura_extrusao
            glBegin(GL_LINE_LOOP)
            for ponto in perfil:
                glVertex3f(ponto[0], ponto[1], z)
            glEnd()

        for ponto in perfil:
            glBegin(GL_LINE_STRIP)
            for i in range(num_segmentos + 1):
                z = (i / num_segmentos) * altura_extrusao
                glVertex3f(ponto[0], ponto[1], z)
            glEnd()
        glEnable(GL_LIGHTING)
        return

    # --------- MODO SÓLIDO ----------
    glColor3f(*base_color)

    if modelo_iluminacao != 2:
        # ====== Flat / Gouraud: usa OpenGL normal ======
        glBegin(GL_TRIANGLES)
        # Faces laterais
        for i in range(num_segmentos):
            z1 = (i / num_segmentos) * altura_extrusao
            z2 = ((i + 1) / num_segmentos) * altura_extrusao

            for j in range(num_pontos - 1):
                p1 = [perfil[j][0],     perfil[j][1],     z1]
                p2 = [perfil[j+1][0],   perfil[j+1][1],   z1]
                p3 = [perfil[j][0],     perfil[j][1],     z2]
                p4 = [perfil[j+1][0],   perfil[j+1][1],   z2]

                n1 = calcular_normal_face(p1, p2, p3)
                n2 = calcular_normal_face(p2, p4, p3)

                if modelo_iluminacao == 0:  # Flat
                    glNormal3f(*n1)
                    glVertex3f(*p1); glVertex3f(*p2); glVertex3f(*p3)
                    glNormal3f(*n2)
                    glVertex3f(*p2); glVertex3f(*p4); glVertex3f(*p3)
                else:  # Gouraud (mas com mesma normal por vértice)
                    glNormal3f(*n1)
                    glVertex3f(*p1)
                    glNormal3f(*n1)
                    glVertex3f(*p2)
                    glNormal3f(*n1)
                    glVertex3f(*p3)

                    glNormal3f(*n2)
                    glVertex3f(*p2)
                    glNormal3f(*n2)
                    glVertex3f(*p4)
                    glNormal3f(*n2)
                    glVertex3f(*p3)

        # Base inferior
        if num_pontos > 2:
            z_base = 0.0
            for j in range(1, num_pontos - 1):
                p1 = [perfil[0][0],   perfil[0][1],   z_base]
                p2 = [perfil[j][0],   perfil[j][1],   z_base]
                p3 = [perfil[j+1][0], perfil[j+1][1], z_base]
                normal = calcular_normal_face(p1, p3, p2)
                glNormal3f(*normal)
                glVertex3f(*p1); glVertex3f(*p2); glVertex3f(*p3)

        # Topo
        if num_pontos > 2:
            z_topo = altura_extrusao
            for j in range(1, num_pontos - 1):
                p1 = [perfil[0][0],   perfil[0][1],   z_topo]
                p2 = [perfil[j][0],   perfil[j][1],   z_topo]
                p3 = [perfil[j+1][0], perfil[j+1][1], z_topo]
                normal = calcular_normal_face(p1, p2, p3)
                glNormal3f(*normal)
                glVertex3f(*p1); glVertex3f(*p2); glVertex3f(*p3)

        glEnd()
        return

    # ====== MODO PHONG (2): SCANLINE POR TRIÂNGULO ======
    # Faces laterais
    for i in range(num_segmentos):
        z1 = (i / num_segmentos) * altura_extrusao
        z2 = ((i + 1) / num_segmentos) * altura_extrusao

        for j in range(num_pontos - 1):
            p1 = [perfil[j][0],     perfil[j][1],     z1]
            p2 = [perfil[j+1][0],   perfil[j+1][1],   z1]
            p3 = [perfil[j][0],     perfil[j][1],     z2]
            p4 = [perfil[j+1][0],   perfil[j+1][1],   z2]

            n1 = calcular_normal_face(p1, p2, p3)
            n2 = calcular_normal_face(p2, p4, p3)

            # Triângulo 1: p1,p2,p3
            scanline_phong_triangle(p1, n1, p2, n1, p3, n1, base_color)
            # Triângulo 2: p2,p4,p3
            scanline_phong_triangle(p2, n2, p4, n2, p3, n2, base_color)

    # Base inferior
    if num_pontos > 2:
        z_base = 0.0
        for j in range(1, num_pontos - 1):
            p1 = [perfil[0][0],   perfil[0][1],   z_base]
            p2 = [perfil[j][0],   perfil[j][1],   z_base]
            p3 = [perfil[j+1][0], perfil[j+1][1], z_base]
            n = calcular_normal_face(p1, p3, p2)
            scanline_phong_triangle(p1, n, p2, n, p3, n, base_color)

    # Topo
    if num_pontos > 2:
        z_topo = altura_extrusao
        for j in range(1, num_pontos - 1):
            p1 = [perfil[0][0],   perfil[0][1],   z_topo]
            p2 = [perfil[j][0],   perfil[j][1],   z_topo]
            p3 = [perfil[j+1][0], perfil[j+1][1], z_topo]
            n = calcular_normal_face(p1, p2, p3)
            scanline_phong_triangle(p1, n, p2, n, p3, n, base_color)


def adicionar_ponto_perfil(x, y):
    global perfil_extrusao
    perfil_extrusao.append((x, y))
    print(f"Ponto adicionado: ({x:.2f}, {y:.2f}). Total: {len(perfil_extrusao)} pontos")


def limpar_perfil():
    global perfil_extrusao
    perfil_extrusao = []
    print("Perfil limpo")


def desenhar_cubo_phong():
    glBegin(GL_QUADS)
    glNormal3f(0.0, 0.0, 1.0)
    glVertex3f(-1.0, -1.0,  1.0)
    glVertex3f( 1.0, -1.0,  1.0)
    glVertex3f( 1.0,  1.0,  1.0)
    glVertex3f(-1.0,  1.0,  1.0)

    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f( 1.0, -1.0, -1.0)
    glVertex3f(-1.0, -1.0, -1.0)
    glVertex3f(-1.0,  1.0, -1.0)
    glVertex3f( 1.0,  1.0, -1.0)

    glNormal3f(1.0, 0.0, 0.0)
    glVertex3f( 1.0, -1.0,  1.0)
    glVertex3f( 1.0, -1.0, -1.0)
    glVertex3f( 1.0,  1.0, -1.0)
    glVertex3f( 1.0,  1.0,  1.0)

    glNormal3f(-1.0, 0.0, 0.0)
    glVertex3f(-1.0, -1.0, -1.0)
    glVertex3f(-1.0, -1.0,  1.0)
    glVertex3f(-1.0,  1.0,  1.0)
    glVertex3f(-1.0,  1.0, -1.0)

    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(-1.0,  1.0,  1.0)
    glVertex3f( 1.0,  1.0,  1.0)
    glVertex3f( 1.0,  1.0, -1.0)
    glVertex3f(-1.0,  1.0, -1.0)

    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-1.0, -1.0, -1.0)
    glVertex3f( 1.0, -1.0, -1.0)
    glVertex3f( 1.0, -1.0,  1.0)
    glVertex3f(-1.0, -1.0,  1.0)
    glEnd()


def desenhar_objeto():
    global objeto_selecionado, modo_wireframe, modo_extrusao, modelo_iluminacao

    if modo_extrusao:
        desenhar_extrusao()
        return

    glColor3f(0.0, 0.5, 1.0)

    if objeto_selecionado == 1:
        if modo_wireframe:
            glutWireSphere(1.0, 10, 10)
        else:
            glutSolidSphere(1.0, 20, 20)

    elif objeto_selecionado == 2:
        if modo_wireframe:
            glutWireCube(2.0)
        else:
            if modelo_iluminacao == 2:
                desenhar_cubo_phong()
            else:
                glutSolidCube(2.0)

    elif objeto_selecionado == 3:
        if modo_wireframe:
            glutWireCone(1.0, 2.0, 15, 15)
        else:
            glutSolidCone(1.0, 2.0, 15, 15)

    elif objeto_selecionado == 4:
        if modo_wireframe:
            glutWireTorus(0.5, 1.0, 15, 15)
        else:
            glutSolidTorus(0.5, 1.0, 15, 15)

    elif objeto_selecionado == 5:
        if modo_wireframe:
            glutWireTeapot(1.0)
        else:
            glutSolidTeapot(1.0)


def atualizar_camera():
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
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    yaw_rad = math.radians(camera_yaw)
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera


def mover_camera_tras():
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    yaw_rad = math.radians(camera_yaw)
    camera_x -= math.sin(yaw_rad) * velocidade_camera
    camera_z -= math.cos(yaw_rad) * velocidade_camera


def mover_camera_esquerda():
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    yaw_rad = math.radians(camera_yaw + 90)
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera


def mover_camera_direita():
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    yaw_rad = math.radians(camera_yaw - 90)
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera


def desenhar_texto_2d(x, y, texto):
    glRasterPos2f(x, y)
    for ch in texto:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))


def desenhar_hud():
    global mostrar_comandos, modo_camera, modelo_iluminacao
    global modo_wireframe, projecao_ortografica, modo_extrusao
    global extrusao_ativa, objeto_selecionado

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
    modos_ilum = ["Flat", "Gouraud", "Phong (Scanline)"]
    ilum_str = modos_ilum[modelo_iluminacao]
    wire_str = "Wireframe" if modo_wireframe else "Solido"
    proj_str = "Ortografica" if projecao_ortografica else "Perspectiva"
    extru_str = "OFF"
    if modo_extrusao:
        extru_str = "Perfil 2D" if not extrusao_ativa else "Extrusao 3D"

    obj_nomes = {1: "Esfera", 2: "Cubo", 3: "Cone", 4: "Torus", 5: "Teapot"}
    obj_str = obj_nomes.get(objeto_selecionado, "-")
    if modo_extrusao:
        obj_str = "Extrusao"

    linhas = [
        f"Modo: {modo_str}   |   Objeto: {obj_str}",
        f"Iluminacao [M]: {ilum_str}   |   Renderizacao [F]: {wire_str}   |   Projecao [P]: {proj_str}",
        f"[0] Camera/Objeto  |  [1-5] Objetos  |  [6] Modo Extrusao ({extru_str})",
        "[WASD] (Obj: rotacao / Cam: movimento)  |  Setas: mover objeto",
        "[IJKL/UO] mover luz   |   [T] mostrar/ocultar ajuda",
        "[Extrusao] Clique: adiciona ponto  |  [E] ativa extrusao  |  [C] limpa  |  [H/N] altura",
        "Modo 2 (Phong): extrusao renderizada por scanline + iluminacao Phong por pixel"
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


def display():
    global modo_camera, luz_x, luz_y, luz_z
    global pos_x, pos_y, pos_z, rot_x, rot_y, scale

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    if modo_camera:
        atualizar_camera()
    else:
        gluLookAt(0.0, 0.0, 10.0,  0.0, 0.0, 0.0,  0.0, 1.0, 0.0)

    posicao_luz = [luz_x, luz_y, luz_z, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, posicao_luz)

    glPushMatrix()
    glTranslatef(luz_x, luz_y, luz_z)
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 0.0)
    glutSolidSphere(0.2, 10, 10)
    glEnable(GL_LIGHTING)
    glPopMatrix()

    configurar_iluminacao_renderizacao()

    glPushMatrix()
    glTranslatef(pos_x, pos_y, pos_z)
    glRotatef(rot_x, 1.0, 0.0, 0.0)
    glRotatef(rot_y, 0.0, 1.0, 0.0)
    glScalef(scale, scale, scale)

    desenhar_objeto()
    glPopMatrix()

    desenhar_hud()

    glutSwapBuffers()


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


def keyboard(key, x, y):
    global rot_x, rot_y, scale, projecao_ortografica, modelo_iluminacao
    global luz_x, luz_y, luz_z, modo_wireframe
    global objeto_selecionado, modo_extrusao, extrusao_ativa
    global modo_camera, mouse_capturado
    global camera_x, camera_y, camera_z, camera_yaw, camera_pitch
    global ultimo_mouse_x, ultimo_mouse_y
    global altura_extrusao
    global mostrar_comandos

    if key == b'0':
        modo_camera = not modo_camera
        mouse_capturado = modo_camera
        if modo_camera:
            print("Modo: CÂMERA")
            dx = 0.0 - camera_x
            dy = 0.0 - camera_y
            dz = 0.0 - camera_z
            dist_horizontal = math.sqrt(dx*dx + dz*dz)
            camera_yaw = math.degrees(math.atan2(dx, dz))
            camera_pitch = math.degrees(math.atan2(dy, dist_horizontal))
            glutSetCursor(GLUT_CURSOR_NONE)
            ultimo_mouse_x = glutGet(GLUT_WINDOW_WIDTH)//2
            ultimo_mouse_y = glutGet(GLUT_WINDOW_HEIGHT)//2
            glutWarpPointer(ultimo_mouse_x, ultimo_mouse_y)
        else:
            print("Modo: OBJETO")
            glutSetCursor(GLUT_CURSOR_INHERIT)
        glutPostRedisplay()
        return

    if key == b'1':
        objeto_selecionado = 1; modo_extrusao = False; extrusao_ativa = False
    elif key == b'2':
        objeto_selecionado = 2; modo_extrusao = False; extrusao_ativa = False
    elif key == b'3':
        objeto_selecionado = 3; modo_extrusao = False; extrusao_ativa = False
    elif key == b'4':
        objeto_selecionado = 4; modo_extrusao = False; extrusao_ativa = False
    elif key == b'5':
        objeto_selecionado = 5; modo_extrusao = False; extrusao_ativa = False
    elif key == b'6':
        modo_extrusao = True
        extrusao_ativa = False
        print("Modo Extrusão ativado - clique para adicionar pontos ao perfil")

    if modo_camera:
        if key in (b'w', b'W'): mover_camera_frente()
        elif key in (b's', b'S'): mover_camera_tras()
        elif key in (b'a', b'A'): mover_camera_esquerda()
        elif key in (b'd', b'D'): mover_camera_direita()
    else:
        if key in (b'w', b'W'): rot_x -= 5.0
        elif key in (b's', b'S'): rot_x += 5.0
        elif key in (b'a', b'A'): rot_y -= 5.0
        elif key in (b'd', b'D'): rot_y += 5.0

    if key == b'+':
        scale += 0.1
    elif key == b'-':
        scale = max(0.1, scale - 0.1)

    elif key in (b'i', b'I'): luz_y += 0.5
    elif key in (b'k', b'K'): luz_y -= 0.5
    elif key in (b'j', b'J'): luz_x -= 0.5
    elif key in (b'l', b'L'): luz_x += 0.5
    elif key in (b'u', b'U'): luz_z -= 0.5
    elif key in (b'o', b'O'): luz_z += 0.5

    elif key in (b'p', b'P'):
        projecao_ortografica = not projecao_ortografica
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))

    elif key in (b'm', b'M'):
        modelo_iluminacao = (modelo_iluminacao + 1) % 3
        nomes = ["Flat", "Gouraud", "Phong (Scanline)"]
        print(f"Modo Iluminacao: {nomes[modelo_iluminacao]}")

    elif key in (b'f', b'F'):
        modo_wireframe = not modo_wireframe

    elif key in (b't', b'T'):
        mostrar_comandos = not mostrar_comandos

    if modo_extrusao:
        if key in (b'e', b'E'):
            extrusao_ativa = not extrusao_ativa
            print("Extrusão 3D ATIVADA" if extrusao_ativa else "Extrusão 3D DESATIVADA")
        elif key in (b'c', b'C'):
            limpar_perfil()
            extrusao_ativa = False
        elif key in (b'h', b'H'):
            altura_extrusao += 0.2
            print(f"Altura extrusão: {altura_extrusao:.2f}")
        elif key in (b'n', b'N'):
            altura_extrusao = max(0.1, altura_extrusao - 0.2)
            print(f"Altura extrusão: {altura_extrusao:.2f}")

    glutPostRedisplay()


def mouse_motion(x, y):
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


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Trabalho CG 3D - Scanline Phong")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutPassiveMotionFunc(mouse_motion)
    glutMouseFunc(mouse_click_extrusao)

    print("--- CONTROLES ---")
    print("[0] Camera/Objeto")
    print("[1-5] Objetos | [6] Modo Extrusao")
    print("Modo 2 (M) = Phong: extrusao via scanline + Phong por pixel")
    print("[WASD] Rotacao (objeto) ou movimento (camera)")
    print("[IJKL/UO] mover luz | [P] projecao | [F] Wireframe")
    print("[T] HUD | [H/N] altura extrusao | [E] ativa extrusao 3D")

    glutMainLoop()


if __name__ == "__main__":
    main()
