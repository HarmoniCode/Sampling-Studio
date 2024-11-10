import pytest
from PyQt6.QtWidgets import QApplication
from main import SignalMixerApp

@pytest.fixture(scope="module")
def app():
    return QApplication([])

@pytest.fixture
def signal_mixer_app(app):
    return SignalMixerApp()

def test_activate_slider_radio1_checked(signal_mixer_app):
    signal_mixer_app.radio1.setChecked(True)
    signal_mixer_app.activate_slider(signal_mixer_app.sampling_slider.value())
    assert signal_mixer_app.sampling_slider.isEnabled() == True
    assert signal_mixer_app.sampling_slider_2.isEnabled() == False

def test_activate_slider_radio2_checked(signal_mixer_app):
    signal_mixer_app.radio2.setChecked(True)
    signal_mixer_app.activate_slider(signal_mixer_app.sampling_slider_2.value())
    assert signal_mixer_app.sampling_slider.isEnabled() == False
    assert signal_mixer_app.sampling_slider_2.isEnabled() == True