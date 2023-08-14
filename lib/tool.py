# -*- coding: utf-8 -*-
# File: tool.py
# Time: 2022/4/24 22:37
# Author: jiaxin
# Email: 1094630886@qq.com
import requests
import yaml
import logging
import re
import math

formatter = logging.Formatter('[%(asctime)s] %(filename)s line %(lineno)d - %(levelname)s: %(message)s')
logger = logging.getLogger("image-sync")
log_level = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR,
             'critical': logging.CRITICAL}
DEFAULT_LEVEL = 'info'
DEFAULT_FILE = 'image-sync.log'
DEFAULT_SYNCPOLICY = 'latest'
DEFAULT_NUM = 30
database_type = ['sqlite', 'mysql']
sync_policy_type = ['latest', 'all']
BATCH_NUM = 20


def set_log_file(path):
    file_handler = logging.FileHandler(path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def load_config(path):
    with open(path, "r", encoding='utf-8') as file:
        config = yaml.safe_load(file)
        logger.setLevel(log_level[DEFAULT_LEVEL])

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # 参数检查
        if config.get("global", None) is None or not isinstance(config.get("global", None), dict):
            logger.error("缺少global参数")
            exit()

        if config['global'].get('log', None) is None or not isinstance(config['global'].get('log', None), dict):
            set_log_file(DEFAULT_FILE)
            logger.warning("缺少global.log参数，将使用默认值")
            logger.warning("设置日志等级为默认等级:" + DEFAULT_LEVEL)
            logger.warning("设置日志路径为默认路径:" + DEFAULT_FILE)

        if config['global']['log'].get('level', None) is None and config['global']['log'].get('path', None) is None:
            set_log_file(DEFAULT_FILE)
            logger.warning("缺少global.log.level参数，设置日志等级为默认等级:" + DEFAULT_LEVEL)
            logger.warning("缺少global.log.path参数，设置日志为默认路径:" + DEFAULT_FILE)
        elif config['global']['log'].get('level', None) is None and config['global']['log'].get('path', None):
            set_log_file(config['global']['log'].get('path'))
            logger.warning("缺少global.log.level参数，设置日志等级为默认等级:" + DEFAULT_LEVEL)
            logger.info("设置日志路径为:" + config['global']['log'].get('path'))
        elif config['global']['log'].get('level', None) and config['global']['log'].get('path', None) is None:
            if config['global']['log']['level'] in log_level:
                set_log_file(DEFAULT_FILE)
                logger.setLevel(log_level[config['global']['log']['level']])
                logger.info("设置日志等级为" + config['global']['log']['level'])
                logger.warning("缺少global.log.path参数，设置日志为默认路径:" + DEFAULT_FILE)
            else:
                set_log_file(DEFAULT_FILE)
                logger.warning("非法的global.log.level参数:" + config['global']['log'][
                    'level'] + "正确参数为：debug、info、warning、error、critical，将使用默认值取代错误参数")
                logger.warning("设置日志等级为默认等级:" + DEFAULT_LEVEL)
                logger.warning("缺少global.log.path参数，设置日志为默认路径:" + DEFAULT_FILE)
        elif config['global']['log'].get('level', None) and config['global']['log'].get('path', None):
            if config['global']['log']['level'] in log_level:
                logger.setLevel(log_level[config['global']['log']['level']])
                set_log_file(config['global']['log']['path'])
                logger.info("设置日志等级为" + config['global']['log']['level'])
                logger.info("设置日志路径路径为:" + config['global']['log'].get('path'))
            else:
                set_log_file(config['global']['log']['path'])
                logger.warning("非法的global.log.level参数:" + config['global']['log'][
                    'level'] + "，正确参数为：debug、info、warning、error、critical，将使用默认值取代错误参数")
                logger.warning("设置日志等级为默认等级:" + DEFAULT_LEVEL)
                logger.info("设置日志路径路径为:" + config['global']['log']['path'])

        if config["global"].get("database", None) is None or not isinstance(config["global"].get("database", None),
                                                                            dict):
            logging.error("缺少global.database参数")
            exit()
        if config["global"]['database'].get('type') is None:
            logger.error("缺少global.database.type参数")
            exit()
        if config['global']['database']['type'] not in database_type:
            text = ''
            for i in range(len(database_type)):
                if i != len(database_type) - 1:
                    text = text + database_type[i] + '、'
                else:
                    text = text + database_type[i]
            logger.error("非法的global.database.type参数:" + config['global']['database'][
                'type'] + "，目前仅支持" + text + "数据库")
            exit()
        if config['global']['database']['type'] == 'sqlite' and config['global']['database'].get('dbfile',
                                                                                                 None) is None:
            logger.error("缺少global.database.dbfile参数")
            exit()
        if config['global']['database']['type'] == 'mysql':
            if config['global']['database'].get('host', None) is None:
                logger.warning("缺少global.database.host参数，设置host为默认值127.0.0.1")
                config["global"]["database"]["host"] = "127.0.0.1"
            if config['global']['database'].get('port', None) is None:
                logger.warning("缺少global.database.port参数，设置port为默认值3306")
                config["global"]["database"]["port"] = 3306
            if config['global']['database'].get('db', None) is None:
                logger.warning("缺少global.database.db参数，设置db为默认值image-sync")
                config["global"]["database"]["db"] = "image-sync"
            else:
                if re.search("-", config['global']['database']['db']):
                    logger.error("mysql数据库db不支持 - 符号！！！")
                    exit()
            if config['global']['database'].get('username', None) is None or config['global']['database'].get(
                    'password', None) is None:
                logger.error("缺少mysql数据库用户名或密码参数！！！")
                exit()

        if config['global'].get('syncPolicy', None) is None or not isinstance(config['global'].get('syncPolicy', None),
                                                                              dict):
            logger.warning("缺少global.syncPolicy参数，将使用默认值")
            logger.warning(
                "设置全局同步策略为默认全局同步策略:" + DEFAULT_SYNCPOLICY + "，设置全局同步数为默认全局同步数:" + str(
                    DEFAULT_NUM))
            config['global']['syncPolicy'] = {'type': DEFAULT_SYNCPOLICY, 'num': DEFAULT_NUM}
        if config['global']['syncPolicy'].get('type', None) is None:
            logger.warning("缺少global.syncPolicy.type参数，设置全局同步策略为默认全局同步策略:" + DEFAULT_SYNCPOLICY)
            logger.warning("缺少global.syncPolicy.num参数，设置全局同步数为默认全局同步数:" + str(DEFAULT_NUM))
            config['global']['syncPolicy'] = {'type': DEFAULT_SYNCPOLICY, 'num': DEFAULT_NUM}
        elif config['global']['syncPolicy'].get('type', None):
            if config['global']['syncPolicy']['type'] not in sync_policy_type:
                text = ''
                for i in range(len(sync_policy_type)):
                    if i != len(sync_policy_type) - 1:
                        text = text + sync_policy_type[i] + '、'
                    else:
                        text = text + sync_policy_type[i]
                logger.error(
                    "非法的global.syncPolicy.type参数:" + config['global']['syncPolicy'][
                        'type'] + "，目前仅支持" + text + "同步策略")
                exit()
            elif config['global']['syncPolicy']['type'] == 'latest':
                if config['global']['syncPolicy'].get('num', None) is None:
                    logger.info("设置全局同步策略为:" + config['global']['syncPolicy']['type'])
                    logger.warning("缺少global.syncPolicy.num参数，设置全局同步数为默认全局同步数:" + str(DEFAULT_NUM))
                    config['global']['syncPolicy'] = {'type': config['global']['syncPolicy']['type'],
                                                      'num': DEFAULT_NUM}
                else:
                    logger.info("设置全局同步策略为:" + config['global']['syncPolicy']['type'])
                    logger.info("设置全局同步数为:" + str(config['global']['syncPolicy']['num']))
                    config['global']['syncPolicy'] = {'type': config['global']['syncPolicy']['type'],
                                                      'num': config['global']['syncPolicy']['num']}
        if config['global'].get('batch_num', None) is None:
            logger.warning("缺少global.batch_num参数，将使用默认值" + str(BATCH_NUM))
            config['global']['batch_num'] = BATCH_NUM
        return config


def docker_io_get_tag(image):
    # 每页最多100个
    # 数据格式样例 https://hub.docker.com/v2/repositories/library/busybox/tags/?page_size=100&page=1
    docker_io_url = 'https://hub.docker.com/v2/repositories/{namespace}/{image}/tags/?page_size=100&page='.format(
        namespace=image['namespace'], image=image['name'])

    tag_list = []
    if image['syncPolicy']['type'] == 'latest':
        page = math.ceil(image['syncPolicy']['num'] / 100) + 1
        mod = image['syncPolicy']['num'] % 100
        for i in range(1, page):
            response = requests.get(docker_io_url + str(i)).json()
            if response.get('results', None):
                image_info_list = response['results']
                if mod == 0 or i < page - 1:
                    for image_info in image_info_list:
                        tag_list.append(image_info['name'])
                else:
                    for j in range(mod if mod <= len(image_info_list) else len(image_info_list)):
                        tag_list.append(image_info_list[j]['name'])
            else:
                break
    elif image['syncPolicy']['type'] == 'all':
        i = 1
        while True:
            response = requests.get(docker_io_url + str(i)).json()
            if response.get('results', None):
                image_info_list = response['results']
                for image_info in image_info_list:
                    tag_list.append(image_info['name'])
                i += 1
            else:
                break
    return tag_list


def k8s_gcr_io_get_tag(image):
    # 数据格式样例：https://k8s.gcr.io/v2/kube-apiserver/tags/list
    if image['namespace']:
        k8s_gcr_io_url = 'https://k8s.gcr.io/v2/{namespaces}/{image}/tags/list'.format(namespaces=image['namespace'],
                                                                                       image=image['name'])
    else:
        k8s_gcr_io_url = 'https://k8s.gcr.io/v2/{image}/tags/list'.format(image=image['name'])

    response = requests.get(k8s_gcr_io_url).json()
    image_info_dict = response['manifest']
    all_tag_list = []
    if image['syncPolicy']['type'] == 'latest':
        tag_list = []
        # 遍历数据获取镜像更新时间然后排序
        for image_info in image_info_dict.values():
            # 过滤没用的数据
            if image_info['tag'] and not re.search('sha256-[\d\w]*.sig', image_info['tag'][0]):
                upload_time = image_info['timeUploadedMs']
                tag_list.append({'tag': image_info['tag'], 'upload_time': upload_time})
        tag_list = sorted(tag_list, key=lambda x: x['upload_time'],
                          reverse=True)  # 数据样例：[{'tag': ['v1.8.1'], 'upload_time': '1687966171419'}, {'tag': ['v1.8.0'], 'upload_time': '1685451089512'}]
        i = 0
        for data in tag_list:
            for tag in data['tag']:
                if i < image['syncPolicy']['num']:
                    all_tag_list.append(tag)
                    i += 1
                else:
                    break
    elif image['syncPolicy']['type'] == 'all':
        for image_info in image_info_dict.values():
            if image_info['tag'] and not re.search('sha256-[\d\w]*.sig', image_info['tag'][0]):
                for tag in image_info['tag']:
                    all_tag_list.append(tag)
    return all_tag_list


def quay_io_get_tag(image):
    # 数据格式样例：
    quay_io_url = 'https://quay.io/api/v1/repository/{namespaces}/{image}/tag?onlyActiveTags=true&limit=100&page='.format(
        namespaces=image['namespace'], image=image['name'])
    tag_list = []
    if image['syncPolicy']['type'] == 'latest':
        page = math.ceil(image['syncPolicy']['num'] / 100) + 1
        mod = image['syncPolicy']['num'] % 100
        for i in range(1, page):
            response = requests.get(quay_io_url + str(i)).json()
            image_info_list = response['tags']
            if len(image_info_list):
                if mod == 0 or i < page - 1:
                    for image_info in image_info_list:
                        tag_list.append(image_info['name'])
                else:
                    for j in range(mod if mod <= len(image_info_list) else len(image_info_list)):
                        tag_list.append(image_info_list[j]['name'])
            else:
                break
    elif image['syncPolicy']['type'] == 'all':
        i = 1
        while True:
            response = requests.get(quay_io_url + str(i)).json()
            image_info_list = response['tags']
            if len(image_info_list):
                for image_info in image_info_list:
                    tag_list.append(image_info['name'])
                i += 1
            else:
                break
    return tag_list


if __name__ == '__main__':
    image = {'namespace': 'jenkins', 'name': 'jenkins', 'source': 'docker.io',
             'target': '[registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync]',
             'syncPolicy': {'type': 'latest', 'num': 150}}
    tag = docker_io_get_tag(image)
    # image = {'namespace': '', 'name': 'pause', 'source': 'k8s.gcr.io',
    #          'target': '[registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync]',
    #          'syncPolicy': {'type': 'latest', 'num': 895}}
    # tag = k8s_gcr_io_get_tag(image)
    # image = {'namespace': 'coreos', 'name': 'flannel', 'source': 'quay.io',
    #          'target': '[registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync]',
    #          'syncPolicy': {'type': 'latest', 'num': 11}}
    # tag = quay_io_get_tag(image)
    i = 1
    for j in tag:
        print(i, j)
        i += 1
