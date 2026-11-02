import sys
import os
from PyQt6 import uic
import sqlite3
from download_video import downloading
from init_db_collections import init_db
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QInputDialog, QMessageBox, QListWidgetItem, QMenu
from PyQt6.QtCore import QUrl, Qt, QRect
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import yt_dlp


os.environ["QT_MULTIMEDIA_PREFERRED_PLUGINS"] = "ffmpeg"
init_db()


class MDPayer(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("maket.ui", self)

        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.player.setVideoOutput(self.video_widget)
        self.video_widget.hide()
        self.download_widget.hide()
        self.widget_settings.hide()
        self.search_line.textChanged.connect(self.filter_videos)

        self.btn_new.clicked.connect(self.new_video_parameters)
        self.btn_new_video.clicked.connect(self.new_video)
        self.btn_new_collection.clicked.connect(self.create_new_collection)
        self.btn_settings.clicked.connect(self.open_settings)

        self.colections_list.itemClicked.connect(self.collections_double_click)
        self.folders_list.itemDoubleClicked.connect(self.video_double_click)
        
        self.folders_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folders_list.customContextMenuRequested.connect(self.show_context_menu)

        self.colections_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.colections_list.customContextMenuRequested.connect(self.show_collection_context_menu)

        self.btn_new.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_settings.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.colections_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.folders_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        self.download_dir = os.path.join(os.getcwd(), "downloads")
        self.current_dir = self.download_dir
        
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)

        self.app_color = "Тёмная"
        self.download_dir = os.path.join(os.getcwd(), "downloads")

        if os.path.exists("settings.txt"):
            try:
                with open("settings.txt", "r", encoding="utf-8") as f:
                    lines = f.read().striplines()
                    self.app_color = lines[0]
                    self.download_dir = lines[1]
            except Exception:
                pass

        self.selected_collection = None
        self.menu_bar_create()
        self.load_downloaded_videos()
        self.load_collections_from_db()

        self.setStyleSheet(self.get_color(self.app_color))

    def resizeEvent(self, _):
        width = self.width()
        height = self.height()

        self.colections_list.setGeometry(10, 50, 260, height - 140)
        self.folders_list.setGeometry(290, 55, width - 300, height - 80)
        self.btn_settings.setGeometry(10, height - 90, 40, 40)
        self.btn_stats.setGeometry(55, height - 90, 40, 40)
        self.btn_new_collection.setGeometry(30, height - 125, 220, 22)
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

        self.widget_settings.setGeometry(0, 0, width, height)

    def create_new_collection(self):
        name, ok = QInputDialog.getText(self, "Новая коллекция", "Введите название коллекции:")
        if ok and name:
            try:
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO collections_list (name) VALUES (?)", (name,))
                conn.commit()
                conn.close()
                
                self.load_collections_from_db()
            except Exception as error:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать коллекцию: {error}")

    def load_collections_from_db(self):
        self.colections_list.clear()
        self.list_set_colections.clear()
        all_item = QListWidgetItem("Показать всё")
        all_item.setData(Qt.ItemDataRole.UserRole, "all")
        self.colections_list.addItem(all_item)
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM collections_list")
        rows = cursor.fetchall()

        for i in rows:
            coll_name = i[0]
            self.colections_list.addItem(coll_name)
            self.list_set_colections.addItem(coll_name)

        conn.close()

    def collections_double_click(self, item):
        if item.text() == "Показать всё":
            self.selected_collection = None
        else:
            self.selected_collection = item.text()

        self.current_dir = self.download_dir
        self.load_downloaded_videos()

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
        refresh_action.triggered.connect(self.load_collections_from_db)
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
        self.btn_new_collection.hide()
        self.btn_stats.hide()

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

                downloading(url, ydl_opts)

                self.line_url.clear()
                self.line_set_name.clear()
                self.download_widget.hide()
                self.colections_list.show()
                self.folders_list.show()
                self.search_line.show()
                self.btn_new.show()
                self.btn_new_collection.show()
                self.btn_settings.show()
                self.btn_stats.show()
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

        allowed_paths = []
        if self.selected_collection:
            try:
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()
                cursor.execute( "SELECT file_path FROM video_collections WHERE collection_name = ?", (self.selected_collection,))
                for i in cursor.fetchall():
                    allowed_paths.append(os.path.abspath(i[0]))
                conn.close()
            except Exception:
                pass

        if os.path.exists(self.current_dir):
            for file_name in os.listdir(self.current_dir):
                full_path = os.path.abspath(os.path.join(self.current_dir, file_name))

                if self.selected_collection and (full_path not in allowed_paths):
                    continue
                if os.path.isdir(full_path):
                    item = QListWidgetItem(file_name)
                    item.setData(Qt.ItemDataRole.UserRole, full_path)
                    self.folders_list.addItem(item)
                elif file_name.endswith(".mp4") or file_name.endswith(".m4a"):
                    video_title, _ = os.path.splitext(file_name)
                    item = QListWidgetItem(video_title)
                    item.setData(Qt.ItemDataRole.UserRole, full_path)
                    self.folders_list.addItem(item)

    def video_double_click(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        if path == "back":
            self.current_dir = self.download_dir
            self.load_downloaded_videos()
        elif path and os.path.isdir(path):
            self.current_dir = path
            self.load_downloaded_videos()
        elif path and os.path.exists(path):
            self.play_video(path)

    def show_collection_context_menu(self, position):
        item = self.colections_list.itemAt(position)
        if item is not None:
            if item.data(Qt.ItemDataRole.UserRole) == "all":
                return

            menu = QMenu(self)
            delete_action = menu.addAction("Удалить")

            action = menu.exec(self.colections_list.mapToGlobal(position))
            if action == delete_action:
                self.delete_collection(item)

    def show_context_menu(self, position):
        item = self.folders_list.itemAt(position)
        if item != None:
            path = item.data(Qt.ItemDataRole.UserRole)
            if path == "back":
                return

            menu = QMenu(self)
            delete_do = menu.addAction("Удалить")
            collection_menu = menu.addMenu("добавить в коллекцию")

            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            rows = cursor.execute("SELECT name FROM collections_list").fetchall()
            conn.close()

            for i in rows:
                coll_name = i[0]
                action = collection_menu.addAction(coll_name)
                action.setData(coll_name) 

            if not collection_menu.actions():
                no_col_action = collection_menu.addAction("Нет созданных коллекций")
                no_col_action.setEnabled(False)

            do = menu.exec(self.folders_list.mapToGlobal(position))
            if do == delete_do:
                self.delete_item(item)
            elif do in collection_menu.actions():
                coll_name = do.data()
                self.add_to_collection_from_menu(path, coll_name)
                self.load_collections_from_db()

    def add_to_collection_from_menu(self, path, name):
        try:
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO video_collections (file_path, collection_name) VALUES (?, ?)", (path, name))
            conn.commit()
            conn.close()    
            self.load_downloaded_videos()
            QMessageBox.information(self, "Ура", f"Видео успешно добавлено в коллекцию '{name}'")
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", f"Не удалось привязать к коллекции: {error}")

    def delete_item(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        title = item.text()

        check = QMessageBox.question(
            self, "Удаление", f"Удалить '{title}' с компьютера?",
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

    def delete_collection(self, item):
        name = item.text()

        check = QMessageBox.question(
            self, "Удаление коллекции", f"Вы уверены, что хотите удалить коллекцию '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if check == QMessageBox.StandardButton.Yes:
            try:
                conn = sqlite3.connect("database.db")
                cursor = conn.cursor()

                cursor.execute("DELETE FROM collections_list WHERE name = ?", (name,))
                cursor.execute("DELETE FROM video_collections WHERE collection_name = ?", (name,))
                
                conn.commit()
                conn.close()

                if self.selected_collection == name:
                    self.selected_collection = None

                self.load_collections_from_db()
                self.load_downloaded_videos()
                
                QMessageBox.information(self, "Успешно", f"Коллекция '{name}' удалена.")
            except Exception as error:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить коллекцию: {error}")

    def play_video(self, file_path):
        self.colections_list.hide()
        self.btn_settings.hide()
        self.search_line.hide()
        self.btn_new.hide()
        self.folders_list.hide()
        self.video_widget.show()
        self.btn_new_collection.hide()
        self.btn_stats.hide()

        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.audio_output.setVolume(0.67)
        self.player.play()
        self.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            if self.video_widget.isVisible() or self.download_widget.isVisible() or self.widget_settings.isVisible():
                self.player.stop()
                self.video_widget.hide()
                self.download_widget.hide()
                if self.widget_settings.isVisible():
                    self.save_settings()
                self.widget_settings.hide()

                self.colections_list.show()
                self.folders_list.show()
                self.search_line.show()
                self.btn_new.show()
                self.btn_settings.show()
                self.btn_new_collection.show()
                self.btn_stats.show()
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

    def open_settings(self):
        self.widget_settings.show()
        self.download_widget.hide()
        self.colections_list.hide()
        self.btn_settings.hide()
        self.search_line.hide()
        self.btn_new.hide()
        self.folders_list.hide()
        self.video_widget.hide()
        self.btn_new_collection.hide()
        self.btn_stats.hide()

        self.combo_box_color.setCurrentText(self.app_color)
        self.line_path.setText(self.download_dir)

    def get_color(self, color_name):
        colors = {
            "Тёмная": """
                QMainWindow { background-color: #1e1e24; }
                QWidget { color: #ffffff; }
                QListWidget { background-color: #2a2a32; color: #ffffff; border: 1px solid #3f3f46; border-radius: 6px; padding: 5px; }
                QListWidget::item:selected { background-color: #007acc; color: white; }
                QLineEdit { background-color: #2a2a32; color: #ffffff; border: 1px solid #3f3f46; border-radius: 4px; padding: 5px; }
                QPushButton { background-color: #007acc; color: white; border: none; border-radius: 4px; padding: 6px; }
                QPushButton:hover { background-color: #0098ff; }
                QMenuBar { background-color: #1e1e24; color: white; }
                QMenuBar::item:selected { background-color: #2a2a32; }
                QMenu { background-color: #2a2a32; color: white; border: 1px solid #3f3f46; }
                QMenu::item:selected { background-color: #007acc; }
                QLabel { color: #ffffff; }
                QCheckBox { color: #ffffff; spacing: 5px; }
                QCheckBox::indicator { width: 16px; height: 16px; }
                QComboBox { background-color: #2a2a32; color: #ffffff; border: 1px solid #3f3f46; border-radius: 4px; padding: 5px; }
                QComboBox QAbstractItemView { background-color: #2a2a32; color: #ffffff; selection-background-color: #007acc; }
            """,
            "Светлая": """
                QMainWindow { background-color: #f3f3f3; }
                QWidget { color: #000000; }
                QListWidget { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; border-radius: 6px; padding: 5px; }
                QListWidget::item:selected { background-color: #005fb8; color: white; }
                QLineEdit { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; border-radius: 4px; padding: 5px; }
                QPushButton { background-color: #005fb8; color: white; border: none; border-radius: 4px; padding: 6px; }
                QPushButton:hover { background-color: #0078d4; }
                QMenuBar { background-color: #f3f3f3; color: black; }
                QMenuBar::item:selected { background-color: #e5e5e5; }
                QMenu { background-color: #ffffff; color: black; border: 1px solid #cccccc; }
                QMenu::item:selected { background-color: #005fb8; color: white; }
                QLabel { color: #000000; }
                QCheckBox { color: #000000; spacing: 5px; }
                QCheckBox::indicator { width: 16px; height: 16px; }
                QComboBox { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; border-radius: 4px; padding: 5px; }
                QComboBox QAbstractItemView { background-color: #ffffff; color: #000000; selection-background-color: #005fb8; }
            """,
            "Неон": """
                QMainWindow { background-color: #0d0e15; }
                QWidget { color: #00ffcc; }
                QListWidget { background-color: #161925; color: #00ffcc; border: 1px solid #ff007f; border-radius: 6px; padding: 5px; }
                QListWidget::item:selected { background-color: #ff007f; color: black; font-weight: bold; }
                QLineEdit { background-color: #161925; color: #00ffcc; border: 1px solid #ff007f; border-radius: 4px; padding: 5px; }
                QPushButton { background-color: #ff007f; color: white; border: none; border-radius: 4px; padding: 6px; font-weight: bold; }
                QPushButton:hover { background-color: #ff3399; }
                QMenuBar { background-color: #0d0e15; color: #00ffcc; }
                QMenuBar::item:selected { background-color: #161925; }
                QMenu { background-color: #161925; color: #00ffcc; border: 1px solid #ff007f; }
                QMenu::item:selected { background-color: #ff007f; color: black; }
                QLabel { color: #00ffcc; }
                QCheckBox { color: #00ffcc; spacing: 5px; }
                QCheckBox::indicator { width: 16px; height: 16px; }
                QComboBox { background-color: #161925; color: #00ffcc; border: 1px solid #ff007f; border-radius: 4px; padding: 5px; }
                QComboBox QAbstractItemView { background-color: #161925; color: #00ffcc; selection-background-color: #ff007f; }
            """,
            "Зелёная": """
                QMainWindow { background-color: #243421; }
                QWidget { color: #f0f5f0; }
                QListWidget { background-color: #2e402a; color: #f0f5f0; border: 1px solid #3c5437; border-radius: 6px; padding: 5px; }
                QListWidget::item:selected { background-color: #528b4b; color: white; }
                QLineEdit { background-color: #2e402a; color: #ffffff; border: 1px solid #3c5437; border-radius: 4px; padding: 5px; }
                QPushButton { background-color: #528b4b; color: white; border: none; border-radius: 4px; padding: 6px; }
                QPushButton:hover { background-color: #64a15c; }
                QMenuBar { background-color: #243421; color: white; }
                QMenuBar::item:selected { background-color: #2e402a; }
                QMenu { background-color: #2e402a; color: white; border: 1px solid #3c5437; }
                QMenu::item:selected { background-color: #528b4b; }
                QLabel { color: #f0f5f0; }
                QCheckBox { color: #f0f5f0; spacing: 5px; }
                QCheckBox::indicator { width: 16px; height: 16px; }
                QComboBox { background-color: #2e402a; color: #ffffff; border: 1px solid #3c5437; border-radius: 4px; padding: 5px; }
                QComboBox QAbstractItemView { background-color: #2e402a; color: #ffffff; selection-background-color: #528b4b; }
            """
        }
        return colors.get(color_name)

    def save_settings(self):
        self.app_color = self.combo_box_color.currentText()
        self.download_dir = self.line_path.text()

        try:
            with open("settings.txt", "w", encoding="utf-8") as f:
                f.write(f"{self.app_color}\n")
                f.write(f"{self.download_dir}")

            self.current_dir = self.download_dir
            self.setStyleSheet(self.get_color(self.app_color))
        except Exception as error:
            QMessageBox.critical(self, "Ошибка", error)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MDPayer()
    ex.show()
    sys.exit(app.exec())