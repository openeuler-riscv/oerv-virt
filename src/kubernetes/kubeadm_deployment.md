# 在 oerv 上用 kubeadm 启动 kubernetes
本篇以一个 master 两个 node 为例，示范了如何在 openEuler riscv 上启动一个 kubernetes 集群
## 环境准备

截至目前，在 openEuler riscv 上启动一个 kubernetes 的条件如下：

- 通过 ntp 同步时间
- 配置 /etc/hosts 配置静态解析
- 挂载必要的内核模块
- 修改内核参数
- 关闭 SELinux
- 关闭 Swap
- 关闭 firewalled
- 安装对应职能( master / node )的依赖
- 配置 containerd 的 cgroups 的驱动以及使用的 pause 容器镜像
- 配置 kubelet 启动时 cgroups 驱动的参数

## master 节点配置

首先需要生成一个默认的配置文件，这样子做配置会相对来说方便很多
```shell
kubeadm config print init-defaults > kubeadm.yaml
```
我们这一次只做基本的部署测试，所以我们只修改最有限的参数，主要是两个： advertiseAddress，imageRepository

完成配置后，我们只需要使用下面的指令开始初始化就好了
```shell
kubeadm init --config kubeadm.yaml
```
这里给出一段示例 config
```yaml
apiVersion: kubeadm.k8s.io/v1beta3
bootstrapTokens:
- groups:
  - system:bootstrappers:kubeadm:default-node-token
  token: abcdef.0123456789abcdef
  ttl: 24h0m0s
  usages:
  - signing
  - authentication
kind: InitConfiguration
localAPIEndpoint:
  advertiseAddress: 10.211.102.2 # 我们自己的 advertiseAddress
  bindPort: 6443
nodeRegistration:
  criSocket: unix:///var/run/containerd/containerd.sock
  imagePullPolicy: IfNotPresent
  name: master
  taints: null
---
apiServer:
  timeoutForControlPlane: 4m0s
apiVersion: kubeadm.k8s.io/v1beta3
certificatesDir: /etc/kubernetes/pki
clusterName: kubernetes
controllerManager: {}
dns: {}
etcd:
  local:
    dataDir: /var/lib/etcd
imageRepository: hub.oepkgs.net/ruoqing # 我们目前维护的 kubernetes v1.29.1 的镜像
kind: ClusterConfiguration
kubernetesVersion: 1.29.1
networking:
  dnsDomain: master.local
  serviceSubnet: 10.96.0.0/12
scheduler: {}
```
完成后 kubeadm 会打印出一段指导，跟随指导我们就能够让当前 master 拥有使用 kubectl 的能力，以便我们后面的操作

同时也会有一行用于让 node 加入 master 的指令，当我们需要加入 node 的时候，我们也可以在 master 上使用如下指令来生成加入指令
```shell
kubeadm token create --print-join-command
```
## node 节点配置

node 配置只需要在完成准备环境后输入 master 生成的加入指令就好
```shell
kubeadm join <apiserver host>:<port> --token <master_token> --discovery-token-ca-cert-hash <token_hash> 
```
## 参考环境准备流程
```shell
# 设置 hostname
hostnamectl set-hostname <hostname> # 根据主机名设置

# 设置主机名, 这里需要根据自己的节点的情况进行设置
cat > /etc/hosts << EOF
# Loopback entries; do not change.
# For historical reasons, localhost precedes localhost.localdomain:
127.0.0.1   localhost localhost.localdomain localhost4 localhost4.localdomain4
::1         localhost localhost.localdomain localhost6 localhost6.localdomain6
# See hosts(5) for proper format and other examples:
# 192.168.1.10 foo.example.org foo
# 192.168.1.13 bar.example.org bar
<your_master_ip> master # 设置 master 主机名
<your_node1_ip> node1  # 设置 node1 主机名
<your_node2_ip> node2  # 设置 node2 主机名
EOF

# 设置系统时区
timedatectl set-timezone Asia/Shanghai

# 安装 chrony 同步时间
dnf install -y chrony

# 启用并立即启动 chrony 服务
systemctl enable --now chronyd

# 查看与 chrony 服务器同步的时间源
chronyc sources -v

# 查看当前系统时钟与 chrony 时间源之间的跟踪信息
chronyc tracking

# 强制系统时钟与 chrony 服务器进行快速同步
chronyc -a makestep

# 显示当前正在使用的 swap 分区
swapon --show

# 关闭所有已激活的 swap 分区
swapoff -a

# 禁用系统启动时自动挂载 swap 分区
sed -i '/ swap / s/^\(.*\)$/#\1/g' /etc/fstab

# 临时禁用 SELinux
setenforce 0

# 在重启系统后永久禁用 SELinux
sed -i 's/^SELINUX=.*/SELINUX=disabled/' /etc/selinux/config

# 清除和删除 iptables 规则
iptables -F && iptables -X && iptables -F -t nat && iptables -X -t nat

# 将设置默认的 FORWARD 链策略为 ACCEPT
iptables -P FORWARD ACCEPT

# 停用 firewalld 防火墙服务
systemctl stop firewalld && systemctl disable firewalld

# 导入临时 repo, 后面合并的时候会移除
cat > /etc/yum.repos.d/kube.repo << EOF
[KUBE]
name=KUBE
baseurl=https://build-repo.tarsier-infra.isrc.ac.cn/home:/heruoqing:/branches:/openEuler:/24.03:/Epol/mainline_riscv64/
enabled=1
gpgcheck=0
gpgkey=http://repo.openeuler.org/openEuler-24.03-LTS/OS/$basearch/RPM-GPG-KEY-openEuler
EOF

# 安装统一依赖
dnf install -y containerd socat kubernetes-kubeadm kubernetes-kubelet \
                                cri-tools conntrack ipvsadm containernetworking-plugins

# 安装 master 依赖
dnf install -y kubernetes-master

# 安装 node 依赖
dnf install -y kubernetes-node

# 链接 cni 二进制到 /opt/cni/bin 下
mkdir -p /opt/cni/bin

for bin in `ls /usr/libexec/cni/bin`;
do
  ln -s /usr/libexec/cni/$bin  /opt/cni/bin/$bin
done

# 将默认文件中的 net.ipv4.ip_forward 参数改为 1
sed -i '/net.ipv4.ip_forward =/s/0/1/g' /etc/sysctl.conf

# 添加网桥使用的内核参数
cat > /etc/sysctl.d/kubernetes.conf << EOF
# 允许 IPv6 转发请求通过iptables进行处理（如果禁用防火墙或不是iptables，则该配置无效）
net.bridge.bridge-nf-call-ip6tables = 1
# 允许 IPv4 转发请求通过iptables进行处理（如果禁用防火墙或不是iptables，则该配置无效）
net.bridge.bridge-nf-call-iptables = 1
EOF

# 加载或启动内核模块 br_netfilter，该模块提供了网络桥接所需的网络过滤功能
modprobe br_netfilter

# 查看是否已成功加载模块
lsmod | grep br_netfilter

# 将读取该文件中的参数设置，并将其应用到系统的当前运行状态中
sysctl -p /etc/sysctl.d/kubernetes.conf
sysctl -p /etc/sysctl.conf

# 添加持久化加载的模块
cat > /etc/modules-load.d/kubernetes.conf << EOF
# /etc/modules-load.d/kubernetes.conf
# Linux 网桥支持
br_netfilter

# IPVS 加载均衡器
ip_vs
ip_vs_rr
ip_vs_wrr
ip_vs_sh

# IP 表规则
ip_tables
EOF

# 给予 modules-load 执行权限
chmod a+x /etc/modules-load.d/kubernetes.conf

# 创建一个默认的 containerd 配置文件
containerd config default > /etc/containerd/config.toml

# 设置 containerd 的 systemd cgroups 驱动
sed -i '/SystemdCgroup/s/false/true/' /etc/containerd/config.toml

# 设置 containerd 的 pause 镜像
sed -i 's/registry.k8s.io\/pause:3.6/hub.oepkgs.net\/ruoqing\/pause:3.9/g' /etc/containerd/config.toml

# 启用并立即启动 containerd 服务
systemctl enable --now containerd.service || systemctl restart containerd.service 

# 使用 /etc/default/kubelet 文件来设置 kubelet 的额外参数, 该参数指定了 kubelet 使用 systemd 作为容器运行时的 cgroup 驱动程序
cat > /etc/default/kubelet << EOF
KUBELET_EXTRA_ARGS="--cgroup-driver=systemd"
EOF

# 这里先设置kubelet为开机自启
systemctl enable kubelet
```
