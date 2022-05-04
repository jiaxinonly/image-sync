# -*- coding: utf-8 -*-
# File: tool.py
# Time: 2022/4/24 22:37
# Author: jiaxin
# Email: 1094630886@qq.com
import requests
import yaml
import logging
import re

formatter = logging.Formatter('[%(asctime)s] %(filename)s line %(lineno)d - %(levelname)s: %(message)s')
logger = logging.getLogger("image-sync")
log_level = {'debug': logging.DEBUG, 'info': logging.INFO, 'warning': logging.WARNING, 'error': logging.ERROR,
             'critical': logging.CRITICAL}
DEFAULT_LEVEL = 'info'
DEFAULT_FILE = 'image-sync.log'
DEFAULT_SYNCPOLICY = 'latest'
DEFAULT_NUM = 30
database_type = ['sqlite', 'mysql']
sync_policy_type = ['latest']


def set_log_file(path):
    file_handler = logging.FileHandler(path)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def load_config(path):
    with open(path, "r") as file:
        config = yaml.safe_load(file)
        logger.setLevel(log_level[DEFAULT_LEVEL])

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if not config.get("global", None):
            logger.error("缺少global参数")
            exit()
        else:
            if not isinstance(config['global'].get('database', None), dict):
                logging.error("缺少global.database参数")
                exit()
            else:
                if not config['global']['database'].get('type', None):
                    logger.error("缺少global.database.type参数")
                    exit()
                elif config['global']['database']['type'] not in database_type:
                    text = ''
                    for i in range(len(database_type)):
                        if i != len(database_type) - 1:
                            text = text + database_type[i] + '、'
                        else:
                            text = text + database_type[i]
                    logger.error(
                        "非法的global.database.type参数:" + config['global']['database']['type'] + "，目前仅支持" + text + "数据库")
                else:
                    if config['global']['database']['type'] == 'sqlite':
                        if not config['global']['database'].get('dbfile', None):
                            logger.error("缺少global.database.dbfile参数")
                            exit()
                    else:
                        ...
                    if not config['global'].get('log', None):
                        set_log_file(DEFAULT_FILE)
                        logger.warning("缺少global.log参数，将使用默认值")
                        logger.warning("设置日志等级为默认等级:" + DEFAULT_LEVEL)
                        logger.warning("设置日志路径为默认路径:" + DEFAULT_FILE)
                    else:
                        if not config['global']['log'].get('level', None) and not config['global']['log'].get(
                                'path',
                                None):
                            set_log_file(DEFAULT_FILE)
                            logger.warning("缺少global.log.level参数，设置日志等级为默认等级:" + DEFAULT_LEVEL)
                            logger.warning("设置日志路径为默认路径:" + DEFAULT_FILE)
                        elif not config['global']['log'].get('level', None) and config['global']['log'].get('path',
                                                                                                            None):
                            set_log_file(config['global']['log'].get('path'))
                            logger.info("设置日志路径为:" + config['global']['log'].get('path'))
                            logger.warning("缺少global.log.level参数，设置日志等级为默认等级:" + DEFAULT_LEVEL)
                        elif config['global']['log'].get('level', None) and not config['global']['log'].get('path',
                                                                                                            None):
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
                        else:
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
                            logger.info("使用" + config['global']['database']['type'] + "数据库")
                            if not config['global'].get('syncPolicy', None):
                                logger.warning("缺少global.syncPolicy参数，将使用默认值")
                                logger.warning(
                                    "设置全局同步策略为默认全局同步策略:" + DEFAULT_SYNCPOLICY + "，设置全局同步数为默认全局同步数:" + str(DEFAULT_NUM))
                                config['global']['syncPolicy'] = {'type': DEFAULT_SYNCPOLICY, 'num': DEFAULT_NUM}
                            else:
                                if not config['global']['syncPolicy'].get('type', None):
                                    if not config['global']['syncPolicy'].get('num', None):
                                        logger.warning(
                                            "缺少global.syncPolicy.type参数，设置全局同步策略为默认全局同步策略:" + DEFAULT_SYNCPOLICY)
                                        logger.warning("缺少global.syncPolicy.num参数，设置全局同步数为默认全局同步数:" + str(DEFAULT_NUM))
                                        config['global']['syncPolicy'] = {'type': DEFAULT_SYNCPOLICY,
                                                                          'num': DEFAULT_NUM}
                                        return config
                                    else:
                                        logger.warning(
                                            "缺少global.syncPolicy.type参数，设置全局同步策略为默认全局同步策略:" + DEFAULT_SYNCPOLICY)
                                        logger.info("设置全局同步数为:" + str(config['global']['syncPolicy']['num']))
                                        config['global']['syncPolicy'] = {'type': DEFAULT_SYNCPOLICY,
                                                                          'num': config['global']['syncPolicy']['num']}
                                        return config
                                else:
                                    if config['global']['syncPolicy']['type'] in sync_policy_type:
                                        if not config['global']['syncPolicy'].get('num', None):
                                            logger.info("设置全局同步策略为:" + config['global']['syncPolicy']['type'])
                                            logger.warning(
                                                "缺少global.syncPolicy.num参数，设置全局同步数为默认全局同步数:" + str(DEFAULT_NUM))
                                            config['global']['syncPolicy'] = {
                                                'type': config['global']['syncPolicy']['type'],
                                                'num': DEFAULT_NUM}
                                            return config
                                        else:
                                            logger.info("设置全局同步策略为:" + config['global']['syncPolicy']['type'])
                                            logger.info("设置全局同步数为:" + str(config['global']['syncPolicy']['num']))
                                            config['global']['syncPolicy'] = {
                                                'type': config['global']['syncPolicy']['type'],
                                                'num': config['global']['syncPolicy']['num']}
                                            return config
                                    else:
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


def docker_io_get_tag(image):
    docker_io_url = 'https://hub.docker.com/v2/repositories/{namespace}/{image}/tags/?page_size={num}'.format(
        namespace=image['namespace'], image=image['name'], num=image['syncPolicy']['num'])

    tag_list = []
    if image['syncPolicy']['type'] == 'latest':
        response = requests.get(docker_io_url).json()
        image_info_list = response['results']
        for image_info in image_info_list:
            tag_list.append(image_info['name'])
    return tag_list


def k8s_gcr_io_get_tag(image):
    if image['namespace']:
        k8s_gcr_io_url = 'https://k8s.gcr.io/v2/{namespaces}/{image}/tags/list'.format(namespaces=image['namespace'],
                                                                                       image=image['name'])
    else:
        k8s_gcr_io_url = 'https://k8s.gcr.io/v2/{image}/tags/list'.format(image=image['name'])
    if image['syncPolicy']['type'] == 'latest':
        response = requests.get(k8s_gcr_io_url).json()
        image_info_dict = response['manifest']
        tag_list = []
        for image_info in image_info_dict.values():
            if image_info['tag'] and not re.search('sha256-[\d\w]*.sig', image_info['tag'][0]):
                upload_time = image_info['timeUploadedMs']
                tag_list.append({'tag': image_info['tag'][0], 'upload_time': upload_time})
        tag_list = sorted(tag_list, key=lambda x: x['upload_time'], reverse=True)
        tag_list = [x['tag'] for x in tag_list][0:image['syncPolicy']['num']]
        return tag_list


def quay_io_get_tag(image):
    quay_io_url = 'https://quay.io/api/v1/repository/{namespaces}/{image}/tag?limit={num}&page={page}&onlyActiveTags=true'.format(
        namespaces=image['namespace'], image=image['name'], num=image['syncPolicy']['num'], page=1)
    tag_list = []
    if image['syncPolicy']['type'] == 'latest':
        response = requests.get(quay_io_url).json()
        image_info_list = response['tags']
        for image_info in image_info_list:
            tag_list.append(image_info['name'])
    return tag_list


if __name__ == '__main__':
    image = {'namespace': 'coreos', 'name': 'flannel', 'source': 'quay.io',
             'target': '[registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync]',
             'syncPolicy': {'type': 'latest', 'num': 10}}
    load_config("../conf/config.yaml")
