import hashlib
import os

import jsonpath


def fa_code(code):
    return os.popen(f'kmg 2fa {code}').readline()


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
            if new[key] == old[key]:
                flag = True
                ignore_keys.append(key)
                return flag
        elif isinstance(old[key], dict):
            flag = assert_dict_equal(old[key], new, flag, ignore_keys)
        elif isinstance(old[key], list) and len(old[key]) > 1:
            if isinstance(old[key][0], dict):
                for dic in old[key]:
                    flag = assert_dict_equal(dic, new, flag, ignore_keys)
    return flag
