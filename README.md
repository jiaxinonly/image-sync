# image-sync 容器镜像同步工具
> 支持k8s.gcr.io docker.io quay.io容器镜像同步到阿里云，腾讯云，华为云，百度智能云

> **个人开发可能会有bug和兼容性问题**

> 目前数据库支持sqlite3, mysql  
> 目前仅支持latest和all同步策略  
> 支持多个配置文件，config-example.yaml配置文件会跳过

## 目前存在的问题: 
因起初设计考虑不够，存在同步多个源镜像仓库需要设置多个重复配置，如：  
将k8s.gcr.io同步到阿里云k8s_gcr_io_sync和将quay.io同步到阿里云quay_io_sync
有三种不优雅的解决方式：
1. 被迫全部同步到一个仓库去（k8s.gcr.io===>阿里云image_sync,quay.io===>阿里云image_sync）
2. 使用单个配置文件，每个image重复配置source和target
3. 使用多个配置文件，每个配置文件重复配置target

## 使用方式
> 需要python3和docker环境
1. 将conf文件夹下config-example文件重命名为config.yaml
2. 根据需求修改配置文件，填写目标仓库账号密码
3. 安装依赖 pip install -r requirements.txt
4. python image-sync.py

## 镜像同步列表

> 仅同步最新的50个tag
> 如果需要同步其他镜像，可以在专属issues留言  
> 
> **镜像拉取示例：**  
> 源库：docker pull k8s.gcr.io/kube-apiserver:v1.24.13  
> 阿里云同步仓库：docker pull registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/kube-apiserver:v1.24.13  
> 华为云同步仓库：docker pull swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/kube-apiserver:v1.24.13  
> 腾讯云同步仓库：docker pull ccr.ccs.tencentyun.com/k8s.gcr.io.sync/kube-apiserver:v1.24.13  
> 百度云同步仓库：docker pull registry.baidubce.com/k8s.gcr.io.sync/kube-apiserver:v1.24.13

|   source   |   命令空间    |          镜像           |                            target                            |
| :--------: | :-----------: | :---------------------: | :----------------------------------------------------------: |
| k8s.gcr.io |               |     kube-apiserver      | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/kube-apiserver<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/kube-apiserver<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/kube-apiserver<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/kube-apiserver |
| k8s.gcr.io |               | kube-controller-manager | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/kube-controller-manager<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/kube-controller-manager<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/kube-controller-manager<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/kube-controller-manager |
| k8s.gcr.io |               |     kube-scheduler      | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/kube-scheduler<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/kube-scheduler<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/kube-scheduler<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/kube-scheduler |
| k8s.gcr.io |               |       kube-proxy        | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/kube-proxy<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/kube-proxy<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/kube-proxy<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/kube-proxy |
| k8s.gcr.io |               |          pause          | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/pause<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/pause<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/pause<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/pause |
| k8s.gcr.io |               |          etcd           | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/etcd<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/etcd<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/etcd<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/etcd |
| k8s.gcr.io |               |         coredns         | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/coredns<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/coredns<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/coredns<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/coredns |
| k8s.gcr.io | ingress-nginx |       controller        | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/ingress-nginx-controller<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/ ingress-nginx/controller<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/coredns/ingress-nginx-controller<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/ingress-nginx/controller |
| k8s.gcr.io | ingress-nginx |  kube-webhook-certgen   | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/ingress-nginx-kube-webhook-certgen<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/ ingress-nginx/kube-webhook-certgen<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/coredns/ingress-nginx-kube-webhook-certgen<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/ingress-nginx/kube-webhook-certgen |
| k8s.gcr.io |               |  defaultbackend-amd64   | 阿里云：registry.cn-hangzhou.aliyuncs.com/k8s_gcr_io_sync/defaultbackend-amd64<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/k8s.gcr.io/defaultbackend-amd64<br />腾讯云：ccr.ccs.tencentyun.com/k8s.gcr.io.sync/defaultbackend-amd64<br />百度云：registry.baidubce.com/k8s.gcr.io.sync/defaultbackend-amd64 |
|  quay.io   |    coreos     |         flannel         | 阿里云：registry.cn-hangzhou.aliyuncs.com/quay_io_sync/coreos-flannel<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/quay.io/coreos/flannel<br />腾讯云：ccr.ccs.tencentyun.com/quay.io.sync/coreos-flannel<br />百度云：registry.baidubce.com/quay.io.sync/coreos/flannel |
| docker.io  |    jenkins    |         jenkins         | 阿里云：registry.cn-hangzhou.aliyuncs.com/quay_io_sync/jenkins-jenkins<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/quay.io/jenkins/jenkins<br />腾讯云：ccr.ccs.tencentyun.com/quay.io.sync/jenkins-jenkins<br />百度云：registry.baidubce.com/quay.io.sync/jenkins/jenkins |
| docker.io  |    jenkins    |      inbound-agent      | 阿里云：registry.cn-hangzhou.aliyuncs.com/quay_io_sync/jenkins-inbound-agent<br />华为云：swr.cn-southwest-2.myhuaweicloud.com/quay.io/jenkins/inbound-agent<br />腾讯云：ccr.ccs.tencentyun.com/quay.io.sync/jenkins-inbound-agent<br />百度云：registry.baidubce.com/quay.io.sync/jenkins/inbound-agent |
