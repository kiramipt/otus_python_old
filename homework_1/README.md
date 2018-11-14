# Getting Started
To run script use: ```python log_anayzer.py```

To pass your params through json file use: ```python log_anayzer.py --config config.json```

Examples of config params:
* **LOG_DIR**: path to directory with log files (default="./log")
* **REPORT_DIR**: path to directory with report files (default="./reports")
* **REPORT_SIZE**: size of report, render statistics only for top n urls (default=10)
* **LOG_FILE**: path to script logging file (default=None)
* **ERRORS_LIMIT**: percentage of errors which we can allow when parsing log files (default=0.64)

To run unittest use: ```python test_log_anayzer.py```
