# Anti-Hijack Socks5 Server
## 防劫持Socks5服务器
利用将发出的HTTP请求拆分到多个数据包中的原理抑制HTTP劫持。

运营商有时会通过DNS劫持进行非法活动，可以在解决DNS劫持后使用ahjs5s，避免DNS和HTTP的双重劫持。

----------

使用方法：
 1. 安装Python，2.7和3.4版本测试可用
 2. （可选步骤）编辑config.json，配置server_port，默认为1080，即socks5服务的端口
 3. 在命令行下执行python main.py config.json即可开启socks5服务，配合polipo可以转为http代理，之后设置浏览器代理即可

----------

注意：
 1. 通常劫持发生在HTTP，HTTPS一般不会劫持，所以只需要设置HTTP代理即可，无需设置HTTPS代理

----------

参数配置：
 1. `server_port`：socks5代理的端口，默认1080
 2. `send_packet_size`：拆分HTTP请求的单包大小，默认10（字节）：比如HTTP请求为95字节，那么将分10个数据包发送（最后一个数据包为5字节）

其他配置说明待添加。

----------

Windows版集成Python和Polipo，有简单的配置向导，如不会修改配置文件可以尝试使用。双击start_ahjs5s.bat后根据向导提示启动服务后自行打开浏览器。下载链接：
 - windows.7z: https://github.com/lehui99/ahjs5s/releases/tag/0.9
 - windows.7z: http://pan.baidu.com/s/1jG9XeSm

MD5: 8174dc699eb967dbce493044c25c9c51

SHA1: 3714fd80ad7584520e27b7c43863ef4a0b4a9d22
