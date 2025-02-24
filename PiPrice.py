import sys
import requests
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication

class PiPriceWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.drag_position = None
        self.last_prices = []  # Stores prices for the last 30 minutes (60 updates)
        self.font_black = False   # Default font color: white
        self.sound_enabled = True  # Sound notifications are enabled by default
        self.do_not_disturb = False  # Do Not Disturb mode is off
        self.initUI()
        self.create_tray_icon()
        self.update_price()  # First price update

    def initUI(self):
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        self.label = QtWidgets.QLabel("Fetching Price...")
        self.label.setAlignment(QtCore.Qt.AlignCenter)

        font = QtGui.QFont("Courier New", 48, QtGui.QFont.Bold)
        self.label.setFont(font)
        self.label.setStyleSheet("color: white;")  # Default white color
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.resize(350, 150)

        # Update price every 30 seconds
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_price)
        self.timer.start(30000)

    def update_price(self):
        try:
            url = "https://api.coingecko.com/api/v3/simple/price?ids=pi-network&vs_currencies=usd"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            price = data.get("pi-network", {}).get("usd", None)
            if price is not None:
                self.label.setText(f"π ${price}")

                # Store price history (60 updates = 30 minutes)
                self.last_prices.append(price)
                if len(self.last_prices) > 60:
                    self.last_prices.pop(0)

                # Check for a 10% increase over 30 minutes
                if len(self.last_prices) >= 60:
                    old_price = self.last_prices[0]
                    if old_price > 0:  # Prevent division by zero
                        percentage_change = ((price - old_price) / old_price) * 100
                        print(f"30-min change: {percentage_change:.2f}%")
                        if percentage_change >= 10 and self.sound_enabled and not self.do_not_disturb:
                            self.play_alert_sound()
                    else:
                        print("Old price is zero; cannot compute percentage change.")
        except requests.exceptions.RequestException as e:
            print("API Error:", e)
            self.label.setText("Connection Error")
        except Exception as e:
            print("General Error:", e)
            self.label.setText("Error")

    def play_alert_sound(self):
        # System beep for alert (no external file needed)
        QApplication.beep()

    # Returns a simple black dot icon (16x16 pixels)
    def get_black_dot_icon(self):
        pixmap = QtGui.QPixmap(16, 16)
        pixmap.fill(QtCore.Qt.black)
        return QtGui.QIcon(pixmap)

    # Context menu (right-click)
    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)

        font_action = menu.addAction("Toggle Black/White Font")
        font_action.triggered.connect(self.toggle_font_color)

        sound_action = menu.addAction("Toggle Sound (On/Off)")
        if not self.sound_enabled:
            # If sound is off, display a black dot icon next to the menu item
            sound_action.setIcon(self.get_black_dot_icon())
        sound_action.triggered.connect(self.toggle_sound)

        disturb_action = menu.addAction("Do Not Disturb (1 Hour)")
        disturb_action.triggered.connect(self.enable_do_not_disturb)

        quit_action = menu.addAction("Exit")
        quit_action.triggered.connect(QtWidgets.qApp.quit)

        menu.exec_(event.globalPos())

    def toggle_font_color(self):
        self.font_black = not self.font_black
        if self.font_black:
            self.label.setStyleSheet("color: black;")
        else:
            self.label.setStyleSheet("color: white;")

    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        # Play a system beep to notify toggle (both for enabling and disabling)
        QApplication.beep()
        print("Sound:", "Enabled" if self.sound_enabled else "Disabled")

    def enable_do_not_disturb(self):
        self.do_not_disturb = True
        print("Do Not Disturb mode enabled for 1 hour")
        QtCore.QTimer.singleShot(3600000, self.disable_do_not_disturb)  # Disable after 1 hour

    def disable_do_not_disturb(self):
        self.do_not_disturb = False
        print("Do Not Disturb mode disabled")

    # Allow dragging the widget by clicking anywhere on it
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    # Create system tray icon
    def create_tray_icon(self):
        self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        self.tray_icon.setIcon(QtGui.QIcon())  # You can set an icon here if needed
        self.tray_icon.setVisible(True)
        self.tray_icon.activated.connect(self.icon_activated)

        menu = QtWidgets.QMenu()
        restore_action = menu.addAction("Show")
        restore_action.triggered.connect(self.showNormal)

        quit_action = menu.addAction("Exit")
        quit_action.triggered.connect(QtWidgets.qApp.quit)

        self.tray_icon.setContextMenu(menu)

    def icon_activated(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.DoubleClick:
            self.showNormal()

    # When attempting to close the window, minimize it to the tray instead
    def closeEvent(self, event):
        event.ignore()
        self.hide()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    widget = PiPriceWidget()
    widget.show()
    sys.exit(app.exec_())
