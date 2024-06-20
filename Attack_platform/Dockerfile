FROM kalilinux/kali-rolling

WORKDIR /root

# Fix kali source repositories list
RUN echo "deb http://http.kali.org/kali kali-rolling main contrib non-free" > '/etc/apt/sources.list'
RUN echo "deb-src http://http.kali.org/kali kali-rolling main contrib non-free" >> '/etc/apt/sources.list'
RUN echo "deb http://kali.cs.nctu.edu.tw/kali kali-rolling main non-free contrib" >> '/etc/apt/sources.list'
# update --fix-missing ==> Update base kali linux image
RUN apt update --fix-missing
# full-upgrade -y ==> Upgrade metapackages of kali linux image
RUN apt full-upgrade -y
# iputils-ping ==> Ping command to check network is isolated (ping google.es fails)
RUN apt install -y iputils-ping
# nmap ==> Reconnaisance of plcs
RUN apt install -y nmap
# ruby-full ==> Install modbus-cli
RUN apt install -y ruby-full
# modbus-cli ==> Read-write values (espionage and alteration, but easily noticeable)
RUN gem install modbus-cli
# dsniff ==> Arp-spoofing (MITM: espionage and alteration, less noticeable)
RUN apt install -y dsniff
# hping3 ==> Tcp SYN Flood Attack (DDos) and Tcp RST or FIN attacks to end connections
RUN apt install -y hping3
# kali-desktop-xfce ==> Kali desktop GUI
RUN apt-get install -y kali-desktop-xfce
# xrdp ==> Remote desktop connection for Linux
RUN apt install -y xrdp

# IF YOU WANT TO ACCESS KALI LINUX GUI:
# Uncomment text about host_net inside compose file in this directory and relaunch project with docker compose up -d
# Establish a new password with command: passwd <Whatever you want>
# From cli run command: service xrdp start (service xrdp stop after finishing connection, may take up to a minute)
# From host use xrdp client (remote desktop native app for Windows) name:localhost:3389 user:root password:<Whatever you used>