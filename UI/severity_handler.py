import requests
import base64
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QPushButton, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QMessageBox, QTableWidgetItem

api_base = "https://api-classify.smartfarm.id"

def init_severity_page(ui):
    ui.submitDateTime.clicked.connect(lambda: handle_submit_date(ui))
    ui.submitDateTime_2.clicked.connect(lambda: handle_submit_datetime_2(ui))
    ui.dateAndTimeList.itemClicked.connect(lambda item: handle_date_clicked(ui, item.text()))

    # Klik di luar kotak waktu menyembunyikan kontainernya
    ui.centralwidget.mousePressEvent = lambda event: hide_time_box(ui)

    handle_submit_date(ui, initial=True)
    handle_time_clicked(ui, None, None, initial=True)

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
        timestamps = data.get("matched_directories", [])
        date_set = sorted(set([ts.split('_')[0] for ts in timestamps]))

        ui.dateAndTimeList.clear()
        for date in date_set:
            ui.dateAndTimeList.addItem(date)

        ui._date_to_times = {}
        for ts in timestamps:
            date, time = ts.split('_')
            if date not in ui._date_to_times:
                ui._date_to_times[date] = []
            ui._date_to_times[date].append(time.replace('-', ':'))
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
    json_data = {} if initial else {"tanggal": date, "waktu": time}

    try:
        res = requests.post(f"{api_base}/get-data", json=json_data)
        res.raise_for_status()
        items = res.json()

        ui.severityTable.setColumnCount(8)
        ui.severityTable.setHorizontalHeaderLabels([
            "Image", "Image Preview", "Tanggal", "Waktu",
            "Pred 1", "Pred 2", "Pred 3", "Delete"
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

            ui.severityTable.setItem(row_idx, 2, QTableWidgetItem(item["tanggal"]))
            ui.severityTable.setItem(row_idx, 3, QTableWidgetItem(item["waktu"]))
            ui.severityTable.setItem(row_idx, 4, QTableWidgetItem(item["pred_class_1"]))
            ui.severityTable.setItem(row_idx, 5, QTableWidgetItem(item["pred_class_2"]))
            ui.severityTable.setItem(row_idx, 6, QTableWidgetItem(item["pred_class_3"]))

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(lambda checked, i=item: handle_delete(ui, i))
            ui.severityTable.setCellWidget(row_idx, 7, delete_btn)
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

def handle_submit_datetime_2(ui):
    dt = ui.dateTimeEdit.dateTime().toString("yyyy-MM-dd hh:mm:ss")
    tanggal, waktu = dt.split(' ')
    try:
        res = requests.post(f"{api_base}/get-full-image", json={"tanggal": tanggal, "waktu": waktu})
        res.raise_for_status()
        img_data = res.json().get("image_data", "").split(",")[-1]
        image = QtGui.QImage.fromData(base64.b64decode(img_data))
        tray_size = ui.trayCamera.size()
        pixmap = QtGui.QPixmap.fromImage(image).scaled(
            tray_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
        )
        ui.trayCamera.setPixmap(pixmap)
        ui.trayCamera.setAlignment(QtCore.Qt.AlignCenter)
        ui.trayCamera.setStyleSheet("background-color: #F0F0F0;")
    except Exception as e:
        show_message(f"Gagal mengambil gambar tray: {e}")

def show_message(msg):
    QMessageBox.information(None, "Info", msg)
