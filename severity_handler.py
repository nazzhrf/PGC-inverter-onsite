import requests
import base64
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QMessageBox, QTableWidgetItem, QDialog, QGridLayout, QSpinBox
from PyQt5.QtCore import QDateTime, QTime, QEvent
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)



api_base = "https://api-classify.smartfarm.id"

# Tombol level dan warnanya
LEVEL_BUTTONS = {
    "level0": "0",
    "level1": "1",
    "level3": "3",
    "level5": "5",
    "level7": "7",
    "level9": "9"
}

# Tombol aktif (state di luar UI)
_active_level = {"button": None, "value": None}

def reset_level_buttons(ui):
    for btn_name in LEVEL_BUTTONS:
        btn = getattr(ui, btn_name)
        btn.setStyleSheet("background-color: white")

def on_level_clicked(ui, btn_name):
    reset_level_buttons(ui)
    btn = getattr(ui, btn_name)
    btn.setStyleSheet("background-color: lightblue")
    _active_level["button"] = btn_name
    _active_level["value"] = LEVEL_BUTTONS[btn_name]

    # Ulangi permintaan berdasarkan waktu & tanggal terakhir
    if _active_level.get("last_date") and _active_level.get("last_time"):
        handle_time_clicked(ui, _active_level["last_date"], _active_level["last_time"])

def on_refresh_clicked(ui):
    reset_level_buttons(ui)
    _active_level["button"] = None
    _active_level["value"] = None
    QMessageBox.information(ui, "Info", "Tabel severity kembali ke kondisi semula")

    if _active_level.get("last_date") and _active_level.get("last_time"):
        handle_time_clicked(ui, _active_level["last_date"], _active_level["last_time"])

def setup_level_buttons(ui):
    for btn_name in LEVEL_BUTTONS:
        getattr(ui, btn_name).clicked.connect(lambda _, b=btn_name: on_level_clicked(ui, b))
    ui.refresh.clicked.connect(lambda: on_refresh_clicked(ui))

class TrayPopup(QtWidgets.QDialog):
    def __init__(self, tray_image, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Tray View - Fullscreen")
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: white;")
        self.setFixedSize(920, 540)

        layout = QVBoxLayout()

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: white;")

        self.label = ZoomableImageLabel()
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.set_scroll_area(scroll_area)

        if tray_image is None or tray_image.isNull():
            tray_image = QtGui.QImage(321, 166, QtGui.QImage.Format_RGB32)
            tray_image.fill(QtGui.QColor("gray"))

        self.label.setImage(tray_image)
        scroll_area.setWidget(self.label)

        # Buat tombol setelah label siap
        reset_btn = QPushButton("Reset Zoom")
        reset_btn.setFixedWidth(120)
        reset_btn.clicked.connect(self.label.reset_zoom)

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.close)

        # Layout tombol
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(reset_btn)
        btn_layout.addWidget(close_btn)
        btn_layout.setAlignment(QtCore.Qt.AlignRight)

        # Tambahkan ke layout utama
        layout.addWidget(scroll_area)
        layout.addLayout(btn_layout)
        self.setLayout(layout)


class ClickableImageLabel(QtWidgets.QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_image = None
        self.magnifier = QLabel(self)
        self.magnifier.setFixedSize(120, 120)
        self.magnifier.setStyleSheet("border: 1px solid black; background: white;")
        self.magnifier.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.magnifier.setVisible(False)

        # Circle mask
        mask = QtGui.QRegion(self.magnifier.rect(), QtGui.QRegion.Ellipse)
        self.magnifier.setMask(mask)

    def setImage(self, image):
        self.original_image = image

        # If not yet shown, fallback to fixed size
        size = self.size()
        if size.width() < 50 or size.height() < 50:
            size = QtCore.QSize(880, 460)  # fallback for fullscreen

        pixmap = QtGui.QPixmap.fromImage(image).scaled(
            size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self.setPixmap(pixmap)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setStyleSheet("background-color: #F0F0F0;")

    def mousePressEvent(self, event):
        self.update_magnifier(event.pos())
        self.magnifier.setVisible(True)

    def mouseMoveEvent(self, event):
        if self.magnifier.isVisible():
            self.update_magnifier(event.pos())

    def mouseReleaseEvent(self, event):
        self.magnifier.setVisible(False)

    def update_magnifier(self, pos):
        if self.original_image is None:
            return

        label_w = self.width()
        label_h = self.height()
        img_w = self.original_image.width()
        img_h = self.original_image.height()

        aspect_label = label_w / label_h
        aspect_image = img_w / img_h

        if aspect_image > aspect_label:
            scaled_w = label_w
            scaled_h = int(img_h * label_w / img_w)
            offset_x = 0
            offset_y = (label_h - scaled_h) // 2
        else:
            scaled_h = label_h
            scaled_w = int(img_w * label_h / img_h)
            offset_y = 0
            offset_x = (label_w - scaled_w) // 2

        x = pos.x() - offset_x
        y = pos.y() - offset_y
        if x < 0 or y < 0 or x >= scaled_w or y >= scaled_h:
            self.magnifier.setVisible(False)
            return

        real_x = int(x * img_w / scaled_w)
        real_y = int(y * img_h / scaled_h)

        zoom_size = 160
        half = zoom_size // 2
        crop_x = max(0, real_x - half)
        crop_y = max(0, real_y - half)
        crop_w = min(zoom_size, img_w - crop_x)
        crop_h = min(zoom_size, img_h - crop_y)

        cropped = self.original_image.copy(crop_x, crop_y, crop_w, crop_h)
        zoom_pixmap = QtGui.QPixmap.fromImage(cropped).scaled(
            120, 120, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        self.magnifier.setPixmap(zoom_pixmap)
        self.magnifier.move(pos.x() - 60, pos.y() - 60)

def init_severity_page(ui):
    ui.submitDateTime.clicked.connect(lambda: handle_submit_date(ui))
    ui.dateAndTimeList.itemClicked.connect(lambda item: handle_date_clicked(ui, item.text()))
    ui.centralwidget.mousePressEvent = lambda event: hide_time_box(ui)
    ui.trayCameraFS = ui.findChild(QtWidgets.QPushButton, "trayCameraFS")

    def open_tray_popup():
        print("[DEBUG] Fullscreen tray button clicked")
        if hasattr(ui.trayCamera, "original_image"):
            if ui.trayCamera.original_image and not ui.trayCamera.original_image.isNull():
                print("[DEBUG] original_image is available, opening popup")
                TrayPopup(ui.trayCamera.original_image).exec_()
            else:
                print("[DEBUG] original_image is None or invalid")
                show_message("Tray image not loaded yet.")
        else:
            print("[DEBUG] trayCamera has no original_image attribute")
            show_message("Tray image not loaded yet.")

    if ui.trayCameraFS:
        ui.trayCameraFS.clicked.connect(open_tray_popup)
    else:
        print("[WARNING] trayCameraFS button not found.")

    if not hasattr(ui, "trayCamera") or ui.trayCamera is None:
        raise RuntimeError("trayCamera not initialized in the UI.")

    old_tray = ui.trayCamera
    parent = old_tray.parent()
    if parent is None:
        raise RuntimeError("trayCamera has no parent widget.")

    tray_label = ClickableImageLabel(parent=parent)
    tray_label.setObjectName("trayCamera")
    tray_label.setGeometry(old_tray.geometry())
    tray_label.setSizePolicy(old_tray.sizePolicy())
    tray_label.setAlignment(QtCore.Qt.AlignCenter)
    tray_label.setStyleSheet(old_tray.styleSheet())

    old_tray.hide()
    tray_label.show()

    ui.trayCamera = tray_label

    handle_submit_date(ui, initial=True)
    setup_level_buttons(ui)


def handle_submit_date(ui, initial=False):
    json_data = {}

    if not initial:
        ym = ui.yearMonthLine.text().strip()
        week = ui.yearMonthLine_2.text().strip()
        ymd = ui.yearMonthLine_3.text().strip()

        filled_ymd = bool(ymd)
        filled_ym = bool(ym)
        filled_week = bool(week)

        if filled_ymd and not filled_ym and not filled_week:
            if QtCore.QDate.fromString(ymd, "yyyy/MM/dd").isValid():
                json_data = {"tanggal": ymd.replace('/', '-')}
            else:
                show_message("Format tanggal yyyy/MM/dd salah")
                return
        elif filled_ym and not filled_ymd:
            ym_parts = ym.split('/')
            if len(ym_parts) == 2:
                json_data = {"tahun": ym_parts[0], "bulan": str(int(ym_parts[1]))}
                if filled_week:
                    if week in ['1', '2', '3', '4']:
                        json_data["minggu"] = week
                    else:
                        show_message("Minggu harus antara 1 sampai 4")
                        return
            else:
                show_message("Gunakan format yyyy/MM untuk tahun dan bulan")
                return
        else:
            show_message("Gunakan salah satu kombinasi: (1) tahun+bulan, (2) tahun+bulan+minggu, (3) tanggal")
            return

    try:
        res = requests.post(f"{api_base}/filter-directories", json=json_data)
        res.raise_for_status()
        data = res.json()

        print("[DEBUG] Raw response JSON:", data)
        timestamps = data.get("matched_directories", [])
        print("[DEBUG] matched_directories:", timestamps)

        # timestamps = data.get("matched_directories", [])
        date_set = sorted(set([ts.split('_')[0] for ts in timestamps]))

        ui.dateAndTimeList.clear()
        for date in date_set:
            ui.dateAndTimeList.addItem(date)

        ui._date_to_times = {}
        for ts in timestamps:
            if "_" not in ts:
                print("[WARNING] Unexpected timestamp format:", ts)
            
            date, time = ts.split('_')
            if date not in ui._date_to_times:
                ui._date_to_times[date] = []
            ui._date_to_times[date].append(time.replace('-', ':'))

        print("[DEBUG] _date_to_times:", ui._date_to_times)

        # ✅ Pindahkan fallback di sini
        if initial:
            if ui._date_to_times:
                first_date = next(iter(ui._date_to_times))
                if ui._date_to_times[first_date]:
                    first_time = ui._date_to_times[first_date][0]
                    handle_time_clicked(ui, first_date, first_time)
            else:
                print("[INFO] matched_directories kosong, fallback ke handle_time_clicked dengan json_data = {}")
                handle_time_clicked(ui, date="", time="", initial=True)
    except Exception as e:
        show_message(f"Gagal mengambil data: {e}")

def handle_date_clicked(ui, date):
    if not hasattr(ui, '_time_button_layout'):
        ui._time_button_container = QWidget()
        ui._time_button_layout = QVBoxLayout()
        ui._time_button_container.setLayout(ui._time_button_layout)
        ui._time_button_container.setStyleSheet("background-color: white; border: 1px solid gray;")
        ui._time_button_container.setGeometry(QtCore.QRect(
            ui.dateAndTimeList.geometry().right() + 10,
            ui.dateAndTimeList.geometry().top(),
            160, 200
        ))
        ui._time_button_container.setParent(ui.centralwidget)

    layout = ui._time_button_layout
    for i in reversed(range(layout.count())):
        layout.itemAt(i).widget().setParent(None)

    for time in ui._date_to_times.get(date, []):
        btn = QPushButton(time)
        btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)
        btn.clicked.connect(lambda checked, d=date, t=time: handle_time_clicked(ui, d, t))
        layout.addWidget(btn)

    ui._time_button_container.show()

def hide_time_box(ui):
    if hasattr(ui, '_time_button_container'):
        ui._time_button_container.hide()


def handle_time_clicked(ui, date, time, initial=False):
    _active_level["last_date"] = date
    _active_level["last_time"] = time

    json_data = {} if initial else {"tanggal": date, "waktu": time}

    if _active_level.get("value") is not None:
        json_data["pred_class_1"] = _active_level["value"]

    print("[DEBUG] json_data sent to /get-data:", json_data)

    try:
        res = requests.post(f"{api_base}/get-data", json=json_data)
        res.raise_for_status()
        items = res.json()

        if not items:
            print("[INFO] Response kosong dari /get-data")
            show_message("Tidak ada data severity yang tersedia.")
            return

        ui.severityTable.setColumnCount(8)
        ui.severityTable.setHorizontalHeaderLabels([
            "Image", "Image Preview", "Pred 1", "Pred 2",
            "Pred 3", "Tanggal", "Waktu", "Action"
        ])
        ui.severityTable.setRowCount(0)

        for row_idx, item in enumerate(items):
            ui.severityTable.insertRow(row_idx)
            ui.severityTable.setItem(row_idx, 0, QTableWidgetItem(item["image"]))

            img_data = item["image_data"].split(",")[-1]
            image = QtGui.QImage.fromData(base64.b64decode(img_data))
            pixmap = QtGui.QPixmap.fromImage(image).scaled(100, 100, QtCore.Qt.KeepAspectRatio)
            label = QLabel()
            label.setPixmap(pixmap)
            ui.severityTable.setCellWidget(row_idx, 1, label)

            ui.severityTable.setItem(row_idx, 2, QTableWidgetItem(item["pred_class_1"]))
            ui.severityTable.setItem(row_idx, 3, QTableWidgetItem(item["pred_class_2"]))
            ui.severityTable.setItem(row_idx, 4, QTableWidgetItem(item["pred_class_3"]))
            ui.severityTable.setItem(row_idx, 5, QTableWidgetItem(item["tanggal"]))
            ui.severityTable.setItem(row_idx, 6, QTableWidgetItem(item["waktu"]))

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, i=item: handle_delete(ui, i))
            ui.severityTable.setCellWidget(row_idx, 7, delete_btn)

        load_tray_image(ui, date, time)
        print(f"load tray (date) : {date}")
        print(f"load tray (time) : {time}")

    except Exception as e:
        show_message(f"Gagal mengambil data severity: {e}")

def handle_delete(ui, item):
    confirm = QMessageBox.question(ui.severityTable, "Konfirmasi Hapus", f"Hapus {item['image']}?", QMessageBox.Yes | QMessageBox.No)
    if confirm == QMessageBox.Yes:
        try:
            res = requests.post(f"{api_base}/delete", json={
                "tanggal": item["tanggal"],
                "waktu": item["waktu"],
                "image": item["image"]
            })
            res.raise_for_status()
            show_message("Berhasil dihapus")
            handle_time_clicked(ui, item["tanggal"], item["waktu"])
        except Exception as e:
            show_message(f"Gagal menghapus data: {e}")

# def handle_submit_datetime_2(ui):
#     dt = ui.dateTimeEdit.dateTime().toString("yyyy-MM-dd hh:mm:ss")
#     tanggal, waktu = dt.split(' ')
    
#     try:
#         res = requests.post(f"{api_base}/get-full-image", json={"tanggal": tanggal, "waktu": waktu})
#         res.raise_for_status()
#         img_data = res.json().get("image_data", "").split(",")[-1]
#         image = QtGui.QImage.fromData(base64.b64decode(img_data))
#         tray_size = ui.trayCamera.size()
#         pixmap = QtGui.QPixmap.fromImage(image).scaled(
#             tray_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
#         )
#         ui.trayCamera.setPixmap(pixmap)
#         ui.trayCamera.setAlignment(QtCore.Qt.AlignCenter)
#         ui.trayCamera.setStyleSheet("background-color: #F0F0F0;")
#     except Exception as e:
#         show_message(f"Gagal mengambil gambar tray: {e}")

def show_message(msg):
    QMessageBox.information(None, "Info", msg)

from PyQt5.QtGui import QImage, QPixmap
import base64

def load_tray_image(ui, tanggal, waktu):
    try:
        json_payload = {} if not tanggal or not waktu else {
            "tanggal": tanggal,
            "waktu": waktu
        }

        print("[DEBUG] Payload sent to /get-full-image:", json_payload)

        res = requests.post("https://api-classify.smartfarm.id/get-full-image", json=json_payload)
        res.raise_for_status()
        img_data = res.json().get("image_data", "").split(",")[-1]
        image = QtGui.QImage.fromData(base64.b64decode(img_data))

        # Gunakan resolusi proporsional 16:9 dengan height = 181
        target_height = 175
        target_width = int((16 / 9) * target_height)  # = 322

        print(f"[DEBUG] Scaling to: {target_width} x {target_height}")

        tray_pixmap = QtGui.QPixmap.fromImage(image).scaled(
            target_width,
            target_height,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )

        ui.trayCamera.setPixmap(tray_pixmap)
        ui.trayCamera.setFixedSize(target_width, target_height)  # Force UI size
        ui.trayCamera.setAlignment(QtCore.Qt.AlignCenter)
        ui.trayCamera.setScaledContents(False)  # Biarkan Qt yang urus rasio
        ui.trayCamera.setStyleSheet("background-color: #F0F0F0;")

        if isinstance(ui.trayCamera, ClickableImageLabel):
            ui.trayCamera.original_image = image

    except Exception as e:
        show_message(f"Gagal mengambil gambar tray: {e}")

class ZoomableImageLabel(ClickableImageLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 1.0
        self.zoomed = False
        self.setCursor(QtCore.Qt.OpenHandCursor)

        self._drag_active = False
        self._drag_start_pos = None
        self._scroll_area = None

    def set_scroll_area(self, area):
        self._scroll_area = area

    def mouseDoubleClickEvent(self, event):
        if self.original_image is None:
            return

        self.zoomed = not self.zoomed
        self.zoom_factor = 2.0 if self.zoomed else 1.0

        target_size = self.size() * self.zoom_factor
        pixmap = QtGui.QPixmap.fromImage(self.original_image).scaled(
            target_size,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.setPixmap(pixmap)
        self.resize(pixmap.size())  # supaya scroll area tahu ukuran baru
        self.setCursor(QtCore.Qt.OpenHandCursor)

        super().mouseDoubleClickEvent(event)  # ✅ biar magnifier tetap jalan

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_active = True
            self._drag_start_pos = event.globalPos()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
        super().mousePressEvent(event)  # ✅ biar event lain tetap berjalan

    def mouseMoveEvent(self, event):
        if self._drag_active and self._scroll_area:
            delta = event.globalPos() - self._drag_start_pos
            self._drag_start_pos = event.globalPos()
            h_scroll = self._scroll_area.horizontalScrollBar()
            v_scroll = self._scroll_area.verticalScrollBar()
            h_scroll.setValue(h_scroll.value() - delta.x())
            v_scroll.setValue(v_scroll.value() - delta.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_active = False
            self.setCursor(QtCore.Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)

    def reset_zoom(self):
        if self.original_image is None:
            return

        self.zoomed = False
        self.zoom_factor = 1.0

        # Ambil ukuran area tampilan sekarang
        if self._scroll_area:
            target_size = self._scroll_area.viewport().size()
        else:
            target_size = self.size()  # fallback

        # Buat pixmap baru dari gambar original
        pixmap = QtGui.QPixmap.fromImage(self.original_image).scaled(
            target_size,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )

        self.setPixmap(pixmap)
        self.resize(pixmap.size())  # resize label-nya agar scroll area bisa menyesuaikan





