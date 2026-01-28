import sys
import os
from PyQt6 import QtWidgets, QtGui, QtCore
import vlc
import glob

MUSIC_FOLDER = "/home/rob/Music/"

def find_album_art(audio_path):
    base = os.path.splitext(audio_path)[0]
    for ext in [".jpg", ".jpeg", ".png"]:
        candidate = base + ext
        if os.path.exists(candidate):
            return candidate
    return None

class MusicWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        # Get songs
        self.songs = glob.glob(os.path.join(MUSIC_FOLDER, "*.mp3"))
        self.current_index = 0

        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        self.setWindowTitle("Music Widget")
        self.setFixedSize(260, 360)

        # VLC
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()

        # Main layout
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.setLayout(layout)

        # Album art
        self.art_label = QtWidgets.QLabel()
        self.art_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.art_label)
        self.update_album_art()

        # Song title label
        self.title_label = QtWidgets.QLabel("")
        self.title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.title_label.setStyleSheet("color: white; font-size: 14px;")
        layout.addWidget(self.title_label)
        self.update_song_title()


        # Progress bar
        self.progress = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.progress.setRange(0, 1000)
        self.progress.sliderReleased.connect(self.seek)
        layout.addWidget(self.progress)

        # Timer
        self.timer = QtCore.QTimer()
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.update_progress)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(btn_layout)

        self.prev_btn = QtWidgets.QPushButton("<<")
        self.play_btn = QtWidgets.QPushButton("Play")
        self.next_btn = QtWidgets.QPushButton(">>")

        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.play_btn)
        btn_layout.addWidget(self.next_btn)

        # Connect
        self.play_btn.clicked.connect(self.toggle_play)
        self.prev_btn.clicked.connect(self.prev_song)
        self.next_btn.clicked.connect(self.next_song)

        # Volume slider (minimal)
        self.volume = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(70)  # default volume
        self.volume.setFixedHeight(14)
        self.volume.valueChanged.connect(self.set_volume)

        self.volume.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255,255,255,80);
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                width: 10px;
                height: 10px;
                margin: -3px 0;
                border-radius: 5px;
                background: white;
            }
        """)

        layout.addWidget(self.volume)

        self.player.audio_set_volume(50)

    # ----------------------------------------------------

    def toggle_play(self):
        """Play/Pause toggle."""
        state = self.player.get_state()

        if state in (vlc.State.Playing, vlc.State.Buffering):
            self.player.pause()
            self.play_btn.setText("Play")
        else:
            self.player.play()   # resume instead of restarting
            self.play_btn.setText("Pause")

    # ----------------------------------------------------

    def update_album_art(self):
        if self.songs:
            art_path = find_album_art(self.songs[self.current_index])
        else:
            art_path = None

        if art_path:
            pixmap = QtGui.QPixmap(art_path)
            pixmap = pixmap.scaled(
                200, 200,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation
            )

            final_pix = QtGui.QPixmap(200, 200)
            final_pix.fill(QtCore.Qt.GlobalColor.transparent)
            painter = QtGui.QPainter(final_pix)
            painter.drawPixmap(
                (200 - pixmap.width()) // 2,
                (200 - pixmap.height()) // 2,
                pixmap
            )
            painter.end()

            self.art_label.setPixmap(final_pix)
        else:
            fallback = QtGui.QPixmap(200, 200)
            fallback.fill(QtGui.QColor("darkgray"))
            self.art_label.setPixmap(fallback)

    def update_song_title(self):
        if not self.songs:
            self.title_label.setText("")
            return

        filename = os.path.basename(self.songs[self.current_index])
        title = os.path.splitext(filename)[0]
        self.title_label.setText(title)


    # ----------------------------------------------------

    def play(self):
        if not self.songs:
            return

        current_song = self.songs[self.current_index]
        media = self.instance.media_new(current_song)
        self.player.set_media(media)
        self.player.play()

        self.timer.start()
        self.update_album_art()
        self.update_song_title()

    def next_song(self):
        if not self.songs:
            return
        self.current_index = (self.current_index + 1) % len(self.songs)
        self.play()
        self.update_song_title()

    def prev_song(self):
        if not self.songs:
            return
        self.current_index = (self.current_index - 1) % len(self.songs)
        self.play()
        self.update_song_title()

    def update_progress(self):
        if self.player.get_length() <= 0:
            return
        pos = self.player.get_position()
        self.progress.setValue(int(pos * 1000))

    def seek(self):
        value = self.progress.value() / 1000
        self.player.set_position(value)

    def set_volume(self, value):
        self.player.audio_set_volume(value)

# ----------------------------------------------------

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    widget = MusicWidget()
    widget.show()
    sys.exit(app.exec())
