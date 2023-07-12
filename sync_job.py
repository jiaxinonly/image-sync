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
        logger.info("初始化同步job")
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
        logger.info("获取完整同步tag列表。。。")
        if self.image['source'] == 'docker.io':
            self.tag_list = docker_io_get_tag(self.image)
        elif self.image['source'] == 'k8s.gcr.io':
            self.tag_list = k8s_gcr_io_get_tag(self.image)
        elif self.image['source'] == 'quay.io':
            self.tag_list = quay_io_get_tag(self.image)
        logger.debug("同步镜像列表：" + str(self.tag_list))

        ##############################
        # 处理镜像列表，去掉已经同步过的镜像
        ##############################
        self.tag_set = set()
        self.target_image_list = []
        # 遍历目的镜像仓库，获取需要拉取的镜像tag
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
            # 查询镜像是否已经同步过
            sql = "select tag from image_sync_history where source='{}' and namespace='{}' and name='{}' and target_path='{}'".format(
                self.image['source'], self.image['namespace'], self.image['name'], target['path'])
            self.cursor.execute(sql)
            response = self.cursor.fetchall()
            response = [i[0] for i in response]
            logger.debug(target['path'] + "同步过的tag列表：" + str(response))
            for tag in self.tag_list:
                # 排除同步过的镜像
                if tag not in response:
                    # 保存需要拉取的镜像tag 只要有一个目的镜像仓库没有同步过，都需要拉一次
                    self.tag_set.add(tag)
                    # 保存目的镜像需要推送的tag
                    self.target_image_list.append(
                        {'full_image_name': full_image_name, 'path': target['path'], 'tag': tag})
        logger.debug("过滤后的镜像列表：" + str(self.tag_set))

    # 拉取镜像
    def pull(self):
        logger.info("开始拉取镜像。。。")
        for tag in self.tag_set:
            logger.info("拉取镜像" + self.source_full_image_name + ':' + tag)
            # 拉取镜像
            self.client.images.pull(self.source_full_image_name, tag)

    def make_tag(self):
        logger.info("开始标记tag。。。")
        for target_image in self.target_image_list:
            logger.debug(target_image['full_image_name'] + ':' + target_image['tag'] + " 标记完成")
            self.client.images.get(self.source_full_image_name + ':' + target_image['tag']).tag(
                target_image['full_image_name'] + ':' + target_image['tag'])

    def push(self):
        logger.info("开始push镜像。。。")
        for target_image in self.target_image_list:
            logger.info("docker push " + target_image['full_image_name'] + ":" + target_image['tag'])
            self.client.images.push(target_image['full_image_name'], target_image['tag'])
            image_id = self.client.images.get(
                target_image['full_image_name'] + ':' + target_image['tag']).id
            sql = "insert into image_sync_history (source, namespace, name, target_path, tag, image_id) values ('{}','{}','{}', '{}', '{}', '{}')".format(
                self.image['source'], self.image['namespace'], self.image['name'], target_image['path'],
                target_image['tag'], image_id)
            self.cursor.execute(sql)
            logger.debug("清理镜像 " + target_image['full_image_name'] + ':' + target_image['tag'])
            self.client.images.remove(target_image['full_image_name'] + ':' + target_image['tag'])
        self.connect.commit()

    # 清理源镜像
    def clear(self):
        logger.info("清除镜像。。。")
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
