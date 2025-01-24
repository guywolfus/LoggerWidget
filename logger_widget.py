
import os
import logging

try:
    from PyQt6 import QtWidgets, QtCore, QtGui
except:
    from PyQt5 import QtWidgets, QtCore, QtGui


class LoggerWidget(QtWidgets.QWidget):
    """
    A GUI Logger widget, useful to have a visual representation of logging
    during any process. Defers to its logger attributes for easy and familiar interaction
    with this widget (e.g. `self.error()` will defer to `self.logger.error()`).
    """
    _filetype = 'log'
    _default_colors = {
        logging.DEBUG: {'fg': QtGui.QColor(QtCore.Qt.darkGreen), 'bg': QtGui.QColor(QtCore.Qt.transparent)},
        logging.INFO: {'fg': QtGui.QColor(QtCore.Qt.white), 'bg': QtGui.QColor(QtCore.Qt.transparent)},
        logging.WARNING: {'fg': QtGui.QColor(QtCore.Qt.yellow), 'bg': QtGui.QColor(QtCore.Qt.transparent)},
        logging.ERROR: {'fg': QtGui.QColor(QtCore.Qt.red), 'bg': QtGui.QColor(QtCore.Qt.transparent)},
        logging.CRITICAL: {'fg': QtGui.QColor(QtCore.Qt.white), 'bg': QtGui.QColor(QtCore.Qt.red)},
    }

    def __init__(self, logger=None, name="", level=logging.INFO, filepath="", parent=None):
        super().__init__(parent=parent)
        self.name = name if name else __name__
        self.level = level
        self.filepath = filepath if filepath else os.path.join(
            os.path.dirname(__name__),
            ".".join([self.name, self._filetype])
        )

        # logger
        """Set the logger level to DEBUG to ensure all logs are actually
        added, `self.level` is only responsible for filtering."""
        self.handler = LoggerHandler(self)
        _logger = logger if logger else logging.getLogger(self.name)
        self.set_logger(_logger)  # sets: self.logger

        # source & proxy (sort filter) models
        self.source_model = QtGui.QStandardItemModel(self)
        self.proxy_model = LevelFilterProxyModel(self.level, parent=self)
        self.proxy_model.setSourceModel(self.source_model)

        self.init_ui()
        self.apply_filter()

    def __getattr__(self, name):
        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return object.__getattribute__(self.logger, name)

    @property
    def log_levels(self):
        exclude_levels = {'NOTSET', 'WARN', 'FATAL'}  # filter out redundant levels
        level_names = {name for name in logging._nameToLevel.keys() if name not in exclude_levels}
        custom_levels = {name for name, level in self.logger.__class__.__dict__.items() if isinstance(level, int)}
        all_levels = set(level_names).union(custom_levels)
        return sorted(all_levels, key=lambda name: logging.getLevelName(name))

    def init_ui(self):
        log_level_lbl = QtWidgets.QLabel("Log Level:")
        log_level_lbl.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        log_level_lbl.setMinimumWidth(log_level_lbl.sizeHint().width())

        # log level combobox
        self.log_level_cmbx = QtWidgets.QComboBox(self)
        self.log_level_cmbx.addItems(self.log_levels)
        self.log_level_cmbx.currentIndexChanged.connect(self._on_log_level_cmbx_changed)

        current_level_name = logging.getLevelName(self.level)
        current_level_index = self.log_levels.index(current_level_name.upper())
        self.log_level_cmbx.setCurrentIndex(current_level_index)

        # header layout
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addWidget(log_level_lbl)
        header_layout.addWidget(self.log_level_cmbx)

        # colors checkbox
        self.colors_ckb = QtWidgets.QCheckBox("Colors")
        self.colors_ckb.setChecked(True)
        self.colors_ckb.toggled.connect(self._on_colors_ckb_toggled)

        # formatting checkboxes
        self.format_name_ckb = QtWidgets.QCheckBox("Logger Name")
        self.format_date_ckb = QtWidgets.QCheckBox("Date")
        self.format_filename_ckb = QtWidgets.QCheckBox("Filename Line")
        for cb in [self.format_name_ckb, self.format_date_ckb, self.format_filename_ckb]:
            cb.setChecked(True)
            cb.toggled.connect(self._on_format_ckb_toggled)

        # save log button
        self.save_log_btn = QtWidgets.QPushButton("Save")
        self.save_log_btn.clicked.connect(self._on_save_log_btn_clicked)

        # format layout
        format_layout = QtWidgets.QHBoxLayout()
        format_layout.addWidget(self.colors_ckb)
        format_layout.addWidget(self.format_name_ckb)
        format_layout.addWidget(self.format_date_ckb)
        format_layout.addWidget(self.format_filename_ckb)
        format_layout.addStretch()
        format_layout.addWidget(self.save_log_btn)

        # list view & mouse event filter
        self.list_view = QtWidgets.QListView(self)
        self.list_view.setModel(self.proxy_model)
        self.list_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self._show_context_menu_for_item)

        # main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(header_layout)
        main_layout.addLayout(format_layout)
        main_layout.addWidget(self.list_view)

    def _show_context_menu_for_item(self, position):
        index = self.list_view.indexAt(position)
        source_index = self.proxy_model.mapToSource(index)
        source_item = self.proxy_model.sourceModel().itemFromIndex(source_index)
        if source_item and hasattr(source_item, 'show_context_menu'):
            source_item.show_context_menu(self.list_view.mapToGlobal(position))

    def _on_log_level_cmbx_changed(self):
        self.set_level(self.log_level_cmbx.currentText().upper())

    def _on_format_ckb_toggled(self):
        for item in self.get_items():
            item.set_text(
                format_name=self.format_name_ckb.isChecked(),
                format_date=self.format_date_ckb.isChecked(),
                format_filename=self.format_filename_ckb.isChecked(),
            )

    def _on_colors_ckb_toggled(self):
        for item in self.get_items():
            item.set_color(self.colors_ckb.isChecked())

    def _on_save_log_btn_clicked(self):
        self.save_log()

    def save_log(self):
        with open(self.filepath, "w") as log:
            for item in self.get_items(filtered=True):
                log.write(item.text() + "\n")
        print(f"Saving log file: {self.filepath}")

    def set_logger(self, logger):
        if not isinstance(logger, logging.Logger):
            raise TypeError(f"Expected object of type Logger, got {type(logger)} instead.")
        self.logger = logger
        self.name = logger.name
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)

    def set_level(self, level):
        if level:
            self.level = logging.getLevelName(level)
            self.apply_filter()

    def set_format_colors_checked(self, state=True):
        self.colors_ckb.setChecked(state)

    def set_format_name_checked(self, state=True):
        self.format_name_ckb.setChecked(state)

    def set_format_date_checked(self, state=True):
        self.format_date_ckb.setChecked(state)

    def set_format_filename_checked(self, state=True):
        self.format_filename_ckb.setChecked(state)

    def apply_filter(self):
        self.proxy_model.apply_filter(self.level)

    def get_items(self, filtered=False):
        if filtered:
            for row in range(self.proxy_model.rowCount()):
                proxy_index = self.proxy_model.index(row, 0)
                source_index = self.proxy_model.mapToSource(proxy_index)
                item = self.proxy_model.sourceModel().itemFromIndex(source_index)
                yield item
        else:
            for row in range(self.source_model.rowCount()):
                item = self.source_model.item(row)
                yield item

    def add_log_item(self, message, level, log_date, log_filename):
        record = logging.makeLogRecord({'msg': message})
        record.levelno = level
        item = LogItem(
            message=message,
            level=level,
            name=self.name,
            date=log_date,
            filename=log_filename,
            colors=self._default_colors[level],
            colorize=self.colors_ckb.isChecked(),
            format_name=self.format_name_ckb.isChecked(),
            format_date=self.format_date_ckb.isChecked(),
            format_filename=self.format_filename_ckb.isChecked(),
        )
        self.source_model.appendRow(item)
        self.apply_filter()


class LoggerHandler(logging.Handler):
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def emit(self, record):
        log_date = logging.Formatter("%(asctime)s", "%Y-%m-%d %H:%M:%S").format(record)
        log_filename = logging.Formatter("%(filename)s:%(lineno)d").format(record)

        # remove exception info if it exists
        if record.exc_text:
            log_date = log_date.partition("\n")[0] + "]"
            log_filename = log_filename.partition("\n")[0] + "]"

        self.widget.add_log_item(
            message=self.format(record),
            level=record.levelno,
            log_date=log_date,
            log_filename=log_filename,
        )


class LevelFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, level, parent=None):
        super(LevelFilterProxyModel, self).__init__(parent)
        self.level = level

    def apply_filter(self, level):
        self.level = level
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        index = self.sourceModel().index(source_row, 0, source_parent)
        item = self.sourceModel().itemFromIndex(index)
        if item is not None:
            return item.level >= self.level
        return False


class LogItem(QtGui.QStandardItem):
    def __init__(self, message, level, name, date, filename,
                 colors, colorize, format_name, format_date, format_filename):
        super().__init__()
        self.message = message
        self.level = level
        self.name = name
        self.date = date
        self.filename = filename
        self.colors = colors

        # set non-editable flag
        self.setFlags(self.flags() & ~QtCore.Qt.ItemIsEditable)

        self.set_text(format_name, format_date, format_filename)
        self.set_color(colorize)

    def __eq__(self, other):
        if isinstance(other, LogItem):
            return self.message == other.message
        return False

    def __hash__(self):
        return hash(self.message)

    def set_text(self, format_name=True, format_date=True, format_filename=True):
        log_text = ""
        if format_name and self.name: log_text += f"[{self.name}] "
        if format_date and self.date: log_text += f"[{self.date}] "
        if format_filename and self.filename: log_text += f"[{self.filename}] "
        log_text += f"{logging.getLevelName(self.level)}: {self.message}"
        self.setText(log_text)

    def set_color(self, colorize=True):
        if colorize:
            self.setForeground(self.colors['fg'])
            self.setBackground(self.colors['bg'])
        else:
            self.setForeground(QtGui.QColor(QtCore.Qt.white))
            self.setBackground(QtGui.QColor(QtCore.Qt.transparent))

    def show_context_menu(self, position):
        menu = QtWidgets.QMenu()
        copy_action = menu.addAction("Copy log")
        copy_action.triggered.connect(self.copy_to_clipboard)
        menu.exec_(position)

    def copy_to_clipboard(self):
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard.setText(self.text())
        print(f"Copied: {self.text()}")


# example use-case:
if __name__ == "__main__":
    import sys

    # initialize a main window for the widget
    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    logger_widget = LoggerWidget(level=logging.ERROR)
    main_window.setCentralWidget(logger_widget)
    main_window.setWindowTitle("Logger Window")
    main_window.resize(700, 400)
    main_window.show()

    # can use the logging methods directly on the LoggerWidget instance
    logger_widget.debug("This is a debug message")
    logger_widget.info("This is an info message")
    logger_widget.warning("This is a warning message")
    logger_widget.error("This is an error message")
    logger_widget.critical("This is a critical message")
    logger_widget.log(logging.INFO, "Custom log message")
    try:
        x = 1 / 0
    except Exception as e:
        logger_widget.exception("An error occurred: %s", e)

    sys.exit(app.exec_())
