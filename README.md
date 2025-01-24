
# LoggerWidget
A GUI Logger widget, useful to have a visual representation of logging during any process.
Defers to its logger attributes for easy and familiar interaction with this widget (e.g. `self.error()` will defer to `self.logger.error()`).

![LoggerWidget example](https://static.wixstatic.com/media/eaa8d1_1bfbe8dac0c642d49bab0504765ea69c~mv2.png)

### Features:

* __Log level__: <br>
This dropdown easily allows to filter out the logs by level, displaying only logs that are above the selected option.

* __Formatting options__: <br>
Several checkboxes allow you to format/display the logs the way you want them. Also, right-clicking a log will let you to copy the log's text in its formatted manner.

* __Save__: <br>
This button will save the output ".log" file in the same folder as the logger (can be overwritten as needed), in the same format as the selected options.

* Supports Qt versions PyQt5 and PyQt6

* The above example is provided in the code's `if __name__ == "__main__"` block.

<br>
If you've encountered any bugs or issues, please feel free to reach out to me at: guywolfus@gmail.com
