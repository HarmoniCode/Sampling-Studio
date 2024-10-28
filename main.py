import sys
import numpy as np
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QFrame, QSlider
)
from PyQt6.QtGui import QIcon
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
import pyqtgraph as pg
from pyqtgraph import ScatterPlotItem

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

        self.sampling_slider = QSlider(Qt.Orientation.Horizontal)
        self.sampling_slider.setRange(1, 4) 
        self.sampling_slider.setValue(1)    
        self.sampling_slider.setTickInterval(1)
        self.sampling_slider.setTickPosition(QSlider.TickPosition.TicksBelow)

        # Connect the slider to a callback function
        self.sampling_slider.valueChanged.connect(self.update_sampling_markers)

        self.reconstruct_button = QPushButton("Reconstruct Signal")
        self.reconstruct_button.clicked.connect(self.reconstruct_signal)
        layout.addWidget(self.reconstruct_button)

        layout.addWidget(self.sampling_slider)

        layout.addLayout(lists_layout)  
        
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

        self.result_list.itemSelectionChanged.connect(self.display_selected_signal)

        self.setLayout(layout)

    def reconstruct_signal(self):
        # Get the factor from the slider to determine the sampling frequency
        factor = self.sampling_slider.value()
        
        # Calculate the sampling interval based on f_max and factor
        sampling_interval = 1 / (factor * self.f_max) 
        sampling_times = np.arange(0, 2, sampling_interval)
        sampling_amplitudes = np.interp(sampling_times, self.current_signal_t, self.current_signal_data)
        
        # Perform sinc interpolation for reconstruction
        reconstructed_signal = self.sinc_interp(sampling_amplitudes, sampling_times, self.current_signal_t)
        
        # Plot both original and reconstructed signals for comparison
        self.plot_reconstructed_signal(reconstructed_signal)

    def plot_reconstructed_signal(self, reconstructed_signal):
        self.plot_widget.clear()
        
        # Plot the original signal in blue
        self.plot_widget.plot(self.current_signal_t, self.current_signal_data, pen='b', name="Original Signal")
        
        # Plot the reconstructed signal in red
        self.plot_widget.plot(self.current_signal_t, reconstructed_signal, pen='r', name="Reconstructed Signal")

        # Set plot title and labels
        self.plot_widget.setTitle("Original vs. Reconstructed Signal")
        self.plot_widget.setLabel("left", "Amplitude")
        self.plot_widget.setLabel("bottom", "Time [s]")

    def sinc_interp(self,x, s, t):
        """Sinc interpolation of sampled points.
        Parameters:
        x : np.ndarray : sampled signal values
        s : np.ndarray : sampled time points
        t : np.ndarray : desired time points for reconstruction
        """
        T = s[1] - s[0]  # Sampling interval
        sinc_matrix = np.tile(t, (len(s), 1)) - np.tile(s[:, np.newaxis], (1, len(t)))
        return np.dot(x, np.sinc(sinc_matrix / T))

    def plot_waveform_with_markers(self, signal, description=None):
        self.plot_widget.clear()
        duration = 1  # seconds
        t = np.linspace(0, duration, len(signal))

        # Plot the waveform without sampling markers
        self.plot_widget.plot(t, signal, pen='b')
        
        # FFT to find dominant (maximum) frequency
        fft_result = np.fft.fft(signal)
        freqs = np.fft.fftfreq(len(signal), 1 / self.fs)
        magnitude = np.abs(fft_result)

        # Get max frequency
        max_freq_idx = np.argmax(magnitude)
        self.f_max = abs(freqs[max_freq_idx])  # Save f_max as an attribute for later use
        
        # Set plot title and labels
        self.plot_widget.setTitle("Signal Waveform with Adjustable Sampling Markers")
        self.plot_widget.setLabel("left", "Amplitude")
        self.plot_widget.setLabel("bottom", "Time [s]")
        
        # Save signal details for further updates
        self.current_displayed_signal = description
        self.current_signal_t = t
        self.current_signal_data = signal

        # Initial marker plot at the default factor (1 * f_max)
        self.plot_sampling_markers(factor=1)

    def plot_sampling_markers(self, factor):
        sampling_interval = 1 / (factor * self.f_max)
        sampling_times = np.arange(0, 1, sampling_interval)
        sampling_amplitudes = np.interp(sampling_times, self.current_signal_t, self.current_signal_data)
        
        # Create ScatterPlotItem only once and update data later
        if not hasattr(self, 'marker_item'):
            self.marker_item = ScatterPlotItem(symbol='o', pen=None, brush='r', size=6)
            self.plot_widget.addItem(self.marker_item)
        
        # Update marker data instead of re-plotting
        spots = [{'pos': (time, amp)} for time, amp in zip(sampling_times, sampling_amplitudes)]
        self.marker_item.setData(spots)

    def update_sampling_markers(self):
        factor = self.sampling_slider.value()  # Get the current value of the slider (1 to 4)
        self.plot_sampling_markers(factor)

    def display_selected_signal(self):
        selected_items = self.result_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            item_widget = self.result_list.itemWidget(item)
            if item_widget:
                # Get the description of the selected signal
                mixed_signal_description = item_widget.description
                mixed_signal = self.result_signals.get(mixed_signal_description, None)
                if mixed_signal is not None:
                    # Plot waveform without markers initially
                    self.plot_waveform_with_markers(mixed_signal, mixed_signal_description)

                    # Get the sampling factor from the slider (1 to 4)
                    factor = self.sampling_slider.value()
                    
                    # Plot sampling markers with the current factor
                    self.plot_sampling_markers(factor)

                    # Update the component list for the selected signal
                    self.components_list.clear()
                    components = self.mixed_signal_components.get(mixed_signal_description, [])
                    if components:
                        self.components_list.addItems(components)
                    else:
                        self.components_list.addItem("No components found")
                        
            print("Selected Signal:", mixed_signal_description)
            print("Components:", components)

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

        components = self.mixed_signal_components.get(description, [])
        if components:
            self.components_list.clear()
        else:
            self.components_list.addItem("No components found")

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
