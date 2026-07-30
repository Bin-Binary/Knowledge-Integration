# Linux 命令记录 - 常用

> 按层级整理 Linux 常用命令，输出为表格形式，包含：按缩写名称、全称、作用、示例、注意事项。

---

## 一、文件与目录管理

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `ls` | list | 列出目录内容 | `ls -lah` 以人类可读格式列出所有文件（含隐藏） | `-a` 含隐藏；`-l` 详细信息；`-h` 易读大小 |
| `cd` | change directory | 切换工作目录 | `cd ~/project` 进入家目录下 project | `cd -` 回到上次目录；`cd ..` 返回上级 |
| `pwd` | print working directory | 显示当前绝对路径 | `pwd` | 无常用参数；脚本中可用 `$PWD` |
| `mkdir` | make directory | 创建目录 | `mkdir -p a/b/c` 递归创建多层目录 | `-p` 父目录不存在时自动创建 |
| `rmdir` | remove directory | 删除空目录 | `rmdir olddir` | 只能删空目录；非空用 `rm -r` |
| `rm` | remove | 删除文件或目录 | `rm -rf build/` 强制递归删除 | `-r` 递归；`-f` 强制；慎用，无回收站 |
| `cp` | copy | 复制文件或目录 | `cp -rv src/ dst/` 递归并显示进度 | `-r` 目录必需；`-i` 覆盖前确认；`-p` 保留属性 |
| `mv` | move | 移动/重命名 | `mv old.txt new.txt` 重命名 | 同分区为重命名不复制；`-i` 覆盖确认 |
| `touch` | touch | 新建空文件 / 更新时间戳 | `touch a.txt` | 文件存在则只更新 mtime |
| `tree` | tree | 树状显示目录结构 | `tree -L 2 -a` 显示 2 层含隐藏 | 需安装；`-L n` 限制层级 |
| `stat` | status | 显示文件/文件系统状态 | `stat a.txt` | 可看 atime/mtime/ctime/inode |
| `file` | file | 识别文件类型 | `file a.out` | 不依赖扩展名，读魔数判断 |
| `ln` | link | 创建链接 | `ln -s /opt/app app` 创建软链接 | `-s` 软链接；软链可跨文件系统，硬链不可 |
| `rename` | rename | 批量重命名 | `rename 's/\.txt$/.md/' *.txt` | CentOS 默认为 C 版语法，Ubuntu 为 Perl 版 |

## 二、文件查看与编辑

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `cat` | concatenate | 查看/拼接文件内容 | `cat -n a.py` 带行号显示 | 大文件用 `less`；`-n` 行号 |
| `tac` | tac (cat 反写) | 反序输出行 | `tac log.txt` | 与 `cat` 行序相反 |
| `nl` | number lines | 带行号显示 | `nl a.py` | 比 `cat -n` 格式选项多 |
| `less` | less | 分页查看（可前可后） | `less +F big.log` 类似 tail -f | `/` 搜索；`q` 退出；`F` 跟踪模式 |
| `more` | more | 分页查看（只能向后） | `more big.txt` | 已被 `less` 取代 |
| `head` | head | 查看开头若干行 | `head -n 50 log` | 默认 10 行；`-n -K` 除最后 K 行外全显示 |
| `tail` | tail | 查看末尾若干行 | `tail -f /var/log/messages` 跟踪 | `-f` 跟踪追加；`--pid=PID` 进程退出后停止 |
| `cut` | cut | 按列/分隔符截取 | `cut -d: -f1 /etc/passwd` | 仅按字节/字符/字段，不支持正则 |
| `paste` | paste | 按列合并文件 | `paste a.txt b.txt` | 默认 Tab 分隔 |
| `sort` | sort | 排序文本行 | `sort -t: -k3 -n /etc/passwd` | `-n` 数字；`-r` 降序；`-u` 去重 |
| `uniq` | unique | 去除相邻重复行 | `sort x \| uniq -c` 统计频次 | 仅相邻行去重，需先 sort |
| `wc` | word count | 统计行/词/字节数 | `wc -l *.py` | `-l` 行；`-w` 词；`-c` 字节 |
| `diff` | difference | 比较文件差异 | `diff -u a.py b.py` | `-u` 统一格式；`-r` 递归比目录 |
| `vim` | Vi IMproved | 文本编辑器 | `vim +42 a.py` 打开跳到 42 行 | `:wq` 存盘退出；`i` 插入；不熟可用 `nano` |
| `nano` | nano | 简单文本编辑器 | `nano a.conf` | `Ctrl+O` 保存，`Ctrl+X` 退出 |

## 三、查找与定位

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `find` | find | 按条件查找文件 | `find . -name "*.log" -mtime -1` | `-mtime -1` 1 天内修改；可用 `-exec` 联动 |
| `locate` | locate | 从预建索引查找 | `locate -i nginx.conf` | 依赖 `updatedb`，非实时 |
| `which` | which | 查可执行文件路径 | `which python3` | 只查 PATH 中的命令 |
| `whereis` | where is | 查命令及源码/手册位置 | `whereis gcc` | 比 which 范围广 |
| `type` | type | 显示命令类型 | `type ll` | 区分别名/内置/外部命令 |
| `grep` | global regex print | 文本搜索 | `grep -rn "TODO" src/` | `-r` 递归；`-n` 行号；`-i` 忽略大小写；`-v` 反向 |
| `egrep` | extended grep | 扩展正则 grep | `egrep "a\|b" x` | 等价 `grep -E`，已不推荐单独使用 |
| `rg` | ripgrep | 高速递归搜索（Rust） | `rg -i "TODO" src` | 需安装；默认忽略 .gitignore |
| `fd` | fd | 现代 find 替代品 | `fd "\.log$" /var` | 需安装；默认正则、忽略隐藏 |
| `awk` | (作者姓氏) | 列处理/报表语言 | `awk -F: '{print $1}' /etc/passwd` | 单引号防 shell 解析；功能强大 |
| `sed` | stream editor | 流编辑器 | `sed -i 's/old/new/g' a.txt` | `-i` 直接改文件，建议先备份 |

## 四、权限与属主

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `chmod` | change mode | 修改权限 | `chmod 755 a.sh` 或 `chmod u+x a.sh` | 数字=ugo；`-R` 递归 |
| `chown` | change owner | 修改属主/组 | `chown user:group a.sh` | 需 root；`-R` 递归 |
| `chgrp` | change group | 修改属组 | `chgrp dev a.sh` | 可被 `chown :group` 替代 |
| `umask` | user mask | 设置默认权限掩码 | `umask 022` | 新文件=666-umask，目录=777-umask |
| `sudo` | super user do | 以管理员执行 | `sudo apt update` | 需在 sudoers 授权；`-i` 进入 root shell |
| `su` | switch user | 切换用户 | `su - deploy` | `-` 加载目标用户环境 |
| `whoami` | who am i | 显示当前用户名 | `whoami` | 等价 `id -un` |
| `id` | identity | 显示用户/组 ID | `id deploy` | 看 uid/gid/附加组 |
| `passwd` | password | 修改密码 | `passwd deploy` | root 可改任意用户；需复杂度 |
| `groups` | groups | 显示用户所属组 | `groups deploy` | 附加组需重新登录生效 |
| `visudo` | visudo | 安全编辑 sudoers | `visudo` | 退出时语法检查，勿直接 vi |
| `setfacl` | set file ACL | 设置文件访问控制列表 | `setfacl -m u:dev:rwx dir/` | 需文件系统支持 acl；`-b` 清除 |
| `getfacl` | get file ACL | 查看 ACL | `getfacl dir/` | 与 setfacl 配套 |
| `chattr` | change attribute | 设置文件扩展属性 | `chattr +i /etc/resolv.conf` | `+i` 不可改（root 也需先去除） |
| `lsattr` | list attribute | 查看扩展属性 | `lsattr a.txt` | 与 chattr 配套 |

## 五、压缩与归档

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `tar` | tape archive | 打包/解包 | `tar -czvf x.tar.gz dir/` | `c` 打包；`x` 解包；`z` gzip；`j` bzip2；`v` 详细 |
| `gzip` | gzip | gzip 压缩/解压 | `gzip big.log` | 原文件被替换为 `.gz`；`-d` 解压 |
| `gunzip` | gunzip | 解压 .gz | `gunzip a.gz` | 等价 `gzip -d` |
| `bzip2` | bzip2 | 高压缩比压缩 | `bzip2 -k big.log` | `-k` 保留原文件；比 gzip 慢 |
| `xz` | xz | LZMA 高压缩比 | `xz -k big.tar` | 压缩率最高，速度最慢 |
| `zip` | zip | ZIP 压缩 | `zip -r x.zip dir/` | 需安装；默认不递归 |
| `unzip` | unzip | 解压 ZIP | `unzip x.zip -d out/` | `-d` 指定目录 |
| `zcat` | zcat | 查看压缩文件内容 | `zcat a.gz` | 不解压直接输出 |
| `zgrep` | zgrep | 在压缩文件中搜索 | `zgrep "ERROR" a.gz` | 避免先解压 |
| `compress` | compress | 早期压缩（LZW） | `compress a.log` | 已淘汰，仅兼容旧系统 |

## 六、进程与任务管理

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `ps` | process status | 查看进程快照 | `ps -ef \| grep nginx` | `-e` 全部；`-f` 详细；BSD 风格用 `aux` |
| `top` | top | 动态进程监控 | `top -d 2 -p 1234` | `M` 按内存排序；`P` 按 CPU；`q` 退出 |
| `htop` | htop | 增强版 top | `htop -t` 树状显示 | 需安装；可鼠标操作 |
| `kill` | kill | 发送信号 | `kill -9 1234` 强杀 | `-15` 优雅退出（默认）；`-9` 强制 |
| `killall` | kill all | 按名杀进程 | `killall -9 nginx` | 会杀所有同名进程 |
| `pkill` | process kill | 按模式杀进程 | `pkill -u dev` 杀用户进程 | 支持按用户/终端/命令名 |
| `jobs` | jobs | 查看后台任务 | `jobs -l` | 仅当前 shell 的任务 |
| `bg` | background | 将任务放后台 | `bg %1` | 配合 Ctrl+Z 暂停后使用 |
| `fg` | foreground | 将任务放前台 | `fg %2` | `%n` 为 jobs 编号 |
| `nohup` | nohangup | 忽略挂断信号运行 | `nohup python train.py &` | 输出默认到 nohup.out；配合 `&` |
| `&` | 后台运行符 | 命令放后台 | `python a.py &` | 终端关闭后可能被杀，用 nohup/systemd |
| `disown` | disown | 移除作业表 | `disown -h %1` | 使进程免受 shell 退出影响 |
| `nice` | nice | 以指定优先级运行 | `nice -n 10 tar czf x.gz big/` | 普通用户只能增大值（降低优先级） |
| `renice` | renice | 调整运行中进程优先级 | `renice -n -5 -p 1234` | 负值需 root |
| `time` | time | 统计命令耗时 | `time make -j` | 输出 real/user/sys |
| `uptime` | uptime | 系统运行时间与负载 | `uptime` | load avg 为 1/5/15 分钟平均 |
| `pidof` | pid of | 查进程 PID | `pidof nginx` | 多实例返回多个 PID |
| `pgrep` | process grep | 按名查 PID | `pgrep -fl python` | `-f` 匹配完整命令行 |
| `lsof` | list open files | 查看打开的文件/端口 | `lsof -i:8080` | 需安装；排查端口占用利器 |
| `strace` | system trace | 跟踪系统调用 | `strace -p 1234 -f` | 性能开销大，调试用 |
| `perf` | performance | 性能分析 | `perf top` | 需内核支持及权限 |

## 七、系统与资源信息

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `uname` | unix name | 显示系统信息 | `uname -a` | `-r` 内核版本 |
| `hostname` | hostname | 显示/设置主机名 | `hostnamectl set-hostname web1` | 永久修改用 hostnamectl |
| `dmesg` | display message | 内核日志 | `dmesg -T` | `-T` 显示人类可读时间 |
| `free` | free | 内存使用 | `free -h -s 2` | `-h` 易读；`-s` 间隔刷新 |
| `df` | disk free | 磁盘使用 | `df -hT` | `-T` 显示文件系统类型 |
| `du` | disk usage | 目录占用 | `du -sh * \| sort -h` | `-s` 汇总；`-h` 易读 |
| `lsblk` | list block | 块设备列表 | `lsblk -f` | 看磁盘/分区/挂载关系 |
| `mount` | mount | 挂载文件系统 | `mount -t nfs srv:/data /mnt` | 需 root；开机挂载写 fstab |
| `umount` | umount | 卸载 | `umount /mnt` | 占用时用 `lsof` 排查 |
| `fdisk` | fixed disk | 分区管理 | `fdisk -l` 列出分区 | 修改分区表危险，先备份 |
| `parted` | parted | 高级分区工具 | `parted /dev/sda print` | 支持 GPT |
| `mkfs` | make filesystem | 创建文件系统 | `mkfs -t ext4 /dev/sdb1` | 会清空数据 |
| `fsck` | filesystem check | 检查修复文件系统 | `fsck -y /dev/sda1` | 需卸载后执行 |
| `dd` | data duplicator | 块级复制 | `dd if=img of=/dev/sdb bs=4M status=progress` | 极易写错盘，反复确认 of= |
| `vmstat` | virtual memory stat | 虚拟内存统计 | `vmstat 1 5` | 1 秒一次共 5 次 |
| `iostat` | I/O stat | 磁盘 I/O 统计 | `iostat -xz 1` | 需 sysstat 包 |
| `sar` | system activity report | 系统活动报告 | `sar -u 1 5` | 需 sysstat；可看历史 |
| `mpstat` | multi-processor stat | CPU 统计 | `mpstat -P ALL 1` | 需 sysstat |
| `nproc` | number of proc | 逻辑 CPU 数 | `nproc` | 快速查看核数 |
| `lscpu` | list cpu | CPU 架构信息 | `lscpu` | 看架构/核数/缓存 |
| `lsmem` | list memory | 内存范围信息 | `lsmem` | 较新发行版才有 |
| `arch` | architecture | 显示机器架构 | `arch` | 等价 `uname -m` |
| `lspci` | list pci | 列出 PCI 设备 | `lspci -v \| grep -i nvidia` | 排查 GPU/网卡 |
| `lsusb` | list usb | 列出 USB 设备 | `lsusb` | 需 usbutils |
| `dmidecode` | DMI decode | 硬件信息（SMBIOS） | `dmidecode -t memory` | 需 root |
| `hwinfo` | hardware info | 硬件信息（详细） | `hwinfo --short` | 需安装 |
| `inxi` | inxi | 硬件信息汇总 | `inxi -F` | 需安装 |
| `sensors` | sensors | 读取温度传感器 | `sensors` | 需 lm-sensors 并 `sensors-detect` |
| `dstat` | dstat | 综合资源监控 | `dstat -tcmdn` | 替代 vmstat/iostat |

## 八、网络

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `ip` | ip | 现代网络配置 | `ip -br a` 简洁查看地址 | 替代 ifconfig；`a`=addr，`r`=route，`l`=link |
| `ifconfig` | interface config | 旧式网络配置 | `ifconfig eth0 up` | 已废弃，部分系统需 net-tools |
| `ping` | ping | ICMP 连通性测试 | `ping -c 4 8.8.8.8` | `-c` 次数；被防火墙屏蔽时无响应 |
| `traceroute` | traceroute | 路由追踪 | `traceroute -n baidu.com` | 需安装；`-n` 不解析域名 |
| `tracepath` | tracepath | 路由追踪（带 MTU） | `tracepath baidu.com` | 无需 root |
| `mtr` | my traceroute | 综合 ping+traceroute | `mtr -n baidu.com` | 需安装；动态更新 |
| `ss` | socket statistics | 查看套接字 | `ss -tlnp` | 替代 netstat；`-t` tcp，`-l` 监听，`-p` 进程 |
| `netstat` | network statistics | 旧式网络统计 | `netstat -tlnp` | 已废弃，建议用 ss |
| `curl` | client URL | HTTP/多协议客户端 | `curl -fsSL https://get.docker.com \| sh` | `-I` 仅头；`-o` 存文件；`-X` 指定方法 |
| `wget` | web get | 下载工具 | `wget -c https://x/a.tar.gz` | `-c` 断点续传；`-r` 递归 |
| `ssh` | secure shell | 远程登录 | `ssh -p 2222 user@host` | `-p` 端口；`-i` 指定密钥 |
| `scp` | secure copy | SSH 复制 | `scp -P 2222 a.txt h:/tmp/` | 大文件/断点续传建议 rsync |
| `rsync` | remote sync | 增量同步 | `rsync -avzP src/ h:/dst/` | 末尾 `/` 含义不同；`--delete` 镜像 |
| `nc` | netcat | 网络瑞士军刀 | `nc -lk 9999` 监听端口 | `-l` 监听；`-k` 持续；可传文件/测端口 |
| `telnet` | telnet | 远程登录/测端口 | `telnet host 3306` | 明文不安全，仅作端口测试 |
| `nslookup` | name server lookup | DNS 查询 | `nslookup baidu.com 8.8.8.8` | 可指定 DNS 服务器 |
| `dig` | domain information groper | 高级 DNS 查询 | `dig +short baidu.com` | 比 nslookup 信息全 |
| `host` | host | 简易 DNS 查询 | `host baidu.com` | 正反向均可 |
| `tcpdump` | tcp dump | 抓包 | `tcpdump -i eth0 -nn port 80` | 需 root；`-w` 存 pcap |
| `nmap` | network mapper | 端口/主机扫描 | `nmap -sS -p 1-1000 host` | 需安装；扫描需授权 |
| `iptables` | iptables | 防火墙规则 | `iptables -L -n -v` | 规则顺序敏感；持久化用 iptables-save |
| `ufw` | uncomplicated firewall | 简化防火墙（Ubuntu） | `ufw allow 22/tcp` | 底层仍为 iptables/nftables |
| `firewall-cmd` | firewalld cli | firewalld 管理 | `firewall-cmd --add-port=80/tcp --permanent` | 需 `--reload` 生效 |

## 九、服务与软件管理

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `systemctl` | system control | 管理 systemd 服务 | `systemctl status nginx` | `start/stop/restart/enable/disable` |
| `service` | service | 旧式服务管理 | `service nginx restart` | 兼容脚本，底层转 systemctl |
| `journalctl` | journal control | 查看 systemd 日志 | `journalctl -u nginx -f` | `-u` 指定单元；`--since today` |
| `apt` | advanced packaging tool | Debian/Ubuntu 包管理 | `apt install -y vim` | `update` 刷索引；`upgrade` 升级 |
| `apt-get` | apt-get | apt 旧版 | `apt-get install vim` | 脚本中推荐用 apt-get |
| `dpkg` | debian package | Debian 底层包管理 | `dpkg -i pkg.deb` | 不处理依赖，需 apt 修复 |
| `yum` | yellowdog updater modified | RHEL/CentOS 包管理 | `yum install -y vim` | 已被 dnf 替代 |
| `dnf` | dandified yum | 新一代 yum | `dnf install -y vim` | CentOS 8+ / Fedora |
| `rpm` | RPM Package Manager | RPM 底层包管理 | `rpm -qa \| grep nginx` | `-q` 查询；不处理依赖 |
| `pip` | pip | Python 包管理 | `pip install -r requirements.txt` | 建议 `--user` 或虚拟环境 |
| `conda` | conda | Conda 环境管理 | `conda create -n dl python=3.10` | 可管理非 Python 依赖 |
| `snap` | snap | Snap 包管理 | `snap install code --classic` | 沙箱化；`--classic` 放开权限 |
| `flatpak` | flatpak | Flatpak 包管理 | `flatpak install flathub org.gimp.GIMP` | 沙箱化跨发行版 |
| `make` | make | 构建管理 | `make -j$(nproc)` | 依赖 Makefile |
| `cmake` | cmake | 构建系统生成器 | `cmake -B build -DCMAKE_BUILD_TYPE=Release` | 生成 Makefile/Ninja |
| `gcc` | GNU compiler collection | C/C++ 编译器 | `gcc -O2 a.c -o a` | `-g` 调试信息；`-Wall` 警告 |
| `g++` | g++ | C++ 编译器 | `g++ -std=c++17 a.cpp -o a` | 同 gcc 体系 |
| `git` | git | 版本控制 | `git clone --depth 1 https://...` | `--depth 1` 浅克隆省流量 |

## 十、用户与登录

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `useradd` | user add | 添加用户 | `useradd -m -s /bin/bash dev` | `-m` 建家目录；不设密码无法登录 |
| `userdel` | user delete | 删除用户 | `userdel -r dev` | `-r` 删家目录；先备份 |
| `usermod` | user modify | 修改用户 | `usermod -aG docker dev` | `-aG` 追加到组，勿漏 `-a` |
| `groupadd` | group add | 添加组 | `groupadd docker` | — |
| `groupdel` | group delete | 删除组 | `groupdel docker` | 不能删用户主组 |
| `who` | who | 查看登录用户 | `who` | 看终端与登录时间 |
| `w` | w | 查看登录用户活动 | `w` | 比 who 更详细，含负载 |
| `last` | last | 登录历史 | `last -n 20` | 读 /var/log/wtmp |
| `lastlog` | last log | 各用户最后登录 | `lastlog` | 读 /var/log/lastlog |
| `wall` | write all | 广播消息 | `wall "维护通知"` | 所有终端可见 |
| `write` | write | 给指定终端发消息 | `write dev pts/1` | 需对方 mesg y |
| `mesg` | message | 控制是否接收消息 | `mesg n` | `n` 拒绝，`y` 接收 |
| `login` | login | 登录 | `login -f dev` | 通常由 getty 调用 |
| `logout` | logout | 注销 | `logout` | 等价 `exit` |

## 十一、文本处理与三剑客

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `awk` | (Aho Weinberger Kernighan) | 列处理/编程语言 | `awk '{sum+=$1} END{print sum}' a` | 单引号防 shell；FS/OFS 设分隔符 |
| `sed` | stream editor | 流编辑 | `sed -n '10,20p' a` 打印 10-20 行 | `-n` 安静模式；`-i` 原地改 |
| `grep` | global regex print | 文本搜索 | `grep -E "err\|warn" log` | `-E` 扩展正则；`-o` 仅输出匹配部分 |
| `tr` | translate | 字符转换/删除 | `tr 'a-z' 'A-Z' < a.txt` | 只能从 stdin 读 |
| `xargs` | xargs | 从 stdin 构建命令参数 | `find . -name "*.py" \| xargs wc -l` | 文件名含空格用 `-d '\n'` 或 `-0` |
| `tee` | tee | 双向输出 | `cmd \| tee out.log \| grep ERR` | `-a` 追加 |
| `envsubst` | env substitute | 环境变量替换 | `envsubst < tpl.conf > app.conf` | 需 gettext；`$$` 转义 |
| `column` | column | 列对齐美化 | `column -t -s: /etc/passwd` | `-t` 表格化 |
| `seq` | sequence | 生成数字序列 | `seq -w 1 10` 补零 | `-w` 等宽 |
| `yes` | yes | 重复输出字符串 | `yes \| rm -i *.tmp` | 用于自动应答 |
| `rev` | reverse | 反转每行字符 | `echo "abc" \| rev` → `cba` | 按字符反转 |
| `fold` | fold | 折行 | `fold -w 80 a.txt` | `-w` 宽度 |
| `fmt` | format | 段落格式化 | `fmt -w 72 a.txt` | 优于 fold，按词折行 |
| `pr` | print | 分页格式化 | `pr -n a.txt` | 用于打印排版 |
| `expand` | expand | Tab 转空格 | `expand -t 4 a.py` | 与 unexpand 相反 |
| `iconv` | iconv | 编码转换 | `iconv -f GBK -t UTF-8 a.txt > b.txt` | `-l` 列出编码 |
| `dos2unix` | dos to unix | CRLF 转 LF | `dos2unix a.sh` | 跨平台脚本常见；需安装 |
| `shuf` | shuffle | 随机打乱 | `shuf -n 10 data.csv` | 抽样常用 |

## 十二、磁盘与文件系统进阶

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `blkid` | block id | 查块设备 UUID/类型 | `blkid /dev/sda1` | 用于 fstab |
| `findmnt` | find mount | 查找挂载信息 | `findmnt /data` | 比 mount 输出清晰 |
| `df` | disk free | 文件系统使用 | `df -i` 查看 inode 使用 | inode 满也会报 No space |
| `duf` | duf | 美化版 df | `duf` | 需安装（Go） |
| `ncdu` | NCurses disk usage | 交互式 du | `ncdu /` | 需安装；快速定位大文件 |
| `fstrim` | filesystem trim | SSD TRIM | `fstrim -v /` | 仅 SSD；支持 discard 挂载选项 |
| `hdparm` | hdparm | 硬盘参数 | `hdparm -tT /dev/sda` | 测速；某些选项危险 |
| `smartctl` | smart control | SMART 健康检测 | `smartctl -a /dev/sda` | 需 smartmontools |
| `md5sum` | MD5 sum | 计算/校验 MD5 | `md5sum *.iso > md5.txt` | 用于完整性校验 |
| `sha256sum` | SHA256 sum | 计算/校验 SHA256 | `sha256sum -c sha256.txt` | 比 MD5 安全 |
| `split` | split | 分割文件 | `split -b 1G big.tar part_` | `-d` 数字后缀；`-l` 按行 |
| `csplit` | context split | 按内容分割 | `csplit a.log /^ERROR/ {*}` | 按模式切分 |

## 十三、日期与时间

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `date` | date | 显示/设置日期 | `date -u +%Y%m%d-%H%M%S` | `-u` UTC；`+%F` 等格式串 |
| `cal` | calendar | 日历 | `cal -3` 显示前当后三月 | `ncal` 竖排 |
| `timedatectl` | timedatectl | 时区/时间管理 | `timedatectl set-timezone Asia/Shanghai` | systemd 提供 |
| `clock` | clock | 硬件时钟（同 hwclock） | `clock -r` | `/etc/adjtime` |
| `hwclock` | hardware clock | 硬件时钟 | `hwclock --systohc` | 同步系统时钟到硬件 |
| `sleep` | sleep | 延迟 | `sleep 1.5` | 支持小数；`s/m/h/d` 单位 |
| `watch` | watch | 周期执行命令 | `watch -n 1 nvidia-smi` | `-n` 间隔；`-d` 高亮变化 |
| `at` | at | 一次性定时任务 | `echo "reboot" \| at 03:00` | 需 atd 服务 |
| `crontab` | cron table | 周期定时任务 | `crontab -e` | 格式 `分 时 日 月 周 命令` |
| `chronyc` | chrony client | NTP 同步查询 | `chronyc tracking` | 替代 ntpd |
| `ntpdate` | ntp date | 一次性 NTP 同步 | `ntpdate ntp.aliyun.com` | 已被 chronyd 取代 |

## 十四、Shell 与脚本

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `echo` | echo | 输出字符串 | `echo -e "a\tb"` | `-e` 解释反斜杠；`-n` 不换行 |
| `printf` | printf | 格式化输出 | `printf "%-10s %d\n" a 1` | 比 echo 可移植 |
| `read` | read | 读取输入 | `read -p "Name: " name` | `-s` 隐藏输入；`-t` 超时 |
| `alias` | alias | 命令别名 | `alias ll='ls -lah'` | 持久化写 ~/.bashrc |
| `unalias` | unalias | 删除别名 | `unalias ll` | — |
| `export` | export | 导出环境变量 | `export PATH=$PATH:/opt/bin` | 仅当前 shell 及子进程有效 |
| `source` | source | 在当前 shell 执行脚本 | `source ~/.bashrc` | 等价 `.` |
| `env` | environment | 显示/设置环境 | `env \| grep PATH` | `-i` 清空环境启动 |
| `set` | set | 设置 shell 选项/位置参数 | `set -euo pipefail` | 脚本健壮性常用 |
| `unset` | unset | 删除变量 | `unset MY_VAR` | — |
| `declare` | declare | 声明变量属性 | `declare -i n=10` | `-r` 只读；`-a` 数组 |
| `history` | history | 命令历史 | `history 20 \| grep ssh` | `!n` 执行第 n 条；`!!` 上一条 |
| `man` | manual | 查看手册 | `man 5 crontab` | 数字指定章节 |
| `tldr` | tldr | 简明示例手册 | `tldr tar` | 需安装；社区维护 |
| `info` | info | GNU 信息手册 | `info coreutils` | 比 man 更详细但较少用 |
| `help` | help | 查看内置命令帮助 | `help cd` | 仅对 shell 内置命令有效 |
| `type` | type | 命令类型 | `type -a ls` | 区分别名/函数/内置/外部 |
| `bash` | Bourne Again Shell | 默认 shell | `bash -x script.sh` 调试 | `-n` 语法检查 |
| `sh` | sh | POSIX shell | `sh script.sh` | 通常是 bash/dash 的链接 |
| `test` | test | 条件测试 | `test -f a.txt && echo ok` | 等价 `[ ]` |
| `expr` | expression | 表达式求值 | `expr 3 + 4` | 运算符前后需空格 |
| `bc` | basic calculator | 任意精度计算器 | `echo "scale=3; 10/3" \| bc` | 默认整数，需 scale |
| `xargs` | xargs | 参数构建 | `cat list \| xargs -n1 -P4 curl` | `-P` 并发 |

## 十五、安全与加密

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `ssh-keygen` | ssh key generator | 生成 SSH 密钥 | `ssh-keygen -t ed25519 -C "me@x"` | ed25519 更安全更快 |
| `ssh-copy-id` | ssh copy id | 分发公钥 | `ssh-copy-id user@host` | 免密登录前提 |
| `ssh-agent` | ssh agent | SSH 密钥代理 | `eval $(ssh-agent)` | 配合 ssh-add |
| `ssh-add` | ssh add | 加载密钥到 agent | `ssh-add ~/.ssh/id_ed25519` | — |
| `openssl` | OpenSSL | SSL/TLS 工具箱 | `openssl rand -hex 16` | 生成随机/证书/哈希 |
| `gpg` | GNU Privacy Guard | 加密/签名 | `gpg -c secret.txt` | 对称加密用 `-c` |
| `md5sum` | MD5 sum | MD5 校验 | `md5sum a.iso` | 不再用于安全场景 |
| `sha256sum` | SHA256 sum | SHA256 校验 | `sha256sum a.iso` | 推荐用于完整性 |
| `base64` | base64 | Base64 编解码 | `echo -n "abc" \| base64` | `-d` 解码 |
| `chmod` | change mode | 权限设置 | `chmod 700 ~/.ssh` | 私钥目录需 700 |
| `chage` | change age | 密码老化策略 | `chage -M 90 dev` | `-l` 查看策略 |
| `fail2ban-client` | fail2ban | 防暴力破解 | `fail2ban-client status sshd` | 需安装并配置 |
| `auditctl` | audit control | 内核审计规则 | `auditctl -w /etc/passwd -p wa` | 需 auditd |

## 十六、其他实用工具

| 缩写名称 | 全称 | 作用 | 示例 | 注意事项 |
| --- | --- | --- | --- | --- |
| `screen` | screen | 终端复用器 | `screen -S train` | 断开后可 `screen -r` 恢复 |
| `tmux` | terminal multiplexer | 终端复用器 | `tmux new -s dev` | `Ctrl+b d` 脱离；`tmux a -t dev` 恢复 |
| `tput` | terminal put | 终端能力操作 | `tput setaf 2` 设绿色 | 脚本着色用 |
| `stty` | set tty | 终端设置 | `stty -echo` 关闭回显 | `stty sane` 恢复 |
| `reset` | reset | 重置终端 | `reset` | 终端乱码时使用 |
| `clear` | clear | 清屏 | `clear` | `Ctrl+L` 等价 |
| `history` | history | 命令历史 | `history -c` 清空 | 持久化在 ~/.bash_history |
| `fortune` | fortune | 随机格言 | `fortune` | 需安装 |
| `cowsay` | cowsay | 牛说话 | `cowsay "hi"` | 需安装；趣味 |
| `figlet` | figlet | ASCII 艺术字 | `figlet Hi` | 需安装 |
| `jq` | jq | JSON 处理器 | `jq '.data[] \| .id' a.json` | 需安装；JSON 的 sed/awk |
| `yq` | yq | YAML/JSON 处理器 | `yq '.a.b' config.yaml` | 需安装 |
| `xmlstarlet` | xmlstarlet | XML 处理 | `xmlstarlet sel -t -m '//item' ...` | 需安装 |
| `parallel` | GNU parallel | 并行执行 | `parallel -j4 wget ::: url1 url2` | 比 xargs 功能强 |
| `entr` | entr | 文件变更触发命令 | `ls *.py \| entr pytest` | 需安装；TDD 利器 |
| `fzf` | fuzzy finder | 模糊查找 | `history \| fzf` | 需安装；`Ctrl+R` 集成 |
| `bat` | bat | cat 增强版 | `bat -A a.py` | 需安装；语法高亮 |
| `exa` / `eza` | exa/eza | ls 增强版 | `eza -lh --git` | 需安装；彩色 |
| `delta` | delta | diff 美化器 | `git diff \| delta` | 需安装；配 git |
| `direnv` | direnv | 目录环境 | `.envrc` 中 `export FOO=bar` | 需 hook shell |
| `mc` | midnight commander | 文件管理器 | `mc` | TUI 文件管理 |
| `tig` | tig | TUI git | `tig` | 浏览 git 历史 |
| `lazygit` | lazygit | TUI git | `lazygit` | 需安装 |
| `ncdu` | ncurses du | 磁盘分析 | `ncdu /var` | 交互式找大文件 |
| `progress` | progress | 显示 coreutils 进度 | `progress -M` | 监控 cp/dd/tar 进度 |

---

## 附：常见组合速查

| 场景 | 命令组合 |
| --- | --- |
| 查找并删除 7 天前的日志 | `find /var/log -name "*.log" -mtime +7 -delete` |
| 统计目录下各类型文件数 | `find . -type f \| sed 's/.*\.//' \| sort \| uniq -c \| sort -rn` |
| 批量替换文件内容 | `grep -rl "old" . \| xargs sed -i 's/old/new/g'` |
| 查看占用 8080 端口的进程 | `lsof -i:8080` 或 `ss -ltnp \| grep 8080` |
| 监控 GPU | `watch -n 1 nvidia-smi` |
| 解压任意格式 | `tar -xvf x.tar.*`（自动识别） |
| 快速 HTTP 服务 | `python3 -m http.server 8000` |
| 不落地下载并执行 | `curl -fsSL url \| bash` |
| 批量压缩日志 | `find . -name "*.log" -exec gzip {} +` |
| 清理 Docker 占用 | `docker system prune -af --volumes` |
| 历史命令去重统计 | `history \| awk '{print $2}' \| sort \| uniq -c \| sort -rn \| head` |
| 查看内存占用前 10 进程 | `ps aux --sort=-%mem \| head -11` |
| SSH 隧道（本地转发） | `ssh -L 8080:localhost:80 user@host` |
| 将命令输出存日志同时显示 | `cmd 2>&1 \| tee run.log` |

---
