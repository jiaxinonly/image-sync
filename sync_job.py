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
    def __init__(self, image):
        self.image = image
        self.client = docker.from_env()
        if self.image['namespace']:
            self.source_full_image_name = self.image['source'] + '/' + self.image['namespace'] + '/' + self.image[
                'name']
        else:
            self.source_full_image_name = self.image['source'] + '/' + self.image['name']
        print("init")

    def get_tag(self):
        if self.image['source'] == 'docker.io':
            self.tag_list = docker_io_get_tag(self.image)
        elif self.image['source'] == 'k8s.gcr.io':
            self.tag_list = k8s_gcr_io_get_tag(self.image)
        elif self.image['source'] == 'quay.io':
            self.tag_list = quay_io_get_tag(self.image)
        print("get_tag")

    def pull(self):
        for tag in self.tag_list:
            logger.info("拉取镜像" + self.source_full_image_name + ':' + tag)
            self.client.images.pull(self.source_full_image_name, tag)
        print(self.tag_list)
        print("pull")

    def make_tag(self):
        self.target_full_image_name_list = []
        for target in self.image['target']:
            if self.image['alias']:
                if target['type'] in support_subspace_list:
                    target_full_image_name = target['path'] + '/' + self.image['alias']
                else:
                    target_full_image_name = target['path'] + '/' + self.image['alias'].replace('/', '-')
            else:
                if self.image['namespace']:
                    if target['type'] in support_subspace_list:
                        target_full_image_name = target['path'] + '/' + self.image['namespace'] + '/' + self.image[
                            'name']
                    else:
                        target_full_image_name = target['path'] + '/' + self.image['namespace'] + '-' + self.image[
                            'name'].replace('_', '-')
                else:
                    if target['type'] in support_subspace_list:
                        target_full_image_name = target['path'] + '/' + self.image['name']
                    else:
                        target_full_image_name = target['path'] + '/' + self.image['name'].replace('/', '')
            self.target_full_image_name_list.append(target_full_image_name)
            print(self.tag_list)
            for tag in self.tag_list:
                print(target_full_image_name)
                self.client.images.get(self.source_full_image_name + ':' + tag).tag(target_full_image_name + ':' + tag)

        print("make_tag")

    def push(self):
        for target_full_image_name in self.target_full_image_name_list:
            for tag in self.tag_list:
                print("push" + target_full_image_name + ':' + tag)
                d = self.client.images.push(target_full_image_name, tag)
                print(d)
                print("remove" + target_full_image_name + ':' + tag)
                self.client.images.remove(target_full_image_name + ':' + tag)
                print("ok")
        print("push")

    def clear(self):
        for tag in self.tag_list:
            self.client.images.remove(self.source_full_image_name + ':' + tag)
        print("clear")


if __name__ == '__main__':
    image = {'namespace': 'library', 'name': 'centos', 'source': 'docker.io', 'alias': None,
             'target': [{'type': 'aliyun', 'path': 'registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync'}],
             'syncPolicy': {'type': 'latest', 'num': 10}}
    test = SyncJob(image)
    test.get_tag()
    test.pull()
    test.make_tag()
    test.push()
    test.clear()
