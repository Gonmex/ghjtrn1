import sys
import os
from PyQt6 import uic
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QInputDialog, QMessageBox, QListWidgetItem, QMenu
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
        
        self.folders_list.itemDoubleClicked.connect(self.item_double_click)
        
        self.folders_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folders_list.customContextMenuRequested.connect(self.show_context_menu)

        self.btn_new.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.colections_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.folders_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.download_dir = os.path.join(os.getcwd(), "downloads")
        self.current_dir = self.download_dir
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        self.menu_bar_create()
        
        self.load_downloaded_videos()

    def resizeEvent(self, _):
        width = self.width()
        height = self.height()

        self.colections_list.setGeometry(10, 50, 260, height - 140)
        self.folders_list.setGeometry(290, 55, width - 300, height - 80)
        self.btn_settings.setGeometry(10, height - 90, 40, 40)
        self.search_line.setGeometry(290, 10, width - 300, 35)
        self.btn_new.setGeometry(width - 70, height - 100, 50, 50)
        self.video_widget.setGeometry(0, 0, width, height)

        self.line_url.setGeometry(30, 60, width - 60, 30)
        self.line_set_name.setGeometry(30, 110, width - 60, 30)
        self.label_format.setGeometry(30, 170, 100, 20)
        self.label_collections.setGeometry(200, 170, width - 230, 20)
        self.verticalLayout.setGeometry(QRect(30, 200, 120, height - 240))
        self.list_set_colections.setGeometry(240, 200, width - 260, height - 250)
        self.btn_new_video.setGeometry(width - 120, height - 80, 100, 30)
        self.download_widget.setGeometry(0, 0, width, height)
        
    def menu_bar_create(self):
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("Файл")
        exit_action = file_menu.addAction("Выход")
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        
        nav_menu = menu_bar.addMenu("Управление")
        refresh_action = nav_menu.addAction("Обновить список")
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.load_downloaded_videos)
        root_action = nav_menu.addAction("На главную")
        root_action.triggered.connect(self.go_to_root_dir)
        
        help_menu = menu_bar.addMenu("Справка")
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self.show_about_dialog)

    def go_to_root_dir(self):
        self.current_dir = self.download_dir
        self.load_downloaded_videos()

    def show_about_dialog(self):
        QMessageBox.about(
            self,
            "О программе",
            "<h3>MDPlayer (Media Downloader & Player)</h3>"
            "<p>Универсальная программа для скачивания и просмотра видео.</p>"
            "<p><b>Версия:</b> 1.0<br>"
            "<b>Базируется на:</b> PyQt6, yt-dlp, FFmpeg<br>"
            "<b>Создатель:</b> Сергей Кондратьев</p>"
        )

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
        video_name = self.line_set_name.text().strip()
        url = self.line_url.text().strip()

        if url:
            try:
                format, format_str = self.foramt_parameters()
                if format == "audio":
                    final_format = format_str  
                else:
                    final_format = f"{format_str}/best"

                ydl_opts_info = {"extract_flat": "in_playlist"}
                with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
                    info_dict = ydl.extract_info(url, download=False)

                is_playlist = "entries" in info_dict
                if is_playlist:
                    is_noplaylist = False
                    if video_name:
                        filename = video_name
                    else:
                        filename = info_dict.get("title", "Сериал")
                    outtmpl_path = os.path.join(os.path.join(self.download_dir, filename), "%(playlist_index)s - %(title)s.%(ext)s")
                else:
                    is_noplaylist = True
                    if video_name:
                        filename = f"{video_name}.%(ext)s"
                    else:
                        filename = "%(title)s.%(ext)s"
                    outtmpl_path = os.path.join(self.download_dir, filename)   

                ydl_opts = {
                    "format": final_format,
                    "outtmpl": outtmpl_path,
                    "merge_output_format": "mp4",
                    "ffmpeg_location": os.getcwd(),
                    "format_sort": ["vcodec:avc", "ext:mp4", "res"],
                    "noplaylist": is_noplaylist,
                    "ignoreerrors": True,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])

                self.line_url.clear()
                self.line_set_name.clear()
                self.download_widget.hide()
                self.colections_list.show()
                self.folders_list.show()
                self.search_line.show()
                self.btn_new.show()
                self.btn_settings.show()
                self.current_dir = self.download_dir
                self.load_downloaded_videos()
                
                QMessageBox.information(self, "Найс", "Скачивание успешно завершено!")
            except Exception as error:
                QMessageBox.critical(self, "Ошибка", f"Не удалось скачать: {error}")

    def load_downloaded_videos(self):
        self.folders_list.clear()

        if self.current_dir != self.download_dir:
            back_item = QListWidgetItem("<- Вернуться назад")
            back_item.setData(Qt.ItemDataRole.UserRole, "back")
            self.folders_list.addItem(back_item)

        if os.path.exists(self.current_dir):
            for file_name in os.listdir(self.current_dir):
                full_path = os.path.join(self.current_dir, file_name)

                if os.path.isdir(full_path):
                    item = QListWidgetItem(file_name)
                    item.setData(Qt.ItemDataRole.UserRole, full_path)
                    self.folders_list.addItem(item)

                elif file_name.endswith(".mp4") or file_name.endswith(".m4a"):
                    video_title, _ = os.path.splitext(file_name)
                    item = QListWidgetItem(video_title)
                    item.setData(Qt.ItemDataRole.UserRole, full_path)
                    self.folders_list.addItem(item)

    def item_double_click(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path == "back":
            self.current_dir = self.download_dir
            self.load_downloaded_videos()
        elif path and os.path.isdir(path):
            self.current_dir = path
            self.load_downloaded_videos()
        elif path and os.path.exists(path):
            self.play_video(path)

    def show_context_menu(self, position):
        item = self.folders_list.itemAt(position)
        if item != None:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path == "back":
                return

            menu = QMenu(self)
            delete_do = menu.addAction("Удалить")
            do = menu.exec(self.folders_list.mapToGlobal(position))
            if do == delete_do:
                self.delete_item(item)

    def delete_item(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        title = item.text()

        check = QMessageBox.question(
            self, "Удаление", f"Удалить \"{title}\" с компьютера?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if check == QMessageBox.StandardButton.Yes:
            try:
                self.player.stop()
                self.player.setSource(QUrl())

                if path and os.path.exists(path):
                    for file_name in os.listdir(path):
                        file_in_dir = os.path.join(path, file_name)
                        if os.path.isfile(file_in_dir):
                            os.remove(file_in_dir)
                    os.rmdir(path)
                else:
                    os.remove(path)

                self.load_downloaded_videos()
                QMessageBox.information(self, "Успешно", "Удалено")
            except Exception as error:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить: {error}")

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
            if self.video_widget.isVisible():
                self.player.stop()
                self.video_widget.hide()
                self.download_widget.hide()

                self.colections_list.show()
                self.folders_list.show()
                self.search_line.show()
                self.btn_new.show()
                self.btn_settings.show()
            elif self.current_dir != self.download_dir:
                self.current_dir = self.download_dir
                self.load_downloaded_videos()

        if event.key() == Qt.Key.Key_Space:
            if self.video_widget.isVisible():
                if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                    self.player.pause()
                else:
                    self.player.play()

    def filter_videos(self, text):
        search_text = text.lower()
        for i in range(self.folders_list.count()):
            item = self.folders_list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == "back":
                continue
            if search_text in item.text().lower():
                item.setHidden(False)
            else:
                item.setHidden(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = Programm()
    ex.show()
    sys.exit(app.exec())