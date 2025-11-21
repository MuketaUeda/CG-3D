import sys
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

# ==========================================
# Variáveis Globais (Estado do Objeto)
# ==========================================
# Rotação (em graus)
rot_x = 0.0
rot_y = 0.0

# Posição (Translação X, Y, Z)
pos_x = 0.0
pos_y = 0.0
pos_z = 0.0

# Escala
scale = 1.0

#Projeção
projecao_ortografica = False

# Modo de renderização do cubo
modo_wireframe = False  # False = sólido, True = wireframe

def init():
    """Configurações iniciais do OpenGL"""
    # Cor de fundo (Preto: R=0, G=0, B=0, Alpha=1)
    glClearColor(0.0, 0.0, 0.0, 1.0)
    
    # Habilita o Z-Buffer (Profundidade). 
    # Sem isso, o OpenGL não sabe o que está na frente ou atrás.
    glEnable(GL_DEPTH_TEST)

def display():
    """Função principal de renderização (chamada a cada frame)"""
    # 1. Limpa os buffers de Cor e Profundidade
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # 2. Reseta a matriz de transformações
    glLoadIdentity()
    
    # 3. Posiciona a Câmera (Observador)
    # gluLookAt(eyeX, eyeY, eyeZ,  centerX, centerY, centerZ,  upX, upY, upZ)
    gluLookAt(0.0, 0.0, 10.0,      # Posição da câmera
              0.0, 0.0, 0.0,       # Para onde ela olha (Origem)
              0.0, 1.0, 0.0)       # Onde é "cima" (Eixo Y)
    
    # 4. Aplica Transformações no OBJETO
    # A ordem importa: Translação -> Rotação -> Escala
    glPushMatrix() # Salva a matriz original (só com a câmera)
    
    glTranslatef(pos_x, pos_y, pos_z) # Move
    glRotatef(rot_x, 1.0, 0.0, 0.0)   # Gira no eixo X
    glRotatef(rot_y, 0.0, 1.0, 0.0)   # Gira no eixo Y
    glScalef(scale, scale, scale)     # Aumenta/Diminui
    
    # 5. Desenha o Objeto
    glColor3f(1.0, 0.0, 0.0) # Define cor Vermelha para o objeto
    if modo_wireframe:
        glutWireCube(1.0)     # Cubo wireframe (apenas arestas)
    else:
        glutSolidCube(1.0)    # Cubo sólido (preenchido)
    
    glPopMatrix() # Restaura a matriz para não afetar outros objetos futuros
    
    # 6. Troca os buffers (Double Buffering) para mostrar o desenho
    glutSwapBuffers()


def reshape(w, h):
    """Chamada quando a janela é redimensionada ou mudamos a projeção"""
    global largura_janela, altura_janela # Guardar para usar depois se precisar
    largura_janela = w
    altura_janela = h
    
    if h == 0: h = 1
    aspecto = w / h
    
    glViewport(0, 0, w, h)
    
    # Entra no modo de Projeção (Lente da Câmera)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    
    if projecao_ortografica:
        # Projeção Ortográfica (Caixa retangular)
        # glOrtho(left, right, bottom, top, near, far)
        # Ajustamos o volume para garantir que o objeto caiba na tela
        if w <= h:
            glOrtho(-10, 10, -10*h/w, 10*h/w, 0.1, 100.0)
        else:
            glOrtho(-10*w/h, 10*w/h, -10, 10, 0.1, 100.0)
    else:
        # Projeção Perspectiva (Cone de visão)
        # gluPerspective(fovy, aspect, zNear, zFar)
        gluPerspective(45, aspecto, 0.1, 100.0)
    
    # Volta para o modo Modelagem (Mundo)
    glMatrixMode(GL_MODELVIEW)

def keyboard(key, x, y):
    """Controle por Teclas (Rotação e Escala)"""
    global rot_x, rot_y, scale, projecao_ortografica, modo_wireframe
    
    # Rotação com WASD
    if key == b'w' or key == b'W':
        rot_x -= 5.0
    elif key == b's' or key == b'S':
        rot_x += 5.0
    elif key == b'a' or key == b'A':
        rot_y -= 5.0
    elif key == b'd' or key == b'D':
        rot_y += 5.0
        
    # Escala com + e -
    elif key == b'+':
        scale += 0.1
    elif key == b'-':
        scale -= 0.1
        if scale < 0.1: scale = 0.1
    
    elif key == b'p' or key == b'P':
        projecao_ortografica = not projecao_ortografica
        # Força o re-cálculo da matriz de projeção usando o tamanho atual da janela
        # Usamos glutGet para pegar o tamanho atual da janela
        w = glutGet(GLUT_WINDOW_WIDTH)
        h = glutGet(GLUT_WINDOW_HEIGHT)
        reshape(w, h)
        print("Projeção: " + ("Ortográfica" if projecao_ortografica else "Perspectiva"))
    
    elif key == b'f' or key == b'F':
        modo_wireframe = not modo_wireframe
        print("Modo: " + ("Wireframe" if modo_wireframe else "Sólido"))
        
    glutPostRedisplay()
        
def special_keys(key, x, y):
    """Controle por Teclas Especiais (Setas para Mover)"""
    global pos_x, pos_y
    
    if key == GLUT_KEY_UP:
        pos_y += 0.1
    elif key == GLUT_KEY_DOWN:
        pos_y -= 0.1
    elif key == GLUT_KEY_LEFT:
        pos_x -= 0.1
    elif key == GLUT_KEY_RIGHT:
        pos_x += 0.1
        
    glutPostRedisplay()

# ==========================================
# Função Principal
# ==========================================
def main():
    # 1. Inicializa GLUT
    glutInit(sys.argv)
    
    # 2. Configura modo de display:
    # DOUBLE: Evita flicker (piscar)
    # RGB: Cores reais
    # DEPTH: Z-Buffer (profundidade)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    
    # 3. Cria Janela
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"Trabalho CG 3D")
    
    # 4. Configurações iniciais do OpenGL (cor, depth)
    init()
    
    # 5. Registra Funções de Callback
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard) # Teclas normais (letras)
    glutSpecialFunc(special_keys) # Teclas especiais (setas)
    
    # 6. Entra no loop infinito
    print("Controles:")
    print("Setas: Mover | WASD: Girar | +/-: Zoom | P: Projeção | F: Wireframe/Sólido")
    glutMainLoop()

if __name__ == "__main__":
    main()