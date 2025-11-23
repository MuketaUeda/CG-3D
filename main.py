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
camera_x, camera_y, camera_z = 0.0, 0.0, 10.0  # Posição da câmera
camera_yaw = 0.0    # Rotação horizontal (esquerda/direita)
camera_pitch = 0.0  # Rotação vertical (cima/baixo)
velocidade_camera = 0.1  # Velocidade de movimento da câmera
sensibilidade_mouse = 0.1  # Sensibilidade do mouse
ultimo_mouse_x = 0
ultimo_mouse_y = 0
mouse_capturado = False

# Estado da Iluminação
# 0: Flat, 1: Gouraud (Suave), 2: Phong (Suave + Brilho)
modelo_iluminacao = 0

# Estado de Renderização
modo_wireframe = False  # True=Wireframe, False=Solid

# Estado do Objeto Selecionado
# 1=Esfera, 2=Cubo, 3=Cone, 4=Torus, 5=Teapot, 6=Modo Extrusão
objeto_selecionado = 1  # Começa com esfera
modo_extrusao = False   # True quando estiver no modo extrusão 

def init():
    """Configurações iniciais do OpenGL"""
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glEnable(GL_DEPTH_TEST)
    
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
        # --- PHONG (Simulado) ---
        glShadeModel(GL_SMOOTH)
        glMaterialfv(GL_FRONT, GL_SPECULAR, [1, 1, 1, 1])
        glMaterialf(GL_FRONT, GL_SHININESS, 60.0)

def desenhar_objeto():
    """Desenha o objeto padrão selecionado"""
    global objeto_selecionado, modo_wireframe, modo_extrusao
    
    if modo_extrusao:
        # TODO: Implementar desenho de extrusão aqui
        glColor3f(1.0, 0.5, 0.0) # Laranja para diferenciar
        glutSolidSphere(1.0, 10, 10)  # Placeholder
        print("Modo Extrusão (A ser implementado)")
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
    pitch_rad = math.radians(camera_pitch)
    
    # Move apenas no plano horizontal (ignora pitch para movimento)
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera

def mover_camera_tras():
    """Move a câmera para trás baseado na direção atual"""
    global camera_x, camera_y, camera_z, camera_yaw, camera_pitch, velocidade_camera
    
    yaw_rad = math.radians(camera_yaw)
    pitch_rad = math.radians(camera_pitch)
    
    # Move apenas no plano horizontal (ignora pitch para movimento)
    camera_x -= math.sin(yaw_rad) * velocidade_camera
    camera_z -= math.cos(yaw_rad) * velocidade_camera

def mover_camera_esquerda():
    """Move a câmera para a esquerda"""
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    
    yaw_rad = math.radians(camera_yaw + 90)  # 90 graus à direita (vetor perpendicular à esquerda)
    
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera

def mover_camera_direita():
    """Move a câmera para a direita"""
    global camera_x, camera_y, camera_z, camera_yaw, velocidade_camera
    
    yaw_rad = math.radians(camera_yaw - 90)  # 90 graus à esquerda (vetor perpendicular à direita)
    
    camera_x += math.sin(yaw_rad) * velocidade_camera
    camera_z += math.cos(yaw_rad) * velocidade_camera

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # 1. Câmera (Móvel ou Fixa dependendo do modo)
    if modo_camera:
        atualizar_camera()
    else:
        # Câmera fixa (modo original)
        gluLookAt(0.0, 0.0, 10.0,  0.0, 0.0, 0.0,  0.0, 1.0, 0.0)
    
    # 2. Posicionar a Luz (MÓVEL)
    # Usamos as variáveis globais luz_x, luz_y, luz_z
    posicao_luz = [luz_x, luz_y, luz_z, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, posicao_luz)
    
    # Desenha esfera amarela representando a luz (Debug Visual)
    glPushMatrix()
    glTranslatef(luz_x, luz_y, luz_z)
    glDisable(GL_LIGHTING)
    glColor3f(1.0, 1.0, 0.0) # Amarelo
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
    glutSwapBuffers()

def reshape(w, h):
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
    global objeto_selecionado, modo_extrusao
    global modo_camera, mouse_capturado
    
    # Alternar entre modo câmera e modo objeto
    if key == b'0':
        modo_camera = not modo_camera
        mouse_capturado = modo_camera
        if modo_camera:
            print("Modo: CÂMERA (WASD + Mouse)")
            # Calcula yaw e pitch para olhar para o objeto (0, 0, 0)
            global camera_yaw, camera_pitch
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
            global ultimo_mouse_x, ultimo_mouse_y
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
        print("Objeto: Esfera")
    elif key == b'2':
        objeto_selecionado = 2
        modo_extrusao = False
        print("Objeto: Cubo")
    elif key == b'3':
        objeto_selecionado = 3
        modo_extrusao = False
        print("Objeto: Cone")
    elif key == b'4':
        objeto_selecionado = 4
        modo_extrusao = False
        print("Objeto: Torus")
    elif key == b'5':
        objeto_selecionado = 5
        modo_extrusao = False
        print("Objeto: Teapot")
    elif key == b'6':
        modo_extrusao = True
        print("Modo Extrusão (A ser implementado)")
    
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
        # Modo Objeto: WASD gira o objeto (comportamento original)
        if key == b'w' or key == b'W': rot_x -= 5.0
        elif key == b's' or key == b'S': rot_x += 5.0
        elif key == b'a' or key == b'A': rot_y -= 5.0
        elif key == b'd' or key == b'D': rot_y += 5.0
    
    # Controles que funcionam em ambos os modos
    if key == b'+': scale += 0.1
    elif key == b'-': scale = max(0.1, scale - 0.1)
    
    # Luz (IJKL - Movimento da Fonte de Luz)
    elif key == b'i' or key == b'I': luz_y += 0.5
    elif key == b'k' or key == b'K': luz_y -= 0.5
    elif key == b'j' or key == b'J': luz_x -= 0.5  # J move para esquerda
    elif key == b'l' or key == b'L': luz_x += 0.5  # L move para direita
    elif key == b'u' or key == b'U': luz_z -= 0.5
    elif key == b'o' or key == b'O': luz_z += 0.5
    
    # Configurações
    elif key == b'p' or key == b'P':
        projecao_ortografica = not projecao_ortografica
        reshape(glutGet(GLUT_WINDOW_WIDTH), glutGet(GLUT_WINDOW_HEIGHT))
        
    elif key == b'm' or key == b'M': # M de Modo de Iluminação
        modelo_iluminacao = (modelo_iluminacao + 1) % 3
        print(f"Modo: {modelo_iluminacao}")
    
    elif key == b'f' or key == b'F': # F de Fill (Wireframe/Solid)
        modo_wireframe = not modo_wireframe
        print(f"Renderização: {'Wireframe' if modo_wireframe else 'Solid'}")

    glutPostRedisplay()

def mouse_motion(x, y):
    """Função chamada quando o mouse se move"""
    global camera_yaw, camera_pitch, ultimo_mouse_x, ultimo_mouse_y
    global mouse_capturado, sensibilidade_mouse
    
    if not modo_camera or not mouse_capturado:
        return
    
    # Calcula a diferença de movimento
    dx = x - ultimo_mouse_x
    dy = y - ultimo_mouse_y
    
    # Atualiza yaw e pitch
    camera_yaw -= dx * sensibilidade_mouse  # Invertido para corrigir direção
    camera_pitch -= dy * sensibilidade_mouse  # Mouse para baixo = olhar para baixo
    
    # Limita o pitch para evitar rotação completa
    camera_pitch = max(-89.0, min(89.0, camera_pitch))
    
    # Mantém o mouse no centro da tela (opcional, para melhor controle)
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
    glutPassiveMotionFunc(mouse_motion)  # Para capturar movimento do mouse
    
    print("--- CONTROLES ---")
    print("[0] Alternar entre Modo Câmera e Modo Objeto")
    print("[1-5] Selecionar Objeto Padrão | [6] Modo Extrusão")
    print("[WASD] Girar Objeto (Modo Objeto) | Mover Câmera (Modo Câmera)")
    print("[Mouse] Olhar ao redor (Modo Câmera)")
    print("[Setas] Mover Objeto")
    print("[IJKL] Mover Luz     | [UO] Luz Z (Fundo/Frente)")
    print("[M] Modo Iluminação (Flat/Gouraud/Phong)")
    print("[P] Projeção         | [F] Wireframe/Solid")
    
    glutMainLoop()

if __name__ == "__main__":
    main()