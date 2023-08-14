# -*- coding: utf-8 -*-
# File: sync_job.py
# Time: 2022/4/18 22:30
# Author: jiaxin
# Email: 1094630886@qq.com
from datetime import datetime

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
        self.final_tag = {}
        if self.image['namespace']:
            self.source_full_image_name = self.image['source'] + '/' + self.image['namespace'] + '/' + self.image[
                'name']
        else:
            self.source_full_image_name = self.image['source'] + '/' + self.image['name']

    def start(self):
        self.get_tag()
        for i in range(0, len(self.final_tag), self.image["batch_num"]):
            batch_tag = list(self.final_tag.keys())[i:i + self.image["batch_num"]]
            self.pull(batch_tag)
            self.make_tag(batch_tag)
            self.push(batch_tag)
            self.clear(batch_tag)

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
            sql = "select tag,source_update_time from image_sync_history where source='{}' and namespace='{}' and name='{}' and target_path='{}'".format(
                self.image['source'], self.image['namespace'], self.image['name'], target['path'])
            self.cursor.execute(sql)
            response = self.cursor.fetchall()
            response = {i[0]: i[1] for i in response}
            logger.debug(target['path'] + "同步过的tag列表：" + str(response))
            for tag in self.tag_list:
                # 排除同步过的镜像
                if tag not in response:
                    # 保存需要拉取的镜像tag 只要有一个目的镜像仓库没有同步过，都需要拉一次
                    if tag not in self.final_tag:
                        self.final_tag[tag] = [
                            {'full_image_name': full_image_name, 'path': target['path'], 'tag': tag,
                             'action': "create", "source_update_time": self.tag_list[tag]}]
                    else:
                        self.final_tag[tag].append(
                            {'full_image_name': full_image_name, 'path': target['path'], 'tag': tag,
                             'action': "create", "source_update_time": self.tag_list[tag]})
                else:
                    # 对比更新时间
                    update_time = datetime.strptime(response[tag], "%Y-%m-%d %H:%M:%S.%f")
                    if update_time < self.tag_list[tag]:
                        # 保存需要拉取的镜像tag 只要有一个目的镜像仓库没有同步过，都需要拉一次
                        if tag not in self.final_tag:
                            self.final_tag[tag] = [
                                {'full_image_name': full_image_name, 'path': target['path'], 'tag': tag,
                                 'action': "update", "source_update_time": self.tag_list[tag]}]
                        else:
                            self.final_tag[tag].append(
                                {'full_image_name': full_image_name, 'path': target['path'], 'tag': tag,
                                 'action': "update", "source_update_time": self.tag_list[tag]})
                        logger.debug("tag " + tag + " 有更新")

        logger.debug("过滤后的镜像列表：" + str(self.final_tag))

    # 拉取镜像
    def pull(self, batch_tag):
        logger.info("开始拉取镜像。。。")
        for tag in batch_tag:
            logger.info("拉取镜像" + self.source_full_image_name + ':' + tag)
            # 拉取镜像
            self.client.images.pull(self.source_full_image_name, tag)

    def make_tag(self, batch_tag):
        logger.info("开始标记tag。。。")
        for tag in batch_tag:
            for data in self.final_tag[tag]:
                self.client.images.get(self.source_full_image_name + ':' + tag).tag(
                    data['full_image_name'] + ':' + data['tag'])
                logger.debug(data['full_image_name'] + ':' + data['tag'] + " 标记完成")

    def push(self, batch_tag):
        logger.info("开始push镜像。。。")
        for tag in batch_tag:
            for data in self.final_tag[tag]:
                logger.info("docker push " + data['full_image_name'] + ":" + data['tag'])
                self.client.images.push(data['full_image_name'], data['tag'])
                image_id = self.client.images.get(
                    data['full_image_name'] + ':' + data['tag']).id
                if data['action'] == "create":
                    sql = "insert into image_sync_history (source_update_time, source, namespace, name, target_path, tag, image_id) values ('{}','{}','{}','{}', '{}', '{}', '{}')".format(
                        data['source_update_time'], self.image['source'], self.image['namespace'], self.image['name'],
                        data['path'],
                        data['tag'], image_id)
                else:
                    sql = "update image_sync_history set update_time='{}', source_update_time='{}',image_id='{}' where source='{}' and namespace='{}' and name='{}' and target_path='{}' and tag='{}'".format(
                        datetime.now(), data['source_update_time'], image_id, self.image['source'],
                        self.image['namespace'], self.image['name'], data['path'], data['tag'])
                self.cursor.execute(sql)
                logger.debug("清理镜像 " + data['full_image_name'] + ':' + data['tag'])
                self.client.images.remove(data['full_image_name'] + ':' + data['tag'])
            self.connect.commit()

    # 清理源镜像
    def clear(self, batch_tag):
        logger.info("清除镜像。。。")
        for tag in batch_tag:
            self.client.images.remove(self.source_full_image_name + ':' + tag)


if __name__ == '__main__':
    image = {'namespace': 'library', 'name': 'centos', 'source': 'docker.io', 'alias': None,
             'target': [{'type': 'aliyun', 'path': 'registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync'}],
             'syncPolicy': {'type': 'latest', 'num': 10}}
    test = SyncJob(image, '', '')
    test.start()
    # test.get_tag()
    # test.pull()
    # test.make_tag()
    # test.push()
    # test.clear()
