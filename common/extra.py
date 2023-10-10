import hashlib
import os
import time

import jsonpath


def get_dict(name, values):
    return {name: values}


def json_extract(data: dict, path: str) -> list:
    return jsonpath.jsonpath(data, path)


def md5_string(in_str):
    md5 = hashlib.md5()
    md5.update(in_str.encode('utf-8'))
    return md5.hexdigest()


def assert_dict_equal(old: dict, new: dict, flag=False, ignore_keys=None):
    if ignore_keys is None:
        ignore_keys = []
    for key in old:
        if key in ignore_keys:
            continue
        if key in new.keys():
            assert new[key] == old[key], f"{key}期望值：{new[key]}, 实际值：{old[key]}"
            flag = True
            ignore_keys.append(key)
        elif isinstance(old[key], dict):
            flag = assert_dict_equal(old[key], new, flag, ignore_keys)
        elif isinstance(old[key], list) and len(old[key]) > 0:
            if isinstance(old[key][0], dict):
                for dic in old[key]:
                    flag = assert_dict_equal(dic, new, flag, ignore_keys)
    return flag


def str_format(strings):
    return strings.replace('\n', '').replace(' ', '').replace("'", '"').replace("None", 'null').replace('False', 'false').replace('True', 'true')


def time_format(time_stamp):
    local_time = time.localtime(time_stamp)
    str_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    return str_time


def check_port(port):
    if os.name == "nt":
        # Windows 平台
        if os.popen(f'netsTAT.EXE -ano | findstr {port} | findstr LISTENING').readline():
            pid = os.popen(f'netsTAT.EXE -ano | findstr {port} | findstr LISTENING').readline().split(' ')[-1].replace('\n', '')
            os.popen(f'taskkill /pid {pid} /f')
    elif os.name == "posix":
        # Linux 平台
        if os.popen(f'netstat -nltp| grep {port} |grep LISTEN').readline():
            pid = os.popen(f'netstat -nltp| grep {port} |grep LISTEN').readline().split(' ')[-1]
            os.popen(f'kill -9 {pid[:pid.find("/")]}')
