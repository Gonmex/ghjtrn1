import sys
import os
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QInputDialog, QMessageBox, QListWidgetItem
from PyQt6.QtCore import QUrl, Qt, QRect
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import yt_dlp


os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "ffmpeg"


class Programm(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("maket.ui", self)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.player.setVideoOutput(self.video_widget)
        self.video_widget.hide()
        self.download_widget.hide()
        self.search_line.textChanged.connect(self.filter_videos)

        self.btn_new.clicked.connect(self.new_video_parameters)
        self.btn_new_video.clicked.connect(self.new_video)
        self.folders_list.itemDoubleClicked.connect(self.play_cliked_video)
        self.btn_new.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.colections_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.folders_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.load_downloaded_videos()

    def resizeEvent(self, _):
        width = self.width()
        height = self.height()

        self.colections_list.setGeometry(10, 50, 260, height - 110)
        self.folders_list.setGeometry(290, 55, width - 300, height - 65)
        self.btn_settings.setGeometry(10, height - 60, 40, 40)
        self.search_line.setGeometry(290, 10, width - 300, 35)
        self.btn_new.setGeometry(width - 70, height - 70, 50, 50)
        self.video_widget.setGeometry(0, 0, width, height)

        self.line_url.setGeometry(30, 60, width - 60, 30)
        self.line_set_name.setGeometry(30, 110, width - 60, 30)
        self.label_format.setGeometry(30, 170, 100, 20)
        self.label_collections.setGeometry(200, 170, width - 230, 20)
        self.verticalLayout.setGeometry(QRect(30, 200, 60, height - 240))
        self.list_set_colections.setGeometry(180, 200, width - 210, height - 240)
        self.btn_new_video.setGeometry(width - 120, height - 50, 100, 30)
        self.download_widget.setGeometry(0, 0, width, height)

    def new_video_parameters(self):
        self.download_widget.show()
        self.colections_list.hide()
        self.btn_settings.hide()
        self.search_line.hide()
        self.btn_new.hide()
        self.folders_list.hide()
        self.video_widget.hide()

    def foramt_parameters(self):
        if self.btn_form_aud.isChecked():
            return "audio", "bestaudio/best"
        elif self.btn_form_360.isChecked():
            return "video", "bestvideo[height<=360]+bestaudio/best[height<=360]"
        elif self.btn_form_480.isChecked():
            return "video", "bestvideo[height<=480]+bestaudio/best[height<=480]"
        elif self.btn_form_720.isChecked():
            return "video", "bestvideo[height<=720]+bestaudio/best[height<=720]"
        elif self.btn_form_1080.isChecked():
            return "video", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
        elif self.btn_form_2k.isChecked():
            return "video", "bestvideo[height<=1440]+bestaudio/best[height<=1440]"
        elif self.btn_form_4k.isChecked():
            return "video", "bestvideo[height<=2160]+bestaudio/best[height<=2160]"
        return "video", "bestvideo+bestaudio/best"

    def new_video(self):
        video_name = self.line_set_name.text()
        url = self.line_url.text()

        if url:
            try:
                if video_name == "":
                    video_names = "%(title)s.%(ext)s"
                else:
                    video_names = f"{video_name}.%(ext)s"

                format, format_str= self.foramt_parameters()
                if format == "audio":
                    final_format = format_str
                else:
                    final_format = f"({format_str})[vcodec!=av01]/best[height<=720]"

                ydl_opts = {
                    "format": final_format,
                    "outtmpl": os.path.join(os.path.join(os.getcwd(), "downloads"), f"{video_names}"),
                    "merge_output_format": "mp4",
                    "ffmpeg_location": os.getcwd(),
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(url, download=True)

                    local_file_path = ydl.prepare_filename(info_dict)

                    base, _ = os.path.splitext(local_file_path)
                    local_file_path = base + ".mp4"

                item = QListWidgetItem(video_name)
                item.setData(Qt.ItemDataRole.UserRole, local_file_path)
                self.folders_list.addItem(item)

                self.line_url.clear()
                self.line_set_name.clear()
                self.download_widget.hide()
                self.colections_list.show()
                self.folders_list.show()
                self.search_line.show()
                self.btn_new.show()
                self.btn_settings.show()
                QMessageBox.information(self, "Найс", f"Видео {video_name} успешно скачано!")
            except Exception:
                pass

    def play_cliked_video(self, item):
        local_path = item.data(Qt.ItemDataRole.UserRole)
        if local_path and os.path.exists(local_path):
            self.play_video(local_path)

    def play_video(self, file_path):
            self.colections_list.hide()
            self.btn_settings.hide()
            self.search_line.hide()
            self.btn_new.hide()
            self.folders_list.hide()
            self.video_widget.show()

            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.audio_output.setVolume(0.67)
            self.player.play()
            self.setFocus()

    def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Escape:
                self.player.stop()
                self.video_widget.hide()
                self.download_widget.hide()

                self.colections_list.show()
                self.folders_list.show()
                self.search_line.show()
                self.btn_new.show()
                self.btn_settings.show()

            if event.key() == Qt.Key.Key_Space:
                if self.video_widget.isVisible():
                    if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                        self.player.pause()
                    else:
                        self.player.play()

    def load_downloaded_videos(self):
        downloads_dir = os.path.join(os.getcwd(), "downloads")
        for file_name in os.listdir(downloads_dir):
            video_title = file_name[0:-5]
            full_path = os.path.join(downloads_dir, file_name)
            item = QListWidgetItem(video_title)
            item.setData(Qt.ItemDataRole.UserRole, full_path)
            self.folders_list.addItem(item)

    def filter_videos(self, text):
        search_text = text.lower()

        for i in range(self.folders_list.count()):
            item = self.folders_list.item(i)
            if search_text in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Programm()
    ex.show()
    sys.exit(app.exec())