#!/usr/bin/env python3
# @Time    : 2020-02-14
# @Author  : caicai
# @File    : request.py
import requests
import urllib3


urllib3.disable_warnings()

from myscan.lib.core.data import cmd_line_options, logger
from myscan.lib.core.common import getredis, gethostportfromurl
from myscan.lib.core.block_info import block_info
from time import sleep
from random import uniform
from myscan.pocs.search import searchmsg
from myscan.config import scan_set
import copy


def request(**kwargs_sour):
    kwargs=copy.deepcopy(kwargs_sour)
    red = getredis()

    # print("start:",kwargs)
    if not kwargs.get("verify", None):
        kwargs["verify"] = False
    if not kwargs.get("timeout", None):
        kwargs["timeout"] = 8
    if not kwargs.get("headers", None):
        kwargs["headers"] = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:38.0) Gecko/20100101 Firefox/38.0"}
    if cmd_line_options.proxy:
        kwargs["proxies"] = cmd_line_options.proxy
    if cmd_line_options.timeout:
        kwargs["timeout"] = cmd_line_options.timeout
    # print("end:",kwargs)
    if kwargs.get('data', None):
        if isinstance(kwargs.get("data"), str):
            kwargs["data"] = kwargs["data"].encode("utf-8", "ignore")
    r = None
    red.hincrby("count_all", "request", amount=1)
    h, p = gethostportfromurl(kwargs.get("url"))
    block = block_info(h, p)
    # retry
    for x in range(cmd_line_options.retry + 1):
        try:
            r = requests.request(**kwargs)
            block.push_result_status(0)
            break
        except requests.exceptions.ConnectTimeout:
            pass
            # logger.debug("request connect timeout :{}".format(kwargs["url"]))
        except requests.exceptions.ReadTimeout:
            pass
            # logger.debug("request read timeout :{}".format(kwargs["url"]))
        except Exception as ex:
            # print(kwargs)
            logger.debug("Request error url:{} error:{}".format(kwargs["url"], ex))
        block.push_result_status(1)
        sleep(uniform(0, 0.2))
    if r!=None:
        if scan_set.get("search_open", False):
            s = searchmsg(r)
            s.verify()
            s.saveresult()
    else:
        red.hincrby("count_all", "request_fail", amount=1)
    return r

