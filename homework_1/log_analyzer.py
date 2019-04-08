#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import gzip
import logging
import traceback

import argparse
import json
import datetime

from statistics import median
from string import Template

DEFAULT_CONFIG = {
    "REPORT_SIZE": 10,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOG_FILE": None,
    "ERRORS_LIMIT": 0.64
}


def setup_logging(log_file):
    """
    Setup logging

    :param log_file: log file name
    :type log_file: str
    """
    logging.basicConfig(
        format=u"[%(asctime)s] %(levelname).1s %(message)s",
        filename=log_file,
        level=logging.INFO,
        datefmt='%Y.%m.%d %H:%M:%S'
    )


def find_last_log_file(dir_path):
    """
    Find last log file in directory

    :param dir_path: dir path in which we search log files
    :type dir_path: str
    :return: return tuple with file_path to last log file, date for this file and log file extension
    :rtype: tuple
    """

    # file regexp pattern
    pattern_str = re.compile(r"^nginx-access-ui\.log-(\d{8})(\.gz)?$")
    pattern = re.compile(pattern_str)

    # find last log file in log_dir
    last_log_file_name = ''
    last_log_date = ''
    file_extension = ''

    # try to find last log file
    for file_name in os.listdir(dir_path):
        if pattern.match(file_name):

            log_date = re.search(pattern_str, file_name).group(1)
            if log_date > last_log_date:
                last_log_date = log_date
                last_log_file_name = os.path.join(dir_path, file_name)

    # if we find last log file then extract its extension and log date
    if last_log_file_name:
        last_log_date = datetime.datetime.strptime(last_log_date, '%Y%m%d').date()
        if last_log_file_name.endswith('.gz'):
            file_extension = 'gz'
        else:
            file_extension = 'plain'

    return last_log_file_name, last_log_date, file_extension


def calculate_statistics(file_path, file_extension, errors_limit=None):
    """
    Calculate statistics using data from file

    :param file_path: path to file with logs
    :type file_path: str
    :param file_extension: extension of file with logs
    :type file_extension: str
    :param errors_limit: error percent that critical to statistics
    :type errors_limit: float
    :return: dictionary with statistics by each unique url
    :rtype: dict
    """

    # if file have extension .gz then use appropriate open function
    if file_extension == 'gz':
        file_open = gzip.open
    else:
        file_open = open

    # read file with logs and collect raw statistics
    with file_open(file_path, 'rt') as f:
        statistics = get_raw_statistics(f, errors_limit)

    # calculate general statistics for all urls
    all_count = sum(len(data) for data in statistics.values())
    all_time_sum = sum(sum(data) for data in statistics.values())

    # calculate enriched_ statistics for html report
    enriched_statistics = {}
    for url, data in statistics.items():
        count = len(data)
        count_perc = count / all_count
        time_sum = sum(data)
        time_perc = time_sum / all_time_sum
        time_avg = time_sum / count
        time_max = max(data)
        time_med = median(data)

        enriched_statistics[url] = {
            'url': url,
            'count': count,
            'count_perc': round(count_perc * 100, 3),
            'time_sum': round(time_sum, 3),
            'time_perc': round(time_perc * 100, 3),
            'time_avg': round(time_avg, 3),
            'time_max': round(time_max, 3),
            'time_med': round(time_med, 3),
        }

    return enriched_statistics


def get_raw_statistics(f, errors_limit):
    """
    Get raw statistics to each unique url from file

    :param f: file_handler
    :type f: TextIOWrapper
    :param errors_limit: error percent that critical to statistics
    :type errors_limit: float
    :return: dict with raw statistics
    :rtype: dict
    """

    statistics = {}
    errors = 0
    records = 0
    for line in f:

        url_break = line.split('] "')
        records += 1
        errors += 1

        try:
            if len(url_break) == 2:
                url_break = url_break[1].split('"')[0].split()
                if len(url_break) == 3:
                    url = url_break[1]
                    request_time = float(line.split()[-1])
                    statistics.setdefault(url, []).append(request_time)
                    errors -= 1
        except:
            pass

    if errors_limit is not None and records > 0 and errors / records > errors_limit:
        raise Exception('Errors limit exceed')

    return statistics


def render_template(template_file_path, report_file_path, statistics):
    """
    Render statistics in html report using template and write it into report file

    :param template_file_path: path to template
    :type template_file_path: str
    :param report_file_path: path to created report
    :type report_file_path: str
    :param statistics: list of jsons with statistics
    :type statistics: list
    """

    # open report template file and replace $table_json to our data
    with open(template_file_path) as f:
        s = Template(f.read())
        s = s.safe_substitute(table_json=json.dumps(statistics))

    # write rendered report to report file
    with open(report_file_path, 'w') as f:
        f.write(s)


def main(config):
    """
    Start all calculations

    :param config: dict with configs
    :type config: dict
    """

    # search path to last log file
    last_log_file_path, last_log_date, last_log_file_extension = find_last_log_file(config['LOG_DIR'])
    if not last_log_file_path:
        logging.info('Not found log files')
        return

    # report file checking
    report_file_name = 'report-{0}.html'.format(last_log_date.strftime('%Y.%m.%d'))
    report_file_path = os.path.join(config['REPORT_DIR'], report_file_name)
    template_file_path = os.path.join(config['REPORT_DIR'], 'report.html')

    # if file already exist than exit
    if os.path.isfile(report_file_path):
        logging.info('Current report is up-to-date')
        return

    # calculate statistics
    statistics = calculate_statistics(last_log_file_path, last_log_file_extension, config['ERRORS_LIMIT'])
    top_statistics = sorted(statistics.values(), key=lambda x: x['time_sum'], reverse=True)[:config['REPORT_SIZE']]

    # render template
    render_template(template_file_path, report_file_path, top_statistics)


if __name__ == "__main__":

    # create parser for config file path
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', help='path to config file')
    args = parser.parse_args()

    # update configs if we get config file path
    config = DEFAULT_CONFIG
    if args.config:
        with open(args.config) as f:
            external_config = json.load(f)
            config.update(external_config)

    setup_logging(config['LOG_FILE'])

    try:
        main(config)
    except:
        error_text = traceback.format_exc()
        logging.error(error_text)
