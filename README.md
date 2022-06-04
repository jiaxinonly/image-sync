# image-sync 容器镜像同步工具
> 支持k8s.gcr.io docker.io quay.io容器镜像同步到阿里云，腾讯云，华为云，百度智能云

> 目前仅支持sqlite3, mysql支持待开发中

> 目前仅支持latest 同步策略且num数字限制还未实现

> 将要完善的功能：yaml配置检查，mysql支持，num限制

## 使用步骤
1. 修改conf文件夹下的实例yaml文件，重命名为config.yaml
2. 安装依赖 pip install -r requirements.txt
3. python images-sync
