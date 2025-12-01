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
camera_yaw = 0.0    # Rotação horizontal (esquerda/direita)
camera_pitch = 0.0  # Rotação vertical (cima/baixo)
velocidade_camera = 0.1
sensibilidade_mouse = 0.1
ultimo_mouse_x = 0
ultimo_mouse_y = 0
mouse_capturado = False

# Estado da Iluminação
# 0: Flat, 1: Gouraud (Suave), 2: Phong (Suave + Brilho)
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

# === NOVO: Mostrar comandos na tela ===
mostrar_comandos = True


def init():
    """Configurações iniciais do OpenGL"""
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)

    # Importante para iluminação correta quando usamos escala
    # (normais são renormalizadas automaticamente)
    # === NOVO ===
    glEnable(GL_NORMALIZE)
    
    # ==========================================
    # CONFIGURAÇÃO DE LUZ
    # ==========================================
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    
    # Cores da Luz
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
    """Aplica o modelo de iluminação escolhido"""
    global modelo_iluminacao
    
    if modelo_iluminacao == 0: 
        # --- FLAT SHADING ---
        glShadeModel(GL_FLAT)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])
        glMaterialf(GL_FRONT, GL_SHININESS, 0)
        
    elif modelo_iluminacao == 1:
        # --- GOURAUD ---
        glShadeModel(GL_SMOOTH)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [0, 0, 0, 1])
        glMaterialf(GL_FRONT, GL_SHININESS, 0)
        
    elif modelo_iluminacao == 2:
        # --- PHONG (Simulado: suave + especular forte) ---
        glShadeModel(GL_SMOOTH)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1, 1, 1, 1])
        glMaterialf(GL_FRONT, GL_SHININESS, 60.0)


def calcular_normal_face(p1, p2, p3):
    """Calcula a normal de uma face triangular"""
    v1 = [p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2]]
    v2 = [p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2]]
    
    # Produto vetorial
    nx = v1[1] * v2[2] - v1[2] * v2[1]
    ny = v1[2] * v2[0] - v1[0] * v2[2]
    nz = v1[0] * v2[1] - v1[1] * v2[0]
    
    # Normalizar
    length = math.sqrt(nx*nx + ny*ny + nz*nz)
    if length > 0:
        return [nx/length, ny/length, nz/length]
    return [0, 0, 1]


def desenhar_perfil_2d():
    """Desenha o perfil 2D como linhas no plano XY"""
    global perfil_extrusao
    
    if len(perfil_extrusao) < 2:
        return
    
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 0.0)  # Amarelo para o perfil 2D
    glLineWidth(2.0)
    
    # Desenha as linhas conectando os pontos
    glBegin(GL_LINE_STRIP)
    for ponto in perfil_extrusao:
        glVertex3f(ponto[0], ponto[1], 0.0)
    glEnd()
    
    # Desenha pontos como pequenas esferas
    for ponto in perfil_extrusao:
        glPushMatrix()
        glTranslatef(ponto[0], ponto[1], 0.0)
        glutSolidSphere(0.05, 8, 8)
        glPopMatrix()
    
    glEnable(GL_LIGHTING)
    glLineWidth(1.0)


def desenhar_extrusao():
    """Desenha o objeto extrudado a partir do perfil"""
    global perfil_extrusao, altura_extrusao, num_segmentos_extrusao, modo_wireframe, extrusao_ativa, modelo_iluminacao
    
    # Se a extrusão não está ativa, mostra apenas o perfil 2D
    if not extrusao_ativa:
        desenhar_perfil_2d()
        return
    
    if len(perfil_extrusao) < 3:
        # Se não há pontos suficientes, mostra apenas o perfil 2D
        desenhar_perfil_2d()
        return
    
    glColor3f(0.0, 0.8, 0.3)  # Verde para o objeto extrudado
    
    # Fechar o perfil se não estiver fechado
    perfil = perfil_extrusao.copy()
    if perfil[0] != perfil[-1]:
        perfil.append(perfil[0])
    
    num_pontos = len(perfil)
    num_segmentos = num_segmentos_extrusao
    
    if modo_wireframe:
        glDisable(GL_LIGHTING)
        # Desenha apenas as arestas
        for i in range(num_segmentos + 1):
            z = (i / num_segmentos) * altura_extrusao
            glBegin(GL_LINE_LOOP)
            for ponto in perfil:
                glVertex3f(ponto[0], ponto[1], z)
            glEnd()
        
        # Desenha linhas verticais conectando os pontos
        for ponto in perfil:
            glBegin(GL_LINE_STRIP)
            for i in range(num_segmentos + 1):
                z = (i / num_segmentos) * altura_extrusao
                glVertex3f(ponto[0], ponto[1], z)
            glEnd()
        glEnable(GL_LIGHTING)
    else:
        # Desenha faces sólidas
        glBegin(GL_TRIANGLES)
        
        # Faces laterais (ao longo da extrusão)
        for i in range(num_segmentos):
            z1 = (i / num_segmentos) * altura_extrusao
            z2 = ((i + 1) / num_segmentos) * altura_extrusao
            
            for j in range(num_pontos - 1):
                # Dois triângulos por face lateral
                p1 = [perfil[j][0], perfil[j][1], z1]
                p2 = [perfil[j+1][0], perfil[j+1][1], z1]
                p3 = [perfil[j][0], perfil[j][1], z2]
                p4 = [perfil[j+1][0], perfil[j+1][1], z2]
                
                # Calcula normais para melhor iluminação
                # Normal do triângulo 1
                n1 = calcular_normal_face(p1, p2, p3)
                # Normal do triângulo 2
                n2 = calcular_normal_face(p2, p4, p3)
                
                # Para Gouraud/Phong, usa normais por vértice
                # Para Flat, usa normal da face
                if modelo_iluminacao == 0:  # Flat
                    # Triângulo 1
                    glNormal3f(n1[0], n1[1], n1[2])
                    glVertex3f(p1[0], p1[1], p1[2])
                    glVertex3f(p2[0], p2[1], p2[2])
                    glVertex3f(p3[0], p3[1], p3[2])
                    
                    # Triângulo 2
                    glNormal3f(n2[0], n2[1], n2[2])
                    glVertex3f(p2[0], p2[1], p2[2])
                    glVertex3f(p4[0], p4[1], p4[2])
                    glVertex3f(p3[0], p3[1], p3[2])
                else:  # Gouraud ou Phong - normais por vértice
                    # Triângulo 1 - cada vértice com sua normal
                    glNormal3f(n1[0], n1[1], n1[2])
                    glVertex3f(p1[0], p1[1], p1[2])
                    glNormal3f(n1[0], n1[1], n1[2])
                    glVertex3f(p2[0], p2[1], p2[2])
                    glNormal3f(n1[0], n1[1], n1[2])
                    glVertex3f(p3[0], p3[1], p3[2])
                    
                    # Triângulo 2
                    glNormal3f(n2[0], n2[1], n2[2])
                    glVertex3f(p2[0], p2[1], p2[2])
                    glNormal3f(n2[0], n2[1], n2[2])
                    glVertex3f(p4[0], p4[1], p4[2])
                    glNormal3f(n2[0], n2[1], n2[2])
                    glVertex3f(p3[0], p3[1], p3[2])
        
        # Face inferior (base)
        if num_pontos > 2:
            z_base = 0.0
            for j in range(1, num_pontos - 1):
                p1 = [perfil[0][0], perfil[0][1], z_base]
                p2 = [perfil[j][0], perfil[j][1], z_base]
                p3 = [perfil[j+1][0], perfil[j+1][1], z_base]
                
                normal = calcular_normal_face(p1, p3, p2)  # Invertido para normal apontar para baixo
                glNormal3f(normal[0], normal[1], normal[2])
                glVertex3f(p1[0], p1[1], p1[2])
                glVertex3f(p2[0], p2[1], p2[2])
                glVertex3f(p3[0], p3[1], p3[2])
        
        # Face superior (topo)
        if num_pontos > 2:
            z_topo = altura_extrusao
            for j in range(1, num_pontos - 1):
                p1 = [perfil[0][0], perfil[0][1], z_topo]
                p2 = [perfil[j][0], perfil[j][1], z_topo]
                p3 = [perfil[j+1][0], perfil[j+1][1], z_topo]
                
                normal = calcular_normal_face(p1, p2, p3)
                glNormal3f(normal[0], normal[1], normal[2])
                glVertex3f(p1[0], p1[1], p1[2])
                glVertex3f(p2[0], p2[1], p2[2])
                glVertex3f(p3[0], p3[1], p3[2])
        
        glEnd()


def adicionar_ponto_perfil(x, y):
    """Adiciona um ponto ao perfil de extrusão"""
    global perfil_extrusao
    # Adiciona as coordenadas diretamente
    perfil_extrusao.append((x, y))
    print(f"Ponto adicionado: ({x:.2f}, {y:.2f}). Total: {len(perfil_extrusao)} pontos")


def limpar_perfil():
    """Limpa o perfil de extrusão"""
    global perfil_extrusao
    perfil_extrusao = []
    print("Perfil limpo")


def ler_coordenadas_terminal():
    """Lê coordenadas X e Y do terminal com validação"""
    global perfil_extrusao
    
    # Limites recomendados baseados na escala da cena
    MIN_COORD = -5.0
    MAX_COORD = 5.0
    
    print("\n" + "="*50)
    print("   ADICIONAR PONTO AO PERFIL DE EXTRUSAO")
    print("="*50)
    print(f"Digite coordenadas entre {MIN_COORD} e {MAX_COORD}")
    print("(Valores fora do range serao ajustados automaticamente)")
    print("")
    
    try:
        # Lê coordenada X
        x_str = input(f"Coordenada X [{MIN_COORD} a {MAX_COORD}]: ")
        x = float(x_str)
        
        # Lê coordenada Y
        y_str = input(f"Coordenada Y [{MIN_COORD} a {MAX_COORD}]: ")
        y = float(y_str)
        
        # Aplica clamping (validação com limites)
        x_clamped = max(MIN_COORD, min(MAX_COORD, x))
        y_clamped = max(MIN_COORD, min(MAX_COORD, y))
        
        # Avisa se houve ajuste
        if x != x_clamped or y != y_clamped:
            print(f"\n>> Valores ajustados para ficarem dentro do range:")
            print(f"   Original: ({x:.2f}, {y:.2f})")
            print(f"   Ajustado: ({x_clamped:.2f}, {y_clamped:.2f})")
        
        # Adiciona o ponto ao perfil
        adicionar_ponto_perfil(x_clamped, y_clamped)
        print("="*50)
        glutPostRedisplay()
        
    except ValueError:
        print("\n>> ERRO: Digite numeros validos!")
        print("   Exemplo: 2.5 ou -3.0")
        print("="*50)
    except EOFError:
        print("\n>> Entrada cancelada")
        print("="*50)
    except KeyboardInterrupt:
        print("\n>> Entrada cancelada")
        print("="*50)


def listar_coordenadas_terminal():
    """Lista todas as coordenadas do perfil no terminal"""
    global perfil_extrusao
    
    print("\n" + "="*50)
    print("   PONTOS DO PERFIL DE EXTRUSAO")
    print("="*50)
    
    if len(perfil_extrusao) == 0:
        print("  Nenhum ponto adicionado ainda.")
        print("  Use a tecla [X] para adicionar pontos.")
    else:
        print(f"  Total de pontos: {len(perfil_extrusao)}")
        print("")
        print("  #  |    X    |    Y    ")
        print("  ---+----------+---------")
        for i, (x, y) in enumerate(perfil_extrusao, 1):
            print(f"  {i:2d} | {x:7.2f} | {y:7.2f}")
    
    print("="*50)

# === NOVO: cubo com normais explícitas para Phong (modo 2) ===
def desenhar_cubo_phong():
    # Cubo de lado 2, centrado na origem, vértices em +/-1
    glBegin(GL_QUADS)
    
    # Frente (z = 1)
    glNormal3f(0.0, 0.0, 1.0)
    glVertex3f(-1.0, -1.0,  1.0)
    glVertex3f( 1.0, -1.0,  1.0)
    glVertex3f( 1.0,  1.0,  1.0)
    glVertex3f(-1.0,  1.0,  1.0)
    
    # Trás (z = -1)
    glNormal3f(0.0, 0.0, -1.0)
    glVertex3f( 1.0, -1.0, -1.0)
    glVertex3f(-1.0, -1.0, -1.0)
    glVertex3f(-1.0,  1.0, -1.0)
    glVertex3f( 1.0,  1.0, -1.0)
    
    # Direita (x = 1)
    glNormal3f(1.0, 0.0, 0.0)
    glVertex3f( 1.0, -1.0,  1.0)
    glVertex3f( 1.0, -1.0, -1.0)
    glVertex3f( 1.0,  1.0, -1.0)
    glVertex3f( 1.0,  1.0,  1.0)
    
    # Esquerda (x = -1)
    glNormal3f(-1.0, 0.0, 0.0)
    glVertex3f(-1.0, -1.0, -1.0)
    glVertex3f(-1.0, -1.0,  1.0)
    glVertex3f(-1.0,  1.0,  1.0)
    glVertex3f(-1.0,  1.0, -1.0)
    
    # Topo (y = 1)
    glNormal3f(0.0, 1.0, 0.0)
    glVertex3f(-1.0,  1.0,  1.0)
    glVertex3f( 1.0,  1.0,  1.0)
    glVertex3f( 1.0,  1.0, -1.0)
    glVertex3f(-1.0,  1.0, -1.0)
    
    # Base (y = -1)
    glNormal3f(0.0, -1.0, 0.0)
    glVertex3f(-1.0, -1.0, -1.0)
    glVertex3f( 1.0, -1.0, -1.0)
    glVertex3f( 1.0, -1.0,  1.0)
    glVertex3f(-1.0, -1.0,  1.0)
    
    glEnd()


def desenhar_objeto():
    """Desenha o objeto padrão selecionado"""
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
            # Em modo Phong, usamos nosso cubo com normais + material especular
            if modelo_iluminacao == 2:
                desenhar_cubo_phong()
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
            glutSolidTeapot(1.0)


def atualizar_camera():
    """Atualiza a posição e direção da câmera baseado em yaw e pitch"""
    global camera_x, camera_y, camera_z, camera_yaw, camera_pitch
    
    # Calcula a direção da câmera baseado no yaw e pitch
    yaw_rad = math.radians(camera_yaw)
    pitch_rad = math.radians(camera_pitch)
    
    # Direção para onde a câmera está olhando
    direcao_x = math.cos(pitch_rad) * math.sin(yaw_rad)
    direcao_y = math.sin(pitch_rad)
    direcao_z = math.cos(pitch_rad) * math.cos(yaw_rad)
    
    # Ponto para onde a câmera está olhando
    look_at_x = camera_x + direcao_x
    look_at_y = camera_y + direcao_y
    look_at_z = camera_z + direcao_z
    
    # Aplica a transformação da câmera
    gluLookAt(camera_x, camera_y, camera_z,
              look_at_x, look_at_y, look_at_z,
              0.0, 1.0, 0.0)


def mover_camera_frente():
    """Move a câmera para frente baseado na direção atual"""
    global camera_x, camera_y, camera_z, camera_yaw, camera_pitch, velocidade_camera
    
    yaw_rad = math.radians(camera_yaw)
    
    # Move apenas no plano horizontal
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera


def mover_camera_tras():
    """Move a câmera para trás baseado na direção atual"""
    global camera_x, camera_y, camera_z, camera_yaw, camera_pitch, velocidade_camera
    
    yaw_rad = math.radians(camera_yaw)
    
    # Move apenas no plano horizontal
    camera_x -= math.sin(yaw_rad) * velocidade_camera
    camera_z -= math.cos(yaw_rad) * velocidade_camera


def mover_camera_esquerda():
    """Move a câmera para a esquerda"""
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    
    yaw_rad = math.radians(camera_yaw + 90)  # 90 graus à direita
    
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera


def mover_camera_direita():
    """Move a câmera para a direita"""
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    
    yaw_rad = math.radians(camera_yaw - 90)  # 90 graus à esquerda
    
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera


# === NOVO: funções para desenhar texto 2D (HUD) ===
def desenhar_texto_2d(x, y, texto):
    """Desenha texto 2D usando coordenadas de janela (pixels)"""
    glRasterPos2f(x, y)
    for ch in texto:
        glutBitmapCharacter(GLUT_BITMAP_9_BY_15, ord(ch))


def desenhar_hud():
    """Desenha informações de comandos na tela"""
    global mostrar_comandos, modo_camera, modelo_iluminacao
    global modo_wireframe, projecao_ortografica, modo_extrusao, extrusao_ativa, objeto_selecionado

    if not mostrar_comandos:
        return

    # Salva matrizes e estado
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()

    width = glutGet(GLUT_WINDOW_WIDTH)
    height = glutGet(GLUT_WINDOW_HEIGHT)

    # Projeção ortográfica em coordenadas de janela
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
        "[Extrusao] [X] adiciona ponto  |  [V] lista pontos  |  [E] ativa extrusao  |  [C] limpa  |  [H/N] altura"
    ]

    for linha in linhas:
        desenhar_texto_2d(x, y, linha)
        y -= 20
    
    # Se estiver em modo extrusão, mostrar lista de pontos
    if modo_extrusao and len(perfil_extrusao) > 0:
        y -= 10  # Espaço extra
        glColor3f(1.0, 1.0, 0.0)  # Amarelo para destacar
        desenhar_texto_2d(x, y, f"--- Pontos do Perfil (Total: {len(perfil_extrusao)}) ---")
        y -= 20
        
        glColor3f(0.8, 0.8, 0.8)  # Cinza claro para os pontos
        # Mostrar até 8 pontos para não poluir a tela
        pontos_mostrar = min(8, len(perfil_extrusao))
        for i in range(pontos_mostrar):
            px, py = perfil_extrusao[i]
            desenhar_texto_2d(x, y, f"  P{i+1}: ({px:.2f}, {py:.2f})")
            y -= 18
        
        # Se tiver mais pontos, indicar
        if len(perfil_extrusao) > pontos_mostrar:
            desenhar_texto_2d(x, y, f"  ... e mais {len(perfil_extrusao) - pontos_mostrar} pontos (pressione [V] para ver todos)")
            y -= 18
        
        glColor3f(1.0, 1.0, 1.0)  # Volta para branco

    # Restaura estado
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
    
    # 1. Câmera (Móvel ou Fixa dependendo do modo)
    if modo_camera:
        atualizar_camera()
    else:
        # Câmera fixa (modo original)
        gluLookAt(0.0, 0.0, 10.0,  0.0, 0.0, 0.0,  0.0, 1.0, 0.0)
    
    # 2. Posicionar a Luz
    posicao_luz = [luz_x, luz_y, luz_z, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, posicao_luz)
    
    # Desenha esfera amarela representando a luz
    glPushMatrix()
    glTranslatef(luz_x, luz_y, luz_z)
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 0.0)
    glutSolidSphere(0.2, 10, 10)
    glEnable(GL_LIGHTING)
    glPopMatrix()
    
    # 3. Configura Iluminação e Transformações
    configurar_iluminacao_renderizacao()
    
    glPushMatrix()
    glTranslatef(pos_x, pos_y, pos_z)
    glRotatef(rot_x, 1.0, 0.0, 0.0)
    glRotatef(rot_y, 0.0, 1.0, 0.0)
    glScalef(scale, scale, scale)
    
    # 4. Desenha Objeto
    desenhar_objeto()
    
    glPopMatrix()

    # 5. Desenha HUD com comandos na tela (não interfere na extrusao)
    desenhar_hud()

    glutSwapBuffers()


def reshape(w, h):
    global projecao_ortografica
    
    if h == 0: h = 1
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    
    # Aspect ratio sempre é largura/altura
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
    
    # Alternar entre modo câmera e modo objeto
    if key == b'0':
        modo_camera = not modo_camera
        mouse_capturado = modo_camera
        if modo_camera:
            print("Modo: CÂMERA (WASD + Mouse)")
            # Vetor da câmera para o objeto
            dx = 0.0 - camera_x
            dy = 0.0 - camera_y
            dz = 0.0 - camera_z
            # Calcula distância horizontal
            dist_horizontal = math.sqrt(dx * dx + dz * dz)
            # Calcula yaw (rotação horizontal)
            camera_yaw = math.degrees(math.atan2(dx, dz))
            # Calcula pitch (rotação vertical)
            camera_pitch = math.degrees(math.atan2(dy, dist_horizontal))
            # Captura o mouse quando entra no modo câmera
            glutSetCursor(GLUT_CURSOR_NONE)
            # Inicializa posição do mouse
            ultimo_mouse_x = glutGet(GLUT_WINDOW_WIDTH) // 2
            ultimo_mouse_y = glutGet(GLUT_WINDOW_HEIGHT) // 2
            glutWarpPointer(ultimo_mouse_x, ultimo_mouse_y)
        else:
            print("Modo: OBJETO (WASD move objeto)")
            glutSetCursor(GLUT_CURSOR_INHERIT)
        glutPostRedisplay()
        return
    
    # Seleção de Objetos Padrões (1-5) e Modo Extrusão (6)
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
        extrusao_ativa = False  # Começa com extrusão desativada para ver o perfil 2D
        print("\n" + "="*60)
        print(">>> MODO EXTRUSÃO ATIVADO <<<")
        print("="*60)
        print("Use [X] para adicionar pontos via coordenadas manuais")
        print("Use [V] para visualizar lista de pontos")
        print("Controles: [E] Ativar/Desativar extrusão 3D | [C] Limpar perfil")
        print("           [H] Aumentar altura | [N] Diminuir altura")
        print("="*60)
    
    # Controles WASD - dependem do modo atual
    if modo_camera:
        # Modo Câmera: WASD move a câmera
        if key == b'w' or key == b'W':
            mover_camera_frente()
        elif key == b's' or key == b'S':
            mover_camera_tras()
        elif key == b'a' or key == b'A':
            mover_camera_esquerda()
        elif key == b'd' or key == b'D':
            mover_camera_direita()
    else:
        # Modo Objeto: WASD gira o objeto
        if key == b'w' or key == b'W': rot_x -= 5.0
        elif key == b's' or key == b'S': rot_x += 5.0
        elif key == b'a' or key == b'A': rot_y -= 5.0
        elif key == b'd' or key == b'D': rot_y += 5.0
    
    # Controles que funcionam em ambos os modos
    if key == b'+': 
        scale += 0.1
    elif key == b'-': 
        scale = max(0.1, scale - 0.1)
    
    # Luz (IJKL - Movimento da Fonte de Luz)
    elif key == b'i' or key == b'I': luz_y += 0.5
    elif key == b'k' or key == b'K': luz_y -= 0.5
    elif key == b'j' or key == b'J': luz_x -= 0.5
    elif key == b'l' or key == b'L': luz_x += 0.5
    elif key == b'u' or key == b'U': luz_z -= 0.5
    elif key == b'o' or key == b'O': luz_z += 0.5
    
    # Configurações
    elif key == b'p' or key == b'P':
        projecao_ortografica = not projecao_ortografica
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        
    elif key == b'm' or key == b'M':
        modelo_iluminacao = (modelo_iluminacao + 1) % 3
        nomes = ["Flat", "Gouraud", "Phong"]
        print(f"Modo Iluminacao: {nomes[modelo_iluminacao]}")
    
    elif key == b'f' or key == b'F':
        modo_wireframe = not modo_wireframe
        print(f"Renderização: {'Wireframe' if modo_wireframe else 'Solid'}")

    # === NOVO: mostrar/ocultar HUD ===
    elif key == b't' or key == b'T':
        mostrar_comandos = not mostrar_comandos

    # Controles do Modo Extrusão
    if modo_extrusao:
        if key == b'x' or key == b'X':
            # Adicionar ponto via entrada manual no terminal
            ler_coordenadas_terminal()
        elif key == b'v' or key == b'V':
            # Visualizar lista de coordenadas no terminal
            listar_coordenadas_terminal()
        elif key == b'e' or key == b'E':
            extrusao_ativa = not extrusao_ativa
            if extrusao_ativa:
                print("Extrusão 3D ATIVADA")
            else:
                print("Extrusão 3D DESATIVADA - Modo edição de perfil 2D")
            glutPostRedisplay()
        elif key == b'c' or key == b'C':
            limpar_perfil()
            extrusao_ativa = False
            glutPostRedisplay()
        elif key == b'h' or key == b'H':
            altura_extrusao += 0.2
            print(f"Altura extrusão: {altura_extrusao:.2f}")
            glutPostRedisplay()
        elif key == b'n' or key == b'N':
            altura_extrusao = max(0.1, altura_extrusao - 0.2)
            print(f"Altura extrusão: {altura_extrusao:.2f}")
            glutPostRedisplay()

    glutPostRedisplay()


def mouse_motion(x, y):
    """Função chamada quando o mouse se move"""
    global camera_yaw, camera_pitch, ultimo_mouse_x, ultimo_mouse_y
    global mouse_capturado, sensibilidade_mouse, modo_camera
    
    if not modo_camera or not mouse_capturado:
        return
    
    # Calcula a diferença de movimento
    dx = x - ultimo_mouse_x
    dy = y - ultimo_mouse_y
    
    # Atualiza yaw e pitch
    camera_yaw -= dx * sensibilidade_mouse
    camera_pitch -= dy * sensibilidade_mouse
    
    # Limita o pitch para evitar rotação completa
    camera_pitch = max(-89.0, min(89.0, camera_pitch))
    
    # Mantém o mouse no centro da tela
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
    """Função desabilitada - entrada de pontos agora é apenas via teclado"""
    # Sistema de clique do mouse removido para maior precisão
    # Use a tecla X para adicionar pontos manualmente via terminal
    pass


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Trabalho CG 3D")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    glutPassiveMotionFunc(mouse_motion)  # Para capturar movimento do mouse (câmera)
    
    print("=" * 60)
    print("              TRABALHO CG 3D - CONTROLES")
    print("=" * 60)
    print("\n--- CONTROLES GERAIS ---")
    print("[0] Alternar entre Modo Câmera e Modo Objeto")
    print("[1-5] Selecionar Objeto Padrão | [6] Modo Extrusão")
    print("[WASD] Girar Objeto (Modo Objeto) | Mover Câmera (Modo Câmera)")
    print("[Mouse] Olhar ao redor (apenas Modo Câmera)")
    print("[Setas] Mover Objeto")
    print("[IJKL] Mover Luz     | [UO] Luz Z (Fundo/Frente)")
    print("[M] Modo Iluminação (Flat/Gouraud/Phong)")
    print("[P] Projeção         | [F] Wireframe/Solid")
    print("[T] Mostrar/Ocultar comandos na tela")
    print("\n--- MODO EXTRUSÃO ---")
    print("[X] Adicionar ponto ao perfil (entrada manual via terminal)")
    print("[V] Visualizar lista de todos os pontos no terminal")
    print("[E] Ativar/Desativar extrusão 3D (ver perfil 2D ou objeto 3D)")
    print("[C] Limpar perfil | [H] Aumentar altura | [N] Diminuir altura")
    print("\n--- LIMITES DE COORDENADAS ---")
    print("Range recomendado: X e Y entre -5.0 e 5.0")
    print("(Valores fora deste range serão ajustados automaticamente)")
    print("=" * 60)
    
    glutMainLoop()


if __name__ == "__main__":
    main()
