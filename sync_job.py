# -*- coding: utf-8 -*-
# File: sync_job.py
# Time: 2022/4/18 22:30
# Author: jiaxin
# Email: 1094630886@qq.com
import docker
from lib.tool import docker_io_get_tag, k8s_gcr_io_get_tag, quay_io_get_tag
import logging

logger = logging.getLogger("image-sync")

support_subspace_list = ['huaweicloud', 'baidubce']


class SyncJob:
    def __init__(self, image, connect, cursor):
        logger.debug("init sync job")
        self.image = image
        self.connect = connect
        self.cursor = cursor
        self.client = docker.from_env()
        if self.image['namespace']:
            self.source_full_image_name = self.image['source'] + '/' + self.image['namespace'] + '/' + self.image[
                'name']
        else:
            self.source_full_image_name = self.image['source'] + '/' + self.image['name']

    def get_tag(self):
        logger.debug("get tag")
        if self.image['source'] == 'docker.io':
            self.tag_list = docker_io_get_tag(self.image)
        elif self.image['source'] == 'k8s.gcr.io':
            self.tag_list = k8s_gcr_io_get_tag(self.image)
        elif self.image['source'] == 'quay.io':
            self.tag_list = quay_io_get_tag(self.image)

    def pull(self):
        logger.debug("pull")
        self.tag_set = set()
        self.target_image_list = []
        for target in self.image['target']:
            if self.image['alias']:
                if target['type'] in support_subspace_list:
                    self.target_name = self.image['alias']
                    full_image_name = target['path'] + '/' + self.image['alias']
                else:
                    self.target_name = self.image['alias'].replace('/', '-')
                    full_image_name = target['path'] + '/' + self.image['alias'].replace('/', '-')
            else:
                if self.image['namespace']:
                    if target['type'] in support_subspace_list:
                        self.target_name = self.image['name']
                        full_image_name = target['path'] + '/' + self.image['namespace'] + '/' + self.image[
                            'name']
                    else:
                        self.target_name = self.image['name'] + self.image['namespace'] + '-' + self.image[
                            'name'].replace('_', '-')
                        full_image_name = target['path'] + '/' + self.image['namespace'] + '-' + self.image[
                            'name'].replace('_', '-')
                else:
                    if target['type'] in support_subspace_list:
                        self.target_name = self.image['name']
                        full_image_name = target['path'] + '/' + self.image['name']
                    else:
                        self.target_name = self.image['name'].replace('/', '')
                        full_image_name = target['path'] + '/' + self.image['name'].replace('/', '')
            for tag in self.tag_list:
                sql = "select * from image_sync_history where source='{}' and namespace='{}' and name='{}' and target_path='{}' and tag='{}'".format(
                    self.image['source'], self.image['namespace'], self.image['name'], target['path'], tag)
                self.cursor.execute(sql)
                response = self.cursor.fetchone()
                if response is None:
                    self.tag_set.add(tag)
                    self.target_image_list.append(
                        {'full_image_name': full_image_name, 'path': target['path'], 'tag': tag})
                    self.client.images.get(self.source_full_image_name + ':' + tag).tag(full_image_name + ':' + tag)
        for tag in self.tag_set:
            logger.info("拉取镜像" + self.source_full_image_name + ':' + tag)
            self.client.images.pull(self.source_full_image_name, tag)

    def make_tag(self):
        logger.debug("make tag")
        for target_image in self.target_image_list:
            self.client.images.get(self.source_full_image_name + ':' + target_image['tag']).tag(
                target_image['full_image_name'] + ':' + target_image['tag'])

    def push(self):
        logger.debug("开始push镜像")
        for target_image in self.target_image_list:
            logger.debug("docker push " + target_image['full_image_name'] + ":" + target_image['tag'])
            self.client.images.push(target_image['full_image_name'], target_image['tag'])
            image_id = self.client.images.get(
                target_image['full_image_name'] + ':' + target_image['tag']).id
            sql = "insert into image_sync_history (source, namespace, name, target_path, tag, image_id) values ('{}','{}','{}', '{}', '{}', '{}')".format(
                self.image['source'], self.image['namespace'], self.image['name'], target_image['path'],
                target_image['tag'], image_id)
            self.cursor.execute(sql)
            self.client.images.remove(target_image['full_image_name'] + ':' + target_image['tag'])
        self.connect.commit()

    def clear(self):
        logger.debug("clear")
        for tag in self.tag_set:
            self.client.images.remove(self.source_full_image_name + ':' + tag)


if __name__ == '__main__':
    image = {'namespace': 'library', 'name': 'centos', 'source': 'docker.io', 'alias': None,
             'target': [{'type': 'aliyun', 'path': 'registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync'}],
             'syncPolicy': {'type': 'latest', 'num': 10}}
    test = SyncJob(image, '', '')
    test.get_tag()
    test.pull()
    test.make_tag()
    test.push()
    test.clear()
