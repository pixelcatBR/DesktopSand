#!/usr/bin/env python3
import sys
import random
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPainter, QColor, QKeyEvent, QGuiApplication

# --- CONFIGURAÇÕES ---
CELL_SIZE = 4
UI_HEIGHT = 60

CORES = {
    0: (0, 0, 0, 0),       # Vazio (Transparente)
    1: (255, 215, 0, 255), # Areia
    2: (0, 100, 255, 255), # Água
    3: (255, 0, 0, 255),   # Fogo
    4: (139, 69, 19, 255), # Parede
    5: (0, 255, 0, 255),   # Planta
}
MATERIAIS = [1, 2, 3, 4, 5] 

class SandSim:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.material_atual = 1 

    def update(self):
        for y in range(self.rows - 2, -1, -1):
            for x in range(self.cols):
                mat = self.grid[y][x]
                if mat == 0: continue
                # Física Areia
                if mat == 1:
                    if self.grid[y+1][x] == 0: self.grid[y+1][x] = 1; self.grid[y][x] = 0
                    elif self.grid[y+1][x] == 2: self.grid[y+1][x] = 1; self.grid[y][x] = 2
                    elif x > 0 and self.grid[y+1][x-1] == 0: self.grid[y+1][x-1] = 1; self.grid[y][x] = 0
                    elif x < self.cols - 1 and self.grid[y+1][x+1] == 0: self.grid[y+1][x+1] = 1; self.grid[y][x] = 0
                # Física Água
                elif mat == 2:
                    if self.grid[y+1][x] == 0: self.grid[y+1][x] = 2; self.grid[y][x] = 0
                    elif x > 0 and self.grid[y][x-1] == 0: self.grid[y][x-1] = 2; self.grid[y][x] = 0
                    elif x < self.cols - 1 and self.grid[y][x+1] == 0: self.grid[y][x+1] = 2; self.grid[y][x] = 0
                # Física Fogo
                elif mat == 3:
                    if random.random() < 0.05: self.grid[y][x] = 0; continue
                    for dx, dy in [(-1, 0), (1, 0), (0, -1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.cols and 0 <= ny < self.rows:
                            if self.grid[ny][nx] == 0 and random.random() < 0.1: self.grid[ny][nx] = 3
                            elif self.grid[ny][nx] == 5: self.grid[ny][nx] = 3

    def draw_at(self, x, y, is_right_click, ui_y_pixels):
        cx, cy = x // CELL_SIZE, y // CELL_SIZE
        for dy in range(-3, 4):
            for dx in range(-3, 4):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and (ny * CELL_SIZE) < ui_y_pixels:
                    self.grid[ny][nx] = 0 if is_right_click else self.material_atual

class DesktopSand(QWidget):
    def __init__(self):
        super().__init__()
        
        screen = QGuiApplication.primaryScreen()
        self.screen_geom = screen.availableGeometry() 
        self.ui_y_pixels = self.screen_geom.height() - UI_HEIGHT
        self.cols = self.screen_geom.width() // CELL_SIZE
        self.rows = self.screen_geom.height() // CELL_SIZE

        # Janela transparente, sem bordas e sempre no topo
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(self.screen_geom)
        
        self.sim = SandSim(self.cols, self.rows)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_sim)
        self.timer.start(16)

    def update_sim(self):
        self.sim.update()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # Desenha as partículas
        for y in range(self.rows):
            for x in range(self.cols):
                mat = self.sim.grid[y][x]
                if mat != 0:
                    painter.fillRect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE, QColor(*CORES[mat]))

        # Desenha a Interface (Barra de ferramentas)
        ui_width = len(MATERIAIS) * 40 + 20
        painter.fillRect(10, self.ui_y_pixels + 10, ui_width, 40, QColor(40, 40, 40, 220))
        
        for i, mat in enumerate(MATERIAIS):
            rx = 20 + i * 40
            ry = self.ui_y_pixels + 15
            painter.fillRect(rx, ry, 30, 30, QColor(*CORES[mat]))
            
            if self.sim.material_atual == mat:
                painter.setPen(QColor(255, 255, 255, 255))
                painter.drawRect(rx-2, ry-2, 34, 34)
        
        # Texto de ajuda
        painter.setPen(QColor(255, 255, 255, 150))
        painter.drawText(ui_width + 20, self.ui_y_pixels + 35, "ESC: Sair")

    def mousePressEvent(self, event):
        x, y = int(event.position().x()), int(event.position().y())
        
        # Clicou na UI
        if y > self.ui_y_pixels + 10 and x < (len(MATERIAIS) * 40 + 20):
            if event.button() == Qt.MouseButton.LeftButton:
                for i, mat in enumerate(MATERIAIS):
                    rx = 20 + i * 40
                    if rx <= x <= rx + 30:
                        self.sim.material_atual = mat
                        break
        # Clicou para desenhar
        else:
            is_right = (event.buttons() & Qt.MouseButton.RightButton) == Qt.MouseButton.RightButton
            self.sim.draw_at(x, y, is_right, self.ui_y_pixels)

    def mouseMoveEvent(self, event):
        x, y = int(event.position().x()), int(event.position().y())
        if y <= self.ui_y_pixels:
            is_right = (event.buttons() & Qt.MouseButton.RightButton) == Qt.MouseButton.RightButton
            self.sim.draw_at(x, y, is_right, self.ui_y_pixels)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            QApplication.quit()

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        janela = DesktopSand()
        janela.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"\nERRO DETECTADO: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para fechar...")
