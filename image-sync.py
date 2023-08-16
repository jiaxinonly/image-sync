# -*- coding: utf-8 -*-
# File: image-sync.py
# Time: 2022/4/18 21:32
# Author: jiaxin
# Email: 1094630886@qq.com
import os
import re
import sqlite3
from sync_job import SyncJob
import logging
from lib.tool import load_config
import docker
from docker.errors import APIError
import pymysql

logger = logging.getLogger("image-sync")


class ImageSync:
    def __init__(self, conf):
        logger.info("开始初始化配置检查。。。")
        self.config = load_config(conf)
        logger.info("初始化配置检查完成。。。")

    # 检查数据库和docker账号
    def prepare(self):
        # 检查数据库表
        if self.config["global"]["database"]["type"] == "sqlite":
            self.connect = sqlite3.connect(self.config["global"]["database"]["dbfile"])
            self.cursor = self.connect.cursor()
            sql = "create table if not exists image_sync_history (" \
                  "id integer primary key autoincrement not null," \
                  "create_time timestamp not null default current_timestamp," \
                  "update_time timestamp not null default current_timestamp," \
                  "source_update_time timestamp not null default current_timestamp," \
                  "source varchar(300) not null," \
                  "namespace varchar(300) not null," \
                  "name varchar(300) not null," \
                  "target_path varchar(300) not null," \
                  "tag varchar(200) not null," \
                  "image_id varchar(100) not null)"
        elif self.config["global"]["database"]["type"] == "mysql":
            self.connect = pymysql.connect(
                host=self.config["global"]["database"]["host"],
                port=self.config["global"]["database"]["port"],
                user=self.config["global"]["database"]["username"],
                password=self.config["global"]["database"]["password"]
            )
            self.cursor = self.connect.cursor()
            # 检查数据库db
            self.cursor.execute('create database if not exists %s' % self.config["global"]["database"]["db"])
            self.connect.select_db(self.config["global"]["database"]["db"])

            sql = "create table if not exists image_sync_history (" \
                  "id int primary key not null auto_increment comment '自增id'," \
                  "create_time timestamp not null default current_timestamp comment '第一次同步时间'," \
                  "update_time timestamp not null default current_timestamp comment '最后一次更新时间'," \
                  "source_update_time timestamp not null default current_timestamp comment '源目标镜像更新时间'," \
                  "source varchar(300) not null comment '同步源'," \
                  "namespace varchar(300) not null comment '同步源命名空间'," \
                  "name varchar(300) not null comment '镜像名'," \
                  "target_path varchar(300) not null comment '同步目标路径'," \
                  "tag varchar(200) not null comment '镜像tag'," \
                  "image_id varchar(100) not null comment '镜像id')"
        self.cursor.execute(sql)
        logger.info("检查数据库完成。。。")

        self.client = docker.from_env()
        for target in self.config["global"]["target"]:
            logger.info("docker login " + target['type'])
            try:
                self.client.login(str(target['username']), target['password'], registry=target['path'])
            except APIError:
                logger.error(target["type"] + "登录失败，请检查账号密码！！！")
                exit()

    def sync(self):
        for image in self.config["images"]:
            logger.info("开始同步" + image['name'] + "镜像。。。")
            # 设置镜像同步策略
            if not image.get("syncPolicy", None):
                image["syncPolicy"] = self.config["global"]["syncPolicy"]
            # 设置latest策略同步数量
            if image["syncPolicy"]["type"] == 'latest' and not image["syncPolicy"].get("num"):
                image['syncPolicy']['num'] = self.config['global']['syncPolicy']['num']
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
            image['batch_num'] = self.config['global']['batch_num']
            sync_job = SyncJob(image, self.connect, self.cursor)
            sync_job.start()


if __name__ == '__main__':
    for file in os.listdir("conf"):
        conf = os.path.join("conf", file)
        if file != "config-example.yaml" and os.path.isfile(conf) and re.search(".*yaml$", file):
            logger.info(file)
            image_sync = ImageSync(conf)
            image_sync.prepare()
            image_sync.sync()
