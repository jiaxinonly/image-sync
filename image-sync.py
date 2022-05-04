# -*- coding: utf-8 -*-
# File: image-sync.py
# Time: 2022/4/18 21:32
# Author: jiaxin
# Email: 1094630886@qq.com

import sqlite3
from sync_job import SyncJob
import logging
from lib.tool import load_config

logger = logging.getLogger("image-sync")


class ImageSync:
    def __init__(self):
        self.config = load_config('conf/config.yaml')
        logger.info("初始化检查完成")

    def prepare(self):
        logger.info("准备开始同步。。。")
        if self.config["global"]["database"]["type"] == "sqlite":
            connect = sqlite3.connect(self.config["global"]["database"]["dbfile"])
            cursor = connect.cursor()
            sql = "create table image_sync_history (" \
                  "id primary key not null auto_incerment," \
                  "target varchar(300) not null," \
                  "name varchar(150) not null," \
                  "tag varchar(200)) not null)"
            cursor.execute(sql)

        elif self.config["global"]["database"]["type"] == "mysql":
            ...

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
            print(image)
            sync_job = SyncJob(image)
            sync_job.get_tag()
            sync_job.pull()
            sync_job.make_tag()
            sync_job.push()
            sync_job.clear()


if __name__ == '__main__':
    image_sync = ImageSync()
    image_sync.sync()
