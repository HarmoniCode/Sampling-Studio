import sys
import numpy as np
from PyQt6.QtGui import QIcon
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
import pyqtgraph as pg
from scipy.interpolate import interp1d
from pyqtgraph import ScatterPlotItem
from pyqtgraph import PlotWidget

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QFrame, QSlider
)


class SignalListItemWidget(QFrame):
    delete_signal = pyqtSignal(str)

    def __init__(self, description, parent=None):
        super().__init__(parent)
        self.description = description
        self.initUI()

    def initUI(self):
        
        layout = QHBoxLayout(self)
        self.label = QLabel(self.description)
        self.label.setObjectName("signal_label")
        self.delete_button = QPushButton()
        self.delete_button.setObjectName("delete_button")
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
        self.noisy_signals = {}
        self.fs = 44100 

        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        with open("index.qss", "r") as f:
             app.setStyleSheet(f.read())

        mixer_frame = QFrame()
        mixer_frame.setFixedWidth(600)
        layout.addWidget(mixer_frame)
        mixer_layout=QVBoxLayout()
        mixer_layout.setSpacing(15)
        mixer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        mixer_frame.setLayout(mixer_layout)
        
        input_box = QHBoxLayout()
        input_box_frame = QFrame()
        input_box_frame.setObjectName("input_box_frame")
        input_box_frame.setMaximumHeight(270)

        # input_box_frame.setStyleSheet('''background-color:white;''')
        input_box_frame.setLayout(input_box)

        input_frame = QFrame()
        input_layout = QVBoxLayout()
        input_frame.setLayout(input_layout)
        input_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        input_layout.setSpacing(15)
        self.freq_input = QLineEdit()
        self.freq_input.setMinimumHeight(30)


        self.freq_input.setPlaceholderText("Frequency (Hz)")
        self.amp_input = QLineEdit()
        self.amp_input.setMinimumHeight(30)
        self.amp_input.setPlaceholderText("Amplitude")
        self.phase_input = QLineEdit()
        self.phase_input.setMinimumHeight(30)
        self.phase_input.setPlaceholderText("Phase (radians)")
        
        freq_label = QLabel("Frequency:")
        freq_label.setObjectName("input_label")
        input_layout.addWidget(freq_label)
        input_layout.addWidget(self.freq_input)
        
        amp_label = QLabel("Amplitude:")
        amp_label.setObjectName("input_label")
        input_layout.addWidget(amp_label)
        input_layout.addWidget(self.amp_input)
        
        phase_label = QLabel("Phase:")
        phase_label.setObjectName("input_label")
        input_layout.addWidget(phase_label)
        input_layout.addWidget(self.phase_input)
        
        input_box.addWidget(input_frame)


        add_mix_control_layout = QHBoxLayout()

        add_button = QPushButton("Add Signal")
        add_button.setObjectName("add_button")
        add_button.setMinimumHeight(35)
        add_button.clicked.connect(self.add_signal)
        mix_button = QPushButton("Mix Signals")
        mix_button.setObjectName("mix_button")
        mix_button.setMinimumHeight(35)
        mix_button.clicked.connect(self.mix_signals)
        upload_button = QPushButton("Upload Signal")
        upload_button.clicked.connect(self.upload_signal)
        add_mix_control_layout.addWidget(add_button)
        add_mix_control_layout.addWidget(mix_button)

        mixer_layout.addWidget(upload_button)
        mixer_layout.addWidget(input_box_frame)
        mixer_layout.addLayout(add_mix_control_layout)

        self.signal_list = QListWidget()
        self.signal_list.setObjectName("signal_list")

        signal_list_V=QVBoxLayout()
        signal_list_V.setAlignment(Qt.AlignmentFlag.AlignTop)

        Individual_label = QLabel("Individual Signals:")
        Individual_label.setObjectName("bold_label")
        
        signal_list_V.addWidget(Individual_label)
        signal_list_V.addWidget(self.signal_list)
        signal_list_V.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding))
        
        input_box.addLayout(signal_list_V)

        result_components_layout = QHBoxLayout()
        result_components_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.result_list = QListWidget()
        result_list_V=QVBoxLayout()
        result_list_V.setAlignment(Qt.AlignmentFlag.AlignTop)
        mixed_label = QLabel("Mixed Signals:")
        result_list_V.addWidget(mixed_label)
        result_list_V.addWidget(self.result_list)
        result_components_layout.addLayout(result_list_V)

        self.components_list = QListWidget()
        components_list_V=QVBoxLayout()
        components_list_V.setAlignment(Qt.AlignmentFlag.AlignTop)

        component_label = QLabel("Components of Selected Mixed Signal:")
        components_list_V.addWidget(component_label)
        components_list_V.addWidget(self.components_list)
        result_components_layout.addLayout(components_list_V)

        mixer_layout.addLayout(result_components_layout)


        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItems(["Whittaker-Shannon", "Linear", "Cubic"])  # Add options
        
        self.comboBox.currentIndexChanged.connect(self.selected_reconstruction)  # Connect event
        
        mixer_layout.addWidget (self.comboBox)

        plot_reconstructed_layout = QVBoxLayout()

        self.plot_markers_button = QPushButton("Plot Sampling Markers")
        self.plot_markers_button.clicked.connect(self.plot_sampling_markers)
        plot_reconstructed_layout.addWidget(self.plot_markers_button)

        self.reconstruct_button = QPushButton("Reconstruct Signal")
        self.reconstruct_button.clicked.connect(self.reconstruct_signal)
        plot_reconstructed_layout.addWidget(self.reconstruct_button)

        # Create a layout for the sliders
        slider_layout = QVBoxLayout()

        self.sampling_slider = QSlider(Qt.Orientation.Horizontal)
        self.sampling_slider.setRange(1, 4)
        self.sampling_slider.setValue(1)
        self.sampling_slider.setTickInterval(1)
        self.sampling_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        slider_layout.addWidget(self.sampling_slider)

        snr_layout = QHBoxLayout()
        self.snr_value = QLabel("SNR Level : 0")
        snr_layout.addWidget(self.snr_value)

        self.snr_slider = QSlider(Qt.Orientation.Horizontal)
        self.snr_slider.setRange(0, 100)
        self.snr_slider.setValue(100)
        self.snr_slider.setTickInterval(5)
        self.snr_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        snr_layout.addWidget(self.snr_slider)
        slider_layout.addLayout(snr_layout)
        self.snr_slider.valueChanged.connect(self.update_snr_value)    
        self.snr_slider.valueChanged.connect(self.add_noise)  

        # Create a horizontal layout to combine buttons and sliders
        compine_layout = QHBoxLayout()
        compine_layout.addLayout(slider_layout)
        compine_layout.addLayout(plot_reconstructed_layout)

        # Add the combined layout to the main layout
        mixer_layout.addLayout(compine_layout)

        # Add the main plot widget for the original and reconstructed signals
        grid_frame = QFrame()
        grid_frame.setObjectName("grid_frame")
        grid_layout = QVBoxLayout()
        grid_frame.setLayout(grid_layout)

        self.plot_widget = PlotWidget()
        grid_layout.addWidget(self.plot_widget)

        self.plot_widget_1 = PlotWidget()
        grid_layout.addWidget(self.plot_widget_1)

        # Add a new plot widget for the difference signal
        self.difference_plot_widget = PlotWidget()
        grid_layout.addWidget(self.difference_plot_widget)

        # Frequency Domain Plot Widget
        self.freq_plot_widget = PlotWidget()
        grid_layout.addWidget(self.freq_plot_widget)

        layout.addWidget(grid_frame)

        self.result_list.itemSelectionChanged.connect(self.display_selected_signal)

        mixer_layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding))

        self.setLayout(layout)

    def selected_reconstruction(self,x,s,t):
        method = self.comboBox.currentText()
        if method == "Whittaker-Shannon":
            reconstructed_signal = self.whittaker_shannon_reconstruction(x, s, t)
        elif method == "Linear":
            reconstructed_signal = self.linear_interpolation(x, s, t)
        elif method == "Cubic":
            reconstructed_signal = self.cubic_interpolation(x, s, t)
        return reconstructed_signal

    def reconstruct_signal(self):
        # Get the factor from the slider to determine the sampling frequency
        factor = self.sampling_slider.value()

        # Calculate the sampling interval based on f_max and factor
        sampling_interval = 1 / (factor * self.f_max)
        sampling_times = np.arange(0, 5, sampling_interval)
        sampling_amplitudes = np.interp(sampling_times, self.current_signal_t, self.current_signal_data)

        #خد يا لؤي هي دي
        reconstructed_signal = self.selected_reconstruction(sampling_amplitudes, sampling_times, self.current_signal_t)

        # Plot original, reconstructed, and frequency domain signals for comparison
        self.plot_reconstructed_signal(reconstructed_signal)

    def plot_reconstructed_signal(self, reconstructed_signal):

        # Clear the plot widgets
        self.plot_widget_1.clear()
        self.difference_plot_widget.clear()
        self.freq_plot_widget.clear()

        # Plot the reconstructed signal
        self.plot_widget_1.plot(self.current_signal_t, reconstructed_signal, pen='r', name="Reconstructed Signal")

        # Calculate the difference signal
        difference_signal = self.current_signal_data - reconstructed_signal

        # Plot the difference signal in the new plot widget
        self.difference_plot_widget.plot(self.current_signal_t, difference_signal, pen='g', name="Difference Signal")

        # Perform FFT on the reconstructed signal
        N = len(reconstructed_signal)
        fft_values = np.fft.fft(reconstructed_signal)
        fft_magnitude = np.abs(fft_values[:N//2]) * 2 / N # Normalize magnitude
        freq_data = np.fft.fftfreq(N, d=(self.current_signal_t[1] - self.current_signal_t[0]))[:N // 2] # self.current_signal_t[] is the array of  x values (time), N is number of points, d is the sample spacing
        # many bins showing near-zero magnitudes for other frequencies, because a signal length is of means N frequency bins, even if the signal has only one dominant frequency.

        # Plot the frequency domain of the reconstructed signal
        self.freq_plot_widget.plot(freq_data, fft_magnitude, pen='y', name="Frequency Signal")

        # self.freq_plot_line = self.freq_plot_widget.plot(freq_data, fft_magnitude, pen="r")


        self.plot_widget_1.setTitle("Reconstructed Signal")
        self.plot_widget_1.setLabel("left", "Amplitude")
        self.plot_widget_1.setLabel("bottom", "Time [s]")

        self.difference_plot_widget.setTitle("Difference Signal")
        self.difference_plot_widget.setLabel("left", "Amplitude")
        self.difference_plot_widget.setLabel("bottom", "Time [s]")

        self.freq_plot_widget.setTitle("Frequency Domain")
        self.freq_plot_widget.setLabel("left", "Magnitude")
        self.freq_plot_widget.setLabel("bottom", "Frequency [Hz]")

    def whittaker_shannon_reconstruction(self, x, s, t):
        T = s[1] - s[0]
        sinc_matrix = np.tile(t, (len(s), 1)) - np.tile(s[:, np.newaxis], (1, len(t)))
        return np.sum(x[:, np.newaxis] * np.sinc(sinc_matrix / T), axis=0)

    def linear_interpolation(self, x, s, t):
        linear_interpolator = interp1d(s, x, kind='linear')
        return linear_interpolator(t)

    def cubic_interpolation(self, x, s, t):
        cubic_interpolator = interp1d(s, x, kind='cubic')
        return cubic_interpolator(t)

    def plot_waveform_with_markers(self, signal, description=None):
        self.plot_widget.clear()
        duration = 5  # seconds
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
        print(f'max_freq_idx {self.f_max}')

        # Set plot title and labels
        self.plot_widget.setTitle("Signal Waveform with Adjustable Sampling Markers")
        self.plot_widget.setLabel("left", "Amplitude")
        self.plot_widget.setLabel("bottom", "Time [s]")

        # Save signal details for further updates
        self.current_displayed_signal = description
        self.current_signal_t = t
        self.current_signal_data = signal

    def plot_sampling_markers(self):
        factor = self.sampling_slider.value()

        # Calculate sampling interval based on f_max and factor
        sampling_interval = 1 / (factor * self.f_max)
        sampling_times = np.arange(0, 5, sampling_interval)
        sampling_amplitudes = np.interp(sampling_times, self.current_signal_t, self.current_signal_data)

        # If no marker list exists for this signal, initialize it
        if not hasattr(self, 'marker_items'):
            self.marker_items = {}

        # Generate a unique key for the current signal
        signal_key = self.current_displayed_signal

        # Clear existing markers for the current signal if they exist
        if signal_key in self.marker_items:
            self.plot_widget.removeItem(self.marker_items[signal_key])

        # Create a new ScatterPlotItem for the current signal markers and add to dictionary
        marker_item = ScatterPlotItem(symbol='o', pen=None, brush='r', size=6)
        self.marker_items[signal_key] = marker_item
        self.plot_widget.addItem(marker_item)

        # Set new marker positions
        spots = [{'pos': (time, amp)} for time, amp in zip(sampling_times, sampling_amplitudes)]
        marker_item.setData(spots)

    # def update_sampling_markers(self):
    #     factor = self.sampling_slider.value()
    #     self.plot_sampling_markers(factor)

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

                    # Set factor based on current slider position
                    # factor = self.sampling_slider.value()

                    # Plot sampling markers with the current factor
                    # self.plot_sampling_markers(factor)

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

        # print("Mixed Signal Description:", mixed_signal_description)
        # print("Mixed Signal Components:", components)
        # print("Current Result Signals:", self.result_signals)
        # print("Current Mixed Signal Components:", self.mixed_signal_components)

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
                self.plot_widget_1.clear()
                self.difference_plot_widget.clear()
                self.freq_plot_widget.clear()
                self.current_displayed_signal = None
        if self.f_max:
            self.f_max=None

        components = self.mixed_signal_components.get(description, [])
        if components:
            self.components_list.clear()


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
        t = np.linspace(0, 5, len(signal))
        self.plot_widget.plot(t, signal, pen='b')
        self.plot_widget.setTitle("Signal Waveform")
        self.plot_widget.setLabel("left", "Amplitude")
        self.plot_widget.setLabel("bottom", "Time [s]")

        self.current_displayed_signal = description

########################################################
    def add_noise(self):
        snr_value = self.snr_slider.value()
        selected_items = self.result_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            item_widget = self.result_list.itemWidget(item)
            if item_widget:
                mixed_signal_description = item_widget.description
                mixed_signal = self.result_signals.get(mixed_signal_description, None)


                signal = mixed_signal
                signal_description = mixed_signal_description
                if snr_value:
                    signal_power_dB = 10*np.log10(np.mean(np.square(signal)))
                    noise_power = signal_power_dB / (10**(snr_value/10))
                    noise = noise_power * np.random.normal(size=len(signal))
                    noisy_signal = signal + noise
                else:
                    noisy_signal = signal
                self.noisy_signals[signal_description] = noisy_signal
                self.plot_waveform_with_markers(noisy_signal, signal_description)


    def update_snr_value(self,value):
        self.snr_value.setText("SNR Level : " + str(value))

#####################################################################
app = QApplication(sys.argv)
window = SignalMixerApp()
window.show()
sys.exit(app.exec())
