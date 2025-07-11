from PyQt6 import QtCore, QtWidgets

from rascal2.settings import Settings, SettingsGroups, delete_local_settings
from rascal2.widgets.inputs import get_validated_input


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent):
        """
        Dialog to adjust RasCAL-2 settings.

        Parameters
        ----------
        parent : MainWindowView
            The view of the RasCAL-2 GUI
        """
        super().__init__(parent)

        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.settings = parent.settings.copy()
        self.reset_dialog = None

        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        tab_widget = QtWidgets.QTabWidget()
        tab_widget.addTab(SettingsTab(self, SettingsGroups.General), SettingsGroups.General)

        self.reset_button = QtWidgets.QPushButton("Reset to Defaults", self)
        self.reset_button.clicked.connect(self.reset_default_settings)
        self.accept_button = QtWidgets.QPushButton("OK", self)
        self.accept_button.clicked.connect(self.update_settings)
        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.accept_button)
        button_layout.addWidget(self.cancel_button)

        main_layout = QtWidgets.QVBoxLayout()
        main_layout.addWidget(tab_widget)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
        self.setWindowTitle("Settings")

    def update_settings(self) -> None:
        """Accept the changed settings"""
        self.parent().settings = self.settings
        self.parent().settings.save(self.parent().presenter.model.save_path)
        self.accept()

    def reset_default_settings(self) -> None:
        """Reset the settings to the global defaults"""
        delete_local_settings(self.parent().presenter.model.save_path)
        self.parent().settings = Settings()
        self.accept()


class SettingsTab(QtWidgets.QWidget):
    def __init__(self, parent: SettingsDialog, group: SettingsGroups):
        """A tab in the Settings Dialog tab layout.

        Parameters
        ----------
        parent : SettingsDialog
            The dialog in which this tab lies
        group : SettingsGroups
            The set of settings with this value in "title" field of the
            Settings object's "field_info" will be included in this tab.
        """
        super().__init__(parent)

        self.settings = parent.settings
        self.widgets = {}
        tab_layout = QtWidgets.QGridLayout()

        field_info = self.settings.model_fields
        group_settings = [key for (key, value) in field_info.items() if value.title == group]

        for i, setting in enumerate(group_settings):
            label_text = setting.replace("_", " ").title()
            label = QtWidgets.QLabel(label_text)
            label.setToolTip(field_info[setting].description)
            tab_layout.addWidget(label, i, 0)
            self.widgets[setting] = get_validated_input(field_info[setting])
            try:
                self.widgets[setting].set_data(getattr(self.settings, setting))
            except TypeError:
                self.widgets[setting].set_data(str(getattr(self.settings, setting)))
            self.widgets[setting].edited_signal.connect(lambda ignore=None, s=setting: self.modify_setting(s))
            tab_layout.addWidget(self.widgets[setting], i, 1)

        tab_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.setLayout(tab_layout)

    def modify_setting(self, setting: str):
        """A slot that updates the given setting in the dialog's copy of the Settings object.

        Connect this (via a lambda) to the "edited_signal" of the corresponding widget.

        Parameters
        ----------
        setting : str
            The name of the setting to be modified by this slot
        """
        setattr(self.settings, setting, self.widgets[setting].get_data())
