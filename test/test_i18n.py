"""Check complete translations and safe live language changes."""

from argparse import Namespace
from string import Formatter

from PyQt5 import QtWidgets as W
import pytest

from agxarm_control_gui.app import MainWindow
from agxarm_control_gui.i18n import LANGUAGES, MESSAGES, translate


def test_catalog_has_all_languages_and_matching_placeholders():
    for key, versions in MESSAGES.items():
        assert len(versions) == len(LANGUAGES), key
        fields = [{field for _, field, _, _ in Formatter().parse(text)
                   if field is not None} for text in versions]
        assert fields[0] == fields[1] == fields[2], key
        assert all(versions), key
    with pytest.raises(ValueError):
        translate('estop', 'invalid')


def test_language_switch_retains_config_disarms_and_keeps_estop_visible():
    app = W.QApplication.instance() or W.QApplication([])
    window = MainWindow(Namespace(demo=True, robot_model='nero', namespace=None,
                                   keyboard_topic='arm_keyboard_state', config='', language='zh'))
    window.show()
    window.editor.insertPlainText('# unsaved edit\n')
    content = window.editor.toPlainText()
    path = window.config_path
    for index, language in enumerate(LANGUAGES):
        window.allowed = True
        window.arm.setChecked(True)
        window.gate.press([0, 8])
        window.language_selector.setCurrentIndex(index)
        window.change_language()
        app.processEvents()
        assert not window.gate.armed and not any(window.gate.keys)
        assert window.editor.toPlainText() == content
        assert window.editor.document().isModified()
        assert window.config_path == path
        assert window.estop.text() == translate('estop', language)
        assert window.table.horizontalHeaderItem(4).text() == translate('torque', language)
        assert 'language:=' + language in window.command.text()
        for tab in range(3):
            window.tabs.setCurrentIndex(tab)
            app.processEvents()
            assert window.estop.isVisible()
            assert window.rect().contains(window.estop.mapTo(window, window.estop.rect().bottomRight()))
    window.close()
