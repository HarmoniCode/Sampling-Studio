import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QFrame
)
from PyQt6.QtGui import QIcon
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
import pyqtgraph as pg

class SignalListItemWidget(QFrame):
    delete_signal = pyqtSignal(str)  

    def __init__(self, description, parent=None):
        super().__init__(parent)
        self.description = description
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout(self)
        self.label = QLabel(self.description)
        self.delete_button = QPushButton()
        self.delete_button.setFixedWidth(30)
        self.delete_button.setIcon(QIcon.fromTheme("list-remove"))  
        self.delete_button.clicked.connect(self.handle_delete)

        layout.addWidget(self.label)
        layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding))
        layout.addWidget(self.delete_button)
        layout.setContentsMargins(0, 0, 0, 0)

    def handle_delete(self):
        
        self.delete_signal.emit(self.description)


class SignalMixerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Signal Mixer")
        self.setGeometry(100, 100, 800, 600)
        
        self.signals = []  
        self.result_signals = {}  
        self.current_displayed_signal = None
        self.mixed_signal_components = {} 

        self.fs = 44100  
        
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        
        input_layout = QHBoxLayout()
        self.freq_input = QLineEdit()
        self.freq_input.setPlaceholderText("Frequency (Hz)")
        self.amp_input = QLineEdit()
        self.amp_input.setPlaceholderText("Amplitude")
        self.phase_input = QLineEdit()
        self.phase_input.setPlaceholderText("Phase (radians)")
        input_layout.addWidget(QLabel("Frequency:"))
        input_layout.addWidget(self.freq_input)
        input_layout.addWidget(QLabel("Amplitude:"))
        input_layout.addWidget(self.amp_input)
        input_layout.addWidget(QLabel("Phase:"))
        input_layout.addWidget(self.phase_input)
        layout.addLayout(input_layout)
        
        add_button = QPushButton("Add Signal")
        add_button.clicked.connect(self.add_signal)
        mix_button = QPushButton("Mix Signals")
        mix_button.clicked.connect(self.mix_signals)
        upload_button = QPushButton("Upload Signal")
        upload_button.clicked.connect(self.upload_signal)
        layout.addWidget(upload_button)
        layout.addWidget(add_button)
        layout.addWidget(mix_button)

        lists_layout=QHBoxLayout()
        
        self.signal_list = QListWidget()
        signal_list_V=QVBoxLayout()
        signal_list_V.addWidget(QLabel("Individual Signals:"))
        signal_list_V.addWidget(self.signal_list)
        lists_layout.addLayout(signal_list_V)
        
        self.result_list = QListWidget()
        result_list_V=QVBoxLayout()
        result_list_V.addWidget(QLabel("Mixed Signal Results:"))
        result_list_V.addWidget(self.result_list)
        lists_layout.addLayout(result_list_V)
        
        self.components_list = QListWidget()
        components_list_V=QVBoxLayout()
        components_list_V.addWidget(QLabel("Components of Selected Mixed Signal:"))
        components_list_V.addWidget(self.components_list)
        lists_layout.addLayout(components_list_V)

        layout.addLayout(lists_layout)  
        
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        self.result_list.itemSelectionChanged.connect(self.display_selected_signal)

        self.setLayout(layout)

    def mix_signals(self):
        
        duration = 1
        mixed_signal = np.zeros(int(self.fs * duration))
        components = []  
        
        for frequency, amplitude, phase in self.signals:
            wave = self.generate_wave(frequency, amplitude, phase, duration)
            mixed_signal += wave
            components.append(f"Freq: {frequency} Hz, Amp: {amplitude}, Phase: {phase} rad")  
        
        mixed_signal_description = f"Mixed Signal with {len(self.signals)} components"
        self.result_signals[mixed_signal_description] = mixed_signal  
        self.mixed_signal_components[mixed_signal_description] = components  

        list_item_widget = SignalListItemWidget(mixed_signal_description)
        list_item_widget.delete_signal.connect(lambda desc=mixed_signal_description: self.delete_signal(self.result_list, desc, self.result_signals))
        
        list_item = QListWidgetItem(self.result_list)
        list_item.setSizeHint(list_item_widget.sizeHint())
        self.result_list.setItemWidget(list_item, list_item_widget)

        self.plot_waveform(mixed_signal)
        
        self.signals.clear()
        self.signal_list.clear()

    def display_selected_signal(self):
        selected_items = self.result_list.selectedItems()
        if selected_items:  
            item = selected_items[0]  
            item_widget = self.result_list.itemWidget(item)
            if item_widget:
                
                mixed_signal_description = item_widget.description  
                mixed_signal = self.result_signals.get(mixed_signal_description, None)
                if mixed_signal is not None:
                    self.plot_waveform(mixed_signal, mixed_signal_description)
                    
                    self.components_list.clear()  
                    components = self.mixed_signal_components.get(mixed_signal_description, [])
                    print("Components Retrieved for Selected Signal:", components)  
                    if components:
                        self.components_list.addItems(components)  
                    else:
                        self.components_list.addItem("No components found")  

                print("Selected Signal:", mixed_signal_description)  

    def mix_signals(self):
    
        duration = 1
        mixed_signal = np.zeros(int(self.fs * duration))
        components = []  
        
        for frequency, amplitude, phase in self.signals:
            wave = self.generate_wave(frequency, amplitude, phase, duration)
            mixed_signal += wave
            components.append(f"Freq: {frequency} Hz, Amp: {amplitude}, Phase: {phase} rad")  
        
        mixed_signal_description = f"Signal{len(self.result_list) + 1}"  
        self.result_signals[mixed_signal_description] = mixed_signal  
        self.mixed_signal_components[mixed_signal_description] = components  
        
        list_item_widget = SignalListItemWidget(mixed_signal_description)
        list_item_widget.delete_signal.connect(lambda desc=mixed_signal_description: self.delete_signal(self.result_list, desc, self.result_signals))
        
        list_item = QListWidgetItem(self.result_list)
        list_item.setSizeHint(list_item_widget.sizeHint())
        self.result_list.setItemWidget(list_item, list_item_widget)
        
        self.plot_waveform(mixed_signal, mixed_signal_description)
        
        self.signals.clear()
        self.signal_list.clear()

        print("Mixed Signal Description:", mixed_signal_description)
        print("Mixed Signal Components:", components)
        print("Current Result Signals:", self.result_signals)
        print("Current Mixed Signal Components:", self.mixed_signal_components)

    def generate_wave(self, frequency, amplitude, phase, duration):
        t = np.linspace(0, duration, int(self.fs * duration), endpoint=False)
        wave = amplitude * np.sin(2 * np.pi * frequency * t + phase)
        return wave

    def add_signal(self):
        
        try:
            frequency = float(self.freq_input.text())
            amplitude = float(self.amp_input.text())
            phase = float(self.phase_input.text()) if self.phase_input.text() else 0.0
        except ValueError:
            print("Please enter valid numbers.")
            return
        
        self.signals.append((frequency, amplitude, phase))
        
        signal_description = f"Freq: {frequency} Hz, Amp: {amplitude}, Phase: {phase} rad"
        list_item_widget = SignalListItemWidget(signal_description)
        list_item_widget.delete_signal.connect(lambda desc=signal_description: self.delete_signal(self.signal_list, desc, self.signals))
        
        list_item = QListWidgetItem(self.signal_list)
        list_item.setSizeHint(list_item_widget.sizeHint())
        self.signal_list.setItemWidget(list_item, list_item_widget)

        self.freq_input.clear()
        self.amp_input.clear()
        self.phase_input.clear()

    def delete_signal(self, list_widget, description, data_structure):
        
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item_widget = list_widget.itemWidget(item)
            if item_widget and item_widget.description == description:
                list_widget.takeItem(i)  
                break
        
        if description in data_structure:
            del data_structure[description]
        
        if self.current_displayed_signal == description:
            if data_structure:  
                first_signal_description = next(iter(data_structure))
                self.plot_waveform(data_structure[first_signal_description], first_signal_description)
            else:  
                self.plot_widget.clear()
                self.current_displayed_signal = None

    def upload_signal(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, "Open Signal File", "", "Text Files (*.txt *.csv)")

        if file_path:
            try:
                
                signal_data = np.loadtxt(file_path, delimiter=',')
                
                if signal_data.shape[1] > 1:
                    signal = signal_data[:, 1]  
                else:
                    signal = signal_data[:, 0]  
                
                signal_description = f"Uploaded Signal ({file_path.split('/')[-1]})"
                list_item_widget = SignalListItemWidget(signal_description)
                list_item_widget.delete_signal.connect(lambda desc=signal_description: self.delete_signal(self.result_list, desc, self.result_signals))
                
                list_item = QListWidgetItem(self.result_list)
                list_item.setSizeHint(list_item_widget.sizeHint())
                self.result_list.setItemWidget(list_item, list_item_widget)
                
                self.result_signals[signal_description] = signal
                
                self.plot_waveform(signal, signal_description)

            except Exception as e:
                print(f"Failed to load signal: {e}")

    def plot_waveform(self, signal, description=None):
        self.plot_widget.clear()
        t = np.linspace(0, 1, len(signal))
        self.plot_widget.plot(t, signal, pen='b')  
        self.plot_widget.setTitle("Signal Waveform")
        self.plot_widget.setLabel("left", "Amplitude")
        self.plot_widget.setLabel("bottom", "Time [s]")
        
        self.current_displayed_signal = description


app = QApplication(sys.argv)
window = SignalMixerApp()
window.show()
sys.exit(app.exec())
