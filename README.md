# image-sync 容器镜像同步工具
> 支持k8s.gcr.io docker.io quay.io容器镜像同步到阿里云，腾讯云，华为云，百度智能云

> **个人开发可能会有bug和兼容性问题**

> 目前数据库支持sqlite3, mysql

> 目前仅支持latest和all同步策略

> 目前存在的问题：
> 1. 源目标镜像latest更新后不会再次同步

## 使用步骤
> 需要python3和docker环境
1. 将conf文件夹下config-example文件重命名为config.yaml
2. 根据需求修改配置文件，填写目标仓库账号密码
2. 安装依赖 pip install -r requirements.txt
3. python image-sync.py