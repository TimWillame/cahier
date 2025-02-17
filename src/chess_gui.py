import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QPushButton, QSizePolicy, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QFileDialog
from PySide6.QtGui import QIcon, QDrag, QPixmap, QPainter, QPen, QPolygonF
from PySide6.QtCore import Qt, QMimeData, QSize, QPointF
import chess
import chess.pgn
import io

class ChessGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess GUI with python-chess")
        self.setGeometry(100, 100, 600, 600)

        # Chessboard logic from python-chess
        self.board = chess.Board()

        # Set up the GUI layout (here central)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Place the chessboard and the move history
        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        # Chessboard setup
        self.chessboard_widget = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.chessboard_widget.setLayout(self.grid_layout)  # Supprime les marges
        self.grid_layout.setSpacing(0)

        # Create board buttons
        self.squares = {}
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                button = ChessButton(square, self)
                self.grid_layout.addWidget(button, row, col)
                self.squares[square] = button
                button.setStyleSheet("background-color: {}".format("#EEEED2" if (row + col) % 2 == 0 else "#769656"))

        # Move history setup
        self.sidebar_layout = QVBoxLayout()

        self.move_history_widget = QTextEdit()
        self.move_history_widget.setReadOnly(True)
        self.move_history_widget.setFixedWidth(200)
        self.move_history_widget.setStyleSheet("font-size: 14px;")

        # Bouton pour exporter le PGN
        self.export_pgn_button = QPushButton("Exporter PGN")
        self.export_pgn_button.clicked.connect(self.export_pgn)

        # Ajout à la barre latérale
        self.sidebar_layout.addWidget(self.move_history_widget)
        self.sidebar_layout.addWidget(self.export_pgn_button)

        # Add widgets to the main layout
        self.main_layout.addWidget(self.chessboard_widget)
        self.main_layout.addLayout(self.sidebar_layout)

        self.chessboard_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.main_layout.setStretch(0, 1)
        self.main_layout.setStretch(1, 0)

        self.update_board()

    def update_board(self):
        """Updates the GUI to reflect the current state of the board."""
        for square, button in self.squares.items():
            piece = self.board.piece_at(square)
            if piece:
                color = "w" if piece.color == chess.WHITE else "b"
                piece_name = piece.piece_type
                piece_map = {
                    chess.PAWN: "p",
                    chess.ROOK: "r",
                    chess.KNIGHT: "n",
                    chess.BISHOP: "b",
                    chess.QUEEN: "q",
                    chess.KING: "k"
                }
                piece_image = os.path.join(r'src\assets', 'pieces', f'{color + piece_map[piece_name]}.png')
                icon = QIcon(piece_image)
                button.setIcon(icon)
                button.setIconSize(button.size())
            else:
                button.setIcon(QIcon())  # Clear the button if no piece is on the square

    def handle_click(self, square):
        """Handles user clicking on a square."""
        if not hasattr(self, "selected_square") or self.selected_square is None:
            self.selected_square = square
        else:
            move = chess.Move(self.selected_square, square)
            if move in self.board.legal_moves:
                self.board.push(move)
                self.update_board()
                self.update_move_history()
            self.selected_square = None

    def handle_drop(self, from_square, to_square):
        move = chess.Move(from_square, to_square)
        if move in self.board.legal_moves:
            self.board.push(move)
            self.update_board()
            self.update_move_history()

    def update_move_history(self):
        """Updates the move history display"""
        self.move_history_widget.clear()
        move_history = list(self.board.move_stack)

        board_copy = self.board.copy()
        move_stack = list(self.board.move_stack)

        move_number = 1
        board_copy.reset()

        move_text = ""
        for i in range(0, len(move_stack), 2):
            white_move = board_copy.san(move_stack[i])
            board_copy.push(move_stack[i])

            black_move = ""
            if i + 1 < len(move_stack):
                black_move = board_copy.san(move_stack[i + 1])
                board_copy.push(move_stack[i + 1])

            move_text += f"{move_number}. {white_move} {black_move}\n"
            move_number += 1

        self.move_history_widget.setText(move_text)

    def export_pgn(self):
        """Exporte la partie actuelle en format PGN."""
        game = chess.pgn.Game()
        game.headers["Event"] = "Partie d'échecs"
        game.headers["Site"] = "Chess GUI"
        game.headers["Date"] = "NaN"
        game.headers["Round"] = "NaN"
        game.headers["White"] = "Joueur Blanc"
        game.headers["Black"] = "Joueur Noir"

        node = game
        board_copy = self.board.copy()
        for move in board_copy.move_stack:
            node = node.add_variation(move)

        exporter = chess.pgn.StringExporter(columns=None)
        pgn_string = game.accept(exporter)

        with open("partie.pgn", "w", encoding="utf-8") as f:
            f.write(pgn_string)

        print("Partie exportée en PGN.")

    def get_threats(self):
        """Retourne la liste des menaces sous forme de tuples (from_square, to_square)."""
        threats = []
        for move in self.board.legal_moves:
            if self.board.is_capture(move):
                threats.append((move.from_square, move.to_square))
        # print("Threats:", threats) 
        return threats



class ChessButton(QPushButton):
    def __init__(self, square, parent):
        super().__init__()
        self.square = square
        self.parent = parent
        self.setFixedSize(80, 80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAcceptDrops(True)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.parent.handle_click(self.square)

    def mouseMoveEvent(self, event):
        piece = self.parent.board.piece_at(self.square)
        if not piece:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(str(self.square))
        drag.setMimeData(mime_data)

        icon = self.icon()
        if not icon.isNull():
            pixmap = icon.pixmap(64, 64)
            drag.setPixmap(pixmap)

        drag.exec(Qt.MoveAction)

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        source_square = int(event.mimeData().text())
        self.parent.handle_drop(source_square, self.square)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChessGUI()
    window.show()
    sys.exit(app.exec())