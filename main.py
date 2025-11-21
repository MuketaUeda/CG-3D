import sys
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# ==========================================
# Variáveis Globais
# ==========================================
# Estado do Objeto
rot_x, rot_y = 0.0, 0.0
pos_x, pos_y, pos_z = 0.0, 0.0, 0.0
scale = 1.0

# Estado da Luz (NOVO)
luz_x, luz_y, luz_z = 5.0, 5.0, 5.0

# Estado da Câmera/Visualização
projecao_ortografica = False  # False=Perspectiva, True=Ortográfica

# Estado da Iluminação
# 0: Flat, 1: Gouraud (Suave), 2: Phong (Suave + Brilho)
modelo_iluminacao = 0

# Estado de Renderização
modo_wireframe = False  # True=Wireframe, False=Solid 

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

def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # 1. Câmera Fixa
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
    glColor3f(0.0, 0.5, 1.0) # Azul
    if modo_wireframe:
        glutWireSphere(1.0, 10, 10)
    else:
        glutSolidSphere(1.0, 20, 20)  # Mais detalhes quando sólido
    
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
    
    # Objeto
    if key == b'w' or key == b'W': rot_x -= 5.0
    elif key == b's' or key == b'S': rot_x += 5.0
    elif key == b'a' or key == b'A': rot_y -= 5.0
    elif key == b'd' or key == b'D': rot_y += 5.0
    elif key == b'+': scale += 0.1
    elif key == b'-': scale = max(0.1, scale - 0.1)
    
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
        
    elif key == b'm' or key == b'M': # M de Modo de Iluminação
        modelo_iluminacao = (modelo_iluminacao + 1) % 3
        print(f"Modo: {modelo_iluminacao}")
    
    elif key == b'f' or key == b'F': # F de Fill (Wireframe/Solid)
        modo_wireframe = not modo_wireframe
        print(f"Renderização: {'Wireframe' if modo_wireframe else 'Solid'}")

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
    glutCreateWindow(b"Fase 4: Luz Movel (IJKL)")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_keys)
    
    print("--- CONTROLES ---")
    print("[WASD] Girar Objeto  | [Setas] Mover Objeto")
    print("[IJKL] Mover Luz     | [UO] Luz Z (Fundo/Frente)")
    print("[M] Modo Iluminação (Flat/Gouraud/Phong)")
    print("[P] Projeção         | [F] Wireframe/Solid")
    
    glutMainLoop()

if __name__ == "__main__":
    main()