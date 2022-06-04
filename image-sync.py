# -*- coding: utf-8 -*-
# File: image-sync.py
# Time: 2022/4/18 21:32
# Author: jiaxin
# Email: 1094630886@qq.com

import sqlite3
from sync_job import SyncJob
import logging
from lib.tool import load_config
import docker

logger = logging.getLogger("image-sync")


class ImageSync:
    def __init__(self):
        self.config = load_config('conf/config.yaml')
        logger.info("初始化配置检查完成。。。")

    def prepare(self):
        if self.config["global"]["database"]["type"] == "sqlite":
            self.connect = sqlite3.connect(self.config["global"]["database"]["dbfile"])
            self.cursor = self.connect.cursor()
            sql = "create table if not exists image_sync_history (" \
                  "id integer primary key autoincrement not null," \
                  "create_time timestamp not null default current_timestamp," \
                  "update_time timestamp not null default current_timestamp," \
                  "source varchar(300) not null," \
                  "namespace varchar(300) not null," \
                  "name varchar(300) not null," \
                  "target_path varchar(300) not null," \
                  "tag varchar(200) not null," \
                  "image_id varchar(100) not null)"
            print(sql)
            self.cursor.execute(sql)
            logger.info("检查数据库完成。。。")
        elif self.config["global"]["database"]["type"] == "mysql":
            sql = "create table if not exists image_sync_history (" \
                  "id int primary key not null auto_increment comment '自增id'," \
                  "create_time timestamp not null default current_timestamp comment '第一次同步时间'," \
                  "update_time timestamp not null default current_timestamp comment '最后一次更新时间'," \
                  "suorce varchar(300) not null comment '同步源'," \
                  "suorce_name varchar(300) not null comment '同步源镜像名'," \
                  "target varchar(300) not null comment '同步目标'," \
                  "target_name varchar(300) not null comment '同步目标镜像名'," \
                  "tag varchar(200) not null comment '镜像tag'," \
                  "image_id varchar(100) not null comment '镜像id')"
            ...

        self.client = docker.from_env()
        for target in self.config["global"]["target"]:
            logger.info("docker login " + target['type'])
            print(target['path'])
            d = self.client.login(str(target['username']), target['password'], registry=target['path'])
            print(d)

    def sync(self):
        for image in self.config["images"]:
            logger.info("同步" + image['name'] + "镜像。。。")
            if not image.get("syncPolicy", None):
                image["syncPolicy"] = self.config["global"]["syncPolicy"]
            if not image.get("source", None):
                image["source"] = self.config["global"]["source"]
            if not image.get("target", None):
                image["target"] = self.config["global"]["target"]
            if not image.get("namespace", None):
                if image['source'] == 'docker.io':
                    image['namespace'] = 'library'
                elif image['source'] == 'k8s.gcr.io':
                    image['namespace'] = None
                elif image['source'] == 'quay.io':
                    image['namespace'] = None
            if not image.get("alias", None):
                image['alias'] = None

            sync_job = SyncJob(image, self.connect, self.cursor)
            sync_job.get_tag()
            sync_job.pull()
            sync_job.make_tag()
            sync_job.push()
            sync_job.clear()


if __name__ == '__main__':
    image_sync = ImageSync()
    image_sync.prepare()
    image_sync.sync()
