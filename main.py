import sys
import numpy as np
from PyQt6.QtGui import QIcon
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt, pyqtSignal
from scipy.interpolate import interp1d
from pyqtgraph import ScatterPlotItem
from pyqtgraph import PlotWidget
from scipy.interpolate import CubicSpline
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QFrame,
    QSlider,
    QRadioButton,
)
from PyQt6 import QtCore


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
        self.delete_button.setFixedHeight(28)
        self.delete_button.setIcon(QIcon("./Icons/minus.png"))
        self.delete_button.clicked.connect(self.handle_delete)

        self.setStyleSheet(
            "QFrame {border: 1px solid #ccc; border-radius: 5px; padding: 5px;}"
        )

        layout.addWidget(self.label)
        layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        layout.addWidget(self.delete_button)
        layout.setContentsMargins(0, 0, 0, 0)

    def handle_delete(self):
        self.delete_signal.emit(self.description)


class SignalMixerApp(QWidget):
    def __init__(self):
        super().__init__()
        self.isNoNoise = False
        self.signal = None
        self.setObjectName("mainWindow")
        self.setWindowTitle("Signal Mixer")
        self.setGeometry(100, 100, 1500, 600)

        self.signals = []
        self.result_signals = {}
        self.current_displayed_signal = None
        self.mixed_signal_components = {}
        self.noisy_signals = {}
        self.fs = 44100
        self.updated_fs = 44100  # to be updated, and used in freq graph
        self.f_max = None
        self.current_mode = "dark"
        self.duration = 1

        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        mixer_frame = QFrame()
        mixer_frame.setObjectName("mixer_frame")
        mixer_frame.setFixedWidth(650)
        layout.addWidget(mixer_frame)
        mixer_layout = QVBoxLayout()
        mixer_layout.setSpacing(15)
        mixer_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        mixer_frame.setLayout(mixer_layout)

        input_box = QHBoxLayout()
        input_box_frame = QFrame()
        input_box_frame.setObjectName("input_box_frame")
        input_box_frame.setMaximumHeight(270)

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
        self.mix_button = QPushButton("Mix Signals")
        self.mix_button.setObjectName("mix_button")
        self.mix_button.setMinimumHeight(35)
        self.mix_button.clicked.connect(self.mix_signals)

        upload_layout = QHBoxLayout()
        upload_button = QPushButton("Upload Signal")
        upload_button.setIcon(QIcon("./Icons/upload.png"))
        upload_button.setFixedWidth(150)
        upload_button.clicked.connect(self.upload_signal)
        self.mode_button = QPushButton()
        self.mode_button.setIcon(QIcon("./Icons/dark-mode.png"))
        self.mode_button.setIconSize(QtCore.QSize(25, 25))
        self.mode_button.setFixedWidth(50)
        self.mode_button.clicked.connect(self.switch_mode)

        add_mix_control_layout.addWidget(add_button)
        add_mix_control_layout.addWidget(self.mix_button)

        upload_layout.addWidget(upload_button)
        upload_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                1000,
                0,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )
        upload_layout.addWidget(self.mode_button)

        mixer_layout.addLayout(upload_layout)
        mixer_layout.addWidget(input_box_frame)
        mixer_layout.addLayout(add_mix_control_layout)

        self.signal_list = QListWidget()
        self.signal_list.itemSelectionChanged.connect(self.display_selected_signal)
        self.signal_list.setObjectName("signal_list")

        signal_list_V = QVBoxLayout()
        signal_list_V.setAlignment(Qt.AlignmentFlag.AlignTop)

        Individual_label = QLabel("Individual Signals:")
        Individual_label.setObjectName("bold_label")

        signal_list_V.addWidget(Individual_label)
        signal_list_V.addWidget(self.signal_list)
        signal_list_V.addSpacerItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )

        input_box.addLayout(signal_list_V)

        result_components_layout = QHBoxLayout()
        result_components_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        self.result_list = QListWidget()
        result_list_V = QVBoxLayout()
        result_list_V.setAlignment(Qt.AlignmentFlag.AlignTop)
        mixed_label = QLabel("Mixed Signals:")
        result_list_V.addWidget(mixed_label)
        result_list_V.addWidget(self.result_list)
        result_components_layout.addLayout(result_list_V)

        self.components_list = QListWidget()
        self.components_list.setObjectName("components_list")
        components_list_V = QVBoxLayout()
        components_list_V.setAlignment(Qt.AlignmentFlag.AlignTop)

        component_label = QLabel("Signal Components :")
        components_list_V.addWidget(component_label)
        components_list_V.addWidget(self.components_list)
        result_components_layout.addLayout(components_list_V)

        mixer_layout.addLayout(result_components_layout)

        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItems(["Whittaker-Shannon", "Linear", "Cubic"])

        self.comboBox.currentIndexChanged.connect(self.reconstruct_signal)

        mixer_layout.addWidget(self.comboBox)

        # plot_reconstructed_layout = QVBoxLayout()

        slider_layout = QVBoxLayout()

        self.radio1 = QRadioButton("Normalized Frequency")
        self.radio2 = QRadioButton("Actual Frequency")
        self.radio1.setChecked(True)
        self.radio1.toggled.connect(self.activate_slider)

        sampling_layout = QHBoxLayout()
        sampling_label_start = QLabel("Normalized Frequency: Fmax")
        sampling_label_end = QLabel(" 4 Fmax")
        self.sampling_slider = QSlider(Qt.Orientation.Horizontal)

        self.sampling_slider.setRange(1, 4)
        self.sampling_slider.setValue(1)
        self.sampling_slider.setTickInterval(1)
        self.sampling_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sampling_slider.valueChanged.connect(self.plot_sampling_markers)
        self.sampling_slider.valueChanged.connect(self.reconstruct_signal)
        sampling_layout.addWidget(sampling_label_start)
        sampling_layout.addWidget(self.sampling_slider)
        sampling_layout.addWidget(sampling_label_end)
        slider_layout.addWidget(self.radio1)
        slider_layout.addLayout(sampling_layout)
        slider_layout.addWidget(self.radio2)

        sampling_layout_2 = QHBoxLayout()
        sampling_label_start_2 = QLabel("Sampling Frequency: 1")
        self.sampling_label_end_2 = QLabel()
        self.sampling_slider_actual = QSlider(Qt.Orientation.Horizontal)
        if self.f_max is None:
            self.sampling_slider_actual.setRange(1, 400)
        else:
            self.sampling_slider_actual.setRange(1, int(8 * self.f_max / 1.05))

        self.sampling_slider_actual.setValue(1)
        self.sampling_slider_actual.setEnabled(False)
        self.sampling_slider_actual.setTickInterval(1)
        self.sampling_slider_actual.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sampling_slider_actual.valueChanged.connect(self.plot_sampling_markers)
        self.sampling_slider_actual.valueChanged.connect(self.reconstruct_signal)
        sampling_layout_2.addWidget(sampling_label_start_2)
        sampling_layout_2.addWidget(self.sampling_slider_actual)
        sampling_layout_2.addWidget(self.sampling_label_end_2)
        slider_layout.addLayout(sampling_layout_2)

        snr_layout = QHBoxLayout()
        self.snr_value = QLabel("SNR Level : 0")
        snr_layout.addWidget(self.snr_value)

        self.snr_slider = QSlider(Qt.Orientation.Horizontal)
        self.snr_slider.setRange(1, 100)
        self.snr_slider.setValue(100)
        self.snr_slider.setTickInterval(5)
        self.snr_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        snr_layout.addWidget(self.snr_slider)
        slider_layout.addLayout(snr_layout)
        self.snr_slider.valueChanged.connect(self.update_snr_value)
        self.snr_slider.valueChanged.connect(self.add_noise)
        self.snr_slider.valueChanged.connect(self.plot_sampling_markers)
        self.snr_slider.valueChanged.connect(self.reconstruct_signal)

        mixer_layout.addLayout(slider_layout)

        grid_frame = QFrame()
        grid_frame.setObjectName("grid_frame")
        grid_layout = QVBoxLayout()
        grid_frame.setLayout(grid_layout)

        self.main_plot_widget = PlotWidget()
        self.main_plot_widget.setTitle("Signal Waveform")
        self.main_plot_widget.setLabel("left", "Amplitude")
        self.main_plot_widget.setLabel("bottom", "Time [s]")
        grid_layout.addWidget(self.main_plot_widget)

        self.reconstruct_plot_widget = PlotWidget()
        self.reconstruct_plot_widget.setTitle("Reconstructed Signal")
        self.reconstruct_plot_widget.setLabel("left", "Amplitude")
        self.reconstruct_plot_widget.setLabel("bottom", "Time [s]")

        grid_layout.addWidget(self.reconstruct_plot_widget)

        self.difference_plot_widget = PlotWidget()
        self.difference_plot_widget.setTitle("Difference Signal")
        self.difference_plot_widget.setLabel("left", "Amplitude")
        self.difference_plot_widget.setLabel("bottom", "Time [s]")

        grid_layout.addWidget(self.difference_plot_widget)

        self.freq_plot_widget = PlotWidget()
        self.freq_plot_widget.setTitle("Frequency Domain")
        self.freq_plot_widget.setLabel("left", "Magnitude")
        self.freq_plot_widget.setLabel("bottom", "Frequency [Hz]")
        grid_layout.addWidget(self.freq_plot_widget)

        layout.addWidget(grid_frame)

        self.result_list.itemSelectionChanged.connect(self.display_selected_result)

        mixer_layout.addSpacerItem(
            QtWidgets.QSpacerItem(
                0,
                0,
                QtWidgets.QSizePolicy.Policy.Minimum,
                QtWidgets.QSizePolicy.Policy.Expanding,
            )
        )


        defult_signals ={
            "signal 1" :{
                "frequencies":[10, 15, 20],
                "amplitudes":[5, 5, 10],
                "phases":[0, 0, 1.57]
            },
            "signal 2" :{
                "frequencies":[4, 8],
                "amplitudes":[5, 5],
                "phases":[0, 0]
            }
        }


        for signal in defult_signals.values():
            self.add_default_signal(signal["frequencies"], signal["amplitudes"], signal["phases"])

        self.setLayout(layout)
        self.switch_mode()

    def add_default_signal(self, frequencies, amplitudes, phases):
        '''
        Add a default signal to the signal list and plot the waveform.
        Args:
            frequencies (list): List of signal frequencies.
            amplitudes (list): List of signal amplitudes.
            phases (list): List of signal phases.
        '''
        duration = self.duration

        for frequency, amplitude, phase in zip(frequencies, amplitudes, phases):
            wave = self.generate_wave(frequency, amplitude, phase, duration)

            signal_description = f"Freq: {frequency} Hz, Amp: {amplitude}, Phase: {phase} rad"
            self.signals.append((frequency, amplitude, phase))
            self.plot_waveform(wave, signal_description)

            list_item_widget = SignalListItemWidget(signal_description)
            list_item_widget.delete_signal.connect(
                lambda desc=signal_description: self.delete_signal(
                    self.signal_list, desc, self.signals
                )
            )
            list_item = QListWidgetItem(self.signal_list)
            list_item.setSizeHint(list_item_widget.sizeHint())
            self.signal_list.setItemWidget(list_item, list_item_widget)

        if self.signal_list.count() > 0:
            self.signal_list.setCurrentRow(0)

        self.mix_button.click()

    def switch_mode(self):
        if self.current_mode == "light":
            with open("./Styles/darkMode.qss", "r") as f:
                app.setStyleSheet(f.read())
            self.current_mode = "dark"
            self.mode_button.setIcon(QIcon("./Icons/light-mode.png"))
        else:
            with open("./Styles/lightMode.qss", "r") as f:
                app.setStyleSheet(f.read())
            self.mode_button.setIcon(QIcon("./Icons/dark-mode.png"))
            self.current_mode = "light"

    def activate_slider(self):
        if self.radio1.isChecked():
            self.sampling_slider.setEnabled(True)
            self.sampling_slider_actual.setEnabled(False)
            self.plot_sampling_markers()
        else:
            if self.f_max is None:
                self.sampling_slider_actual.setRange(1, 400)
            else:
                self.sampling_slider_actual.setRange(1, int(8 * self.f_max / 1.05))

            self.sampling_slider_actual.setEnabled(True)
            self.sampling_slider.setEnabled(False)
            self.plot_sampling_markers()

    def selected_reconstruction(self, amplitude, sampling_time, current_time):
        method = self.comboBox.currentText()
        if method == "Whittaker-Shannon":
            reconstructed_signal = self.whittaker_shannon_reconstruction(amplitude, sampling_time, current_time)
        elif method == "Linear":
            reconstructed_signal = self.linear_interpolation(amplitude, sampling_time, current_time)
        elif method == "Cubic":
            reconstructed_signal = self.cubic_interpolation(amplitude, sampling_time, current_time)
        return reconstructed_signal

    def get_sampling_markers(self):
        sampling_interval = None
        if self.radio1.isChecked():
            factor = self.sampling_slider.value()
            sampling_interval = 1 / (factor * self.f_max)
            print("1", sampling_interval)
        else:
            if self.f_max is None:
                self.sampling_slider_actual.setRange(1, 400)
            else:
                self.sampling_slider_actual.setRange(1, int(8 * self.f_max / 1.05))
            factor = self.sampling_slider_actual.value()
            self.sampling_label_end_2.setText(f"{self.sampling_slider_actual.value()}")
            sampling_interval = 1 / factor
            print("2", sampling_interval)

        sampling_times = np.arange(0, self.duration, sampling_interval)
        sampling_amplitudes = np.interp(
            sampling_times, self.current_signal_t, self.current_signal_data
        )
        print("fmax", self.f_max)
        return sampling_amplitudes, sampling_times

    def reconstruct_signal(self):
        sampling_amplitudes, sampling_times = self.get_sampling_markers()

        method = self.comboBox.currentText()
        if method == "Whittaker-Shannon":
            reconstructed_signal = self.whittaker_shannon_reconstruction(
                sampling_amplitudes, sampling_times, self.current_signal_t
            )
        elif method == "Linear":
            reconstructed_signal = self.linear_interpolation(
                sampling_amplitudes, sampling_times, self.current_signal_t
            )
        elif method == "Cubic":
            reconstructed_signal = self.cubic_interpolation(
                sampling_amplitudes, sampling_times, self.current_signal_t
            )

        if self.f_max is None:
            raise AttributeError("Please select a signal first")

        self.plot_reconstructed_signal(reconstructed_signal)

    def plot_reconstructed_signal(self, reconstructed_signal):

        self.reconstruct_plot_widget.clear()
        self.difference_plot_widget.clear()
        self.freq_plot_widget.clear()

        # self.main_plot_widget.setYLink(self.reconstruct_plot_widget)
        self.reconstruct_plot_widget.setYLink(self.difference_plot_widget)
        self.reconstruct_plot_widget.plot(
            self.current_signal_t,
            reconstructed_signal,
            pen="r",
            name="Reconstructed Signal",
        )
        #Dr Tamer
        if self.signal is not None and self.signal.any():
            difference_signal = self.signal - reconstructed_signal
        else:
            difference_signal = self.current_signal_data - reconstructed_signal

        self.difference_plot_widget.plot(
            self.current_signal_t, difference_signal, pen="g", name="Difference Signal"
        )
        if self.radio1.isChecked():
            self.updated_fs = self.sampling_slider.value() * self.f_max

        elif self.radio2.isChecked():
            if self.f_max is None:
                self.sampling_slider_actual.setRange(1, 400)
            else:
                self.sampling_slider_actual.setRange(1, int(8 * self.f_max / 1.05))

            self.updated_fs = (self.sampling_slider_actual.value())

        N = len(reconstructed_signal)
        fft_values = np.fft.fft(reconstructed_signal)
        fft_magnitude = np.abs(fft_values[:N // 2]) * 2 / N
        freq_data = np.fft.fftfreq(N, d=(self.current_signal_t[1] - self.current_signal_t[0]))[:N // 2]
        symmetric_freq_data = np.concatenate((-freq_data[::-1], freq_data))
        symmetric_fft_magnitude = np.concatenate((fft_magnitude[::-1], fft_magnitude))

        mask = (symmetric_freq_data >= -1 * self.f_max) & (symmetric_freq_data <= 1 * self.f_max)
        final_freq_data = symmetric_freq_data[mask]
        final_fft_magnitude = symmetric_fft_magnitude[mask]

        self.freq_plot_widget.plot(final_freq_data, final_fft_magnitude, pen='y', name="Periodic Frequency Signal")
        self.freq_plot_widget.plot(final_freq_data + 1 * self.updated_fs, final_fft_magnitude, pen='r',
                                   name="Periodic Frequency Signal")
        self.freq_plot_widget.plot(final_freq_data - 1 * self.updated_fs, final_fft_magnitude, pen='r',
                                   name="Periodic Frequency Signal")
        max_freq_magnitude = max(final_fft_magnitude)
        self.freq_plot_widget.setYRange(0, max_freq_magnitude)

        self.reconstruct_plot_widget.setTitle("Reconstructed Signal")
        self.reconstruct_plot_widget.setLabel("left", "Amplitude")
        self.reconstruct_plot_widget.setLabel("bottom", "Time [s]")

        self.difference_plot_widget.setTitle("Difference Signal")
        self.difference_plot_widget.setLabel("left", "Amplitude")
        self.difference_plot_widget.setLabel("bottom", "Time [s]")

        self.freq_plot_widget.setTitle("Frequency Domain")
        self.freq_plot_widget.setLabel("left", "Magnitude")
        self.freq_plot_widget.setLabel("bottom", "Frequency [Hz]")

    def whittaker_shannon_reconstruction(self, amplitude, sampling_time, current_time):
        T = sampling_time[1] - sampling_time[0]
        sinc_matrix = np.tile(current_time, (len(sampling_time), 1)) - np.tile(sampling_time[:, np.newaxis],
                                                                               (1, len(current_time)))
        return np.sum(amplitude[:, np.newaxis] * np.sinc((sinc_matrix / T)), axis=0)

    def linear_interpolation(self, amplitude, sampling_time, current_time):
        linear_interpolator = interp1d(sampling_time, amplitude, kind='linear', fill_value="extrapolate")
        return linear_interpolator(current_time)

    def cubic_interpolation(self, amplitude, sampling_time, current_time):
        cubic_interpolator = CubicSpline(sampling_time, amplitude)
        return cubic_interpolator(current_time)

    def plot_waveform_with_markers(self, signal, description=None):
        self.main_plot_widget.clear()
        # duration = 1
        current_time = np.linspace(0, self.duration, len(signal))

        self.main_plot_widget.plot(current_time, signal, pen='b')

        self.main_plot_widget.setTitle("Signal Waveform")
        self.main_plot_widget.setLabel("left", "Amplitude")
        self.main_plot_widget.setLabel("bottom", "Time [s]")

        self.current_displayed_signal = description
        self.current_signal_t = current_time
        self.current_signal_data = signal

    def plot_sampling_markers(self):

        sampling_amplitudes, sampling_times = self.get_sampling_markers()

        if not hasattr(self, "marker_items"):
            self.marker_items = {}

        signal_key = self.current_displayed_signal

        if signal_key in self.marker_items:
            self.main_plot_widget.removeItem(self.marker_items[signal_key])

        marker_item = ScatterPlotItem(symbol="o", pen=None, brush="r", size=6)
        self.marker_items[signal_key] = marker_item
        self.main_plot_widget.addItem(marker_item)

        spots = [
            {"pos": (time, amp)}
            for time, amp in zip(sampling_times, sampling_amplitudes)
        ]
        marker_item.setData(spots)

    def display_selected_signal(self):

        self.difference_plot_widget.clear()
        self.reconstruct_plot_widget.clear()
        self.freq_plot_widget.clear()

        selected_signal_items = self.signal_list.selectedItems()
        if selected_signal_items:
            # Clear selection in the result list
            self.result_list.blockSignals(True)
            self.result_list.clearSelection()
            self.result_list.blockSignals(False)

            item = selected_signal_items[0]
            item_widget = self.signal_list.itemWidget(item)
            if item_widget:
                signal_description = item_widget.description
                for signal in self.signals:
                    if (
                            signal_description
                            == f"Freq: {signal[0]} Hz, Amp: {signal[1]}, Phase: {signal[2]} rad"
                    ):
                        wave = self.generate_wave(signal[0], signal[1], signal[2], 1)
                        self.plot_waveform(wave, signal_description)
                        break

    def display_selected_result(self):
        selected_result_items = self.result_list.selectedItems()
        if selected_result_items:
            # Clear selection in the signal list
            self.signal_list.blockSignals(True)
            self.signal_list.clearSelection()
            self.signal_list.blockSignals(False)

            item = selected_result_items[0]
            item_widget = self.result_list.itemWidget(item)
            if item_widget:
                mixed_signal_description = item_widget.description
                mixed_signal = self.result_signals.get(mixed_signal_description, None)
                if mixed_signal is not None:
                    # Check if the signal is a mixed signal or an uploaded signal
                    if mixed_signal_description in self.mixed_signal_components:
                        # get the frequency array values from the component description
                        component_frequencies = [
                            float(comp.split(" ")[1])
                            for comp in self.mixed_signal_components[
                                mixed_signal_description
                            ]
                        ]
                        self.f_max = max(component_frequencies)*1.05
                    else:
                        fft_result = np.fft.fft(mixed_signal)
                        freqs = np.fft.fftfreq(len(mixed_signal), 1 / self.fs)
                        magnitude = np.abs(fft_result)

                        positive_freqs = freqs[freqs >= 0]
                        positive_magnitude = magnitude[freqs >= 0]
                        max_freq_idx = np.argmax(positive_magnitude)
                        self.f_max = positive_freqs[max_freq_idx]

                    self.plot_waveform_with_markers(
                        mixed_signal, mixed_signal_description
                    )
                    self.plot_sampling_markers()
                    self.reconstruct_signal()

                    self.components_list.clear()
                    components = self.mixed_signal_components.get(
                        mixed_signal_description, []
                    )
                    if components:
                        self.components_list.addItems(components)
                    else:
                        self.components_list.addItem("No components found")

    def mix_signals(self):
        # duration = 1
        mixed_signal = np.zeros(int(self.fs))
        components = []
        self.duration = 10
        # tracking of max frequency
        max_frequency = 0
        for frequency, amplitude, phase in self.signals:
            wave = self.generate_wave(frequency, amplitude, phase, self.duration)
            mixed_signal += wave
            components.append(
                f"Freq: {frequency} Hz, Amp: {amplitude}, Phase: {phase} rad"
            )
            max_frequency = max(max_frequency, frequency)

        mixed_signal_description = f"Signal{len(self.result_list) + 1}"
        self.result_signals[mixed_signal_description] = mixed_signal
        self.mixed_signal_components[mixed_signal_description] = components

        # final result of max frequency
        self.f_max = max_frequency
        list_item_widget = SignalListItemWidget(mixed_signal_description)
        list_item_widget.delete_signal.connect(
            lambda desc=mixed_signal_description: self.delete_signal(
                self.result_list, desc, self.result_signals
            )
        )
        list_item = QListWidgetItem(self.result_list)
        list_item.setSizeHint(list_item_widget.sizeHint())
        self.result_list.setItemWidget(list_item, list_item_widget)

        self.plot_waveform(mixed_signal, mixed_signal_description)

        # Clear the signal list
        self.signals.clear()
        self.signal_list.clear()

        # select reuslt signal by defult
        list_item.setSelected(True)
        self.reconstruct_signal()

        # self.reconstruct_signal(mixed_signal, mixed_signal_description)

        # Debug for f_max

    def generate_wave(self, frequency, amplitude, phase, duration):
        t = np.linspace(0, duration, int(self.fs), endpoint=False)
        wave = amplitude * np.sin(2 * np.pi * frequency * t + phase)
        print(
            f"Generated wave: freq={frequency}, amp={amplitude}, phase={phase}, duration={duration}"
        )
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

        signal_description = (
            f"Freq: {frequency} Hz, Amp: {amplitude}, Phase: {phase} rad"
        )
        list_item_widget = SignalListItemWidget(signal_description)
        list_item_widget.delete_signal.connect(
            lambda desc=signal_description: self.delete_signal(
                self.signal_list, desc, self.signals
            )
        )

        list_item = QListWidgetItem(self.signal_list)
        list_item.setSizeHint(list_item_widget.sizeHint())
        self.signal_list.setItemWidget(list_item, list_item_widget)
        list_item.setSelected(True)

        self.freq_input.clear()
        self.amp_input.clear()
        self.phase_input.clear()

        # Plot the newly added signal
        wave = self.generate_wave(frequency, amplitude, phase, 1)
        self.plot_waveform(wave, signal_description)

    def delete_signal(self, list_widget, description, data_structure):
        for i in range(list_widget.count()):
            item = list_widget.item(i)
            item_widget = list_widget.itemWidget(item)
            if item_widget and item_widget.description == description:
                list_widget.takeItem(i)
                break

        if data_structure is self.signals:
            for signal in self.signals:
                signal_description = (
                    f"Freq: {signal[0]} Hz, Amp: {signal[1]}, Phase: {signal[2]} rad"
                )
                if signal_description == description:
                    self.signals.remove(signal)
                    break
        else:
            if description in data_structure:
                del data_structure[description]

        if self.current_displayed_signal == description:
            if data_structure:
                first_signal_description = next(iter(data_structure))
                self.plot_waveform(
                    data_structure[first_signal_description], first_signal_description
                )
            else:
                self.main_plot_widget.clear()
                self.reconstruct_plot_widget.clear()
                self.difference_plot_widget.clear()
                self.freq_plot_widget.clear()
                self.current_displayed_signal = None

        components = self.mixed_signal_components.get(description, [])
        if components:
            self.components_list.clear()

    def upload_signal(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Open Signal File", "", "Text Files (*.txt *.csv)"
        )
        self.duration = 1
        if file_path:
            try:

                signal_data = np.loadtxt(file_path, delimiter=",")

                if signal_data.shape[1] > 1:
                    signal = signal_data[:1000, 1]
                else:
                    signal = signal_data[:1000, 0]

                signal_description = f"Uploaded Signal ({file_path.split('/')[-1]})"
                list_item_widget = SignalListItemWidget(signal_description)
                list_item_widget.delete_signal.connect(
                    lambda desc=signal_description: self.delete_signal(
                        self.result_list, desc, self.result_signals
                    )
                )

                list_item = QListWidgetItem(self.result_list)
                list_item.setSizeHint(list_item_widget.sizeHint())
                self.result_list.setItemWidget(list_item, list_item_widget)

                self.result_signals[signal_description] = signal

                self.plot_waveform(signal, signal_description)

            except Exception as e:
                print(f"Failed to load signal: {e}")

    def plot_waveform(self, signal, description=None):
        self.main_plot_widget.clear()
        t = np.linspace(0, self.duration, len(signal))
        self.main_plot_widget.plot(t, signal, pen="b")
        self.main_plot_widget.setTitle("Signal Waveform")
        self.main_plot_widget.setLabel("left", "Amplitude")
        self.main_plot_widget.setLabel("bottom", "Time [s]")

        self.current_displayed_signal = description

    def add_noise(self):
        snr_value = self.snr_slider.value()
        selected_items = self.result_list.selectedItems()
        if selected_items:
            item = selected_items[0]
            item_widget = self.result_list.itemWidget(item)
            if item_widget:
                mixed_signal_description = item_widget.description
                mixed_signal = self.result_signals.get(mixed_signal_description, None)

                if mixed_signal is not None:
                    self.signal = mixed_signal
                    signal_description = mixed_signal_description

                if snr_value > 0:
                    signal_power = np.mean(np.square(self.signal))
                    noise_power = signal_power / (10 ** (snr_value / 10)) * 10
                    noise = np.sqrt(noise_power) * np.random.normal(size=len(self.signal))
                    noisy_signal = self.signal + noise
                else:
                    noisy_signal = self.signal
                self.noisy_signals[signal_description] = noisy_signal
                self.plot_waveform_with_markers(noisy_signal, signal_description)
    def update_snr_value(self, value):
        self.snr_value.setText("SNR Level : " + str(value))


app = QApplication(sys.argv)
window = SignalMixerApp()
window.show()
sys.exit(app.exec())
