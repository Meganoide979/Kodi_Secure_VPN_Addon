import xbmcaddon
import xbmcgui
import xbmcplugin
import os
import getpass
import sys
import telnetlib
import urllib,urllib2,re
import socket


HOST = "192.168.1.1"
user = "root"
password = "admin"
addon_id = 'plugin.program.securevpn'
icon = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id, 'icon.png'))
fanart = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id , 'fanart.jpg'))
fanart_france = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id , 'france.png'))
fanart_italy = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id , 'italy.png'))
addon_handle = int(sys.argv[1])


def connect():
	global tn
	tn = telnetlib.Telnet(HOST)
	tn.read_until("login: ")
	tn.write(user + "\n")
	if password:
		tn.read_until("Password: ")
		tn.write(password + "\n")
	return tn

	
def index():
    addDir('[B][COLOR black]VPN Status[/COLOR][/B]','url',1,icon,'',fanart)
    addDir('[B][COLOR black]Restart the VPN [/COLOR][/B]','url',2,icon,'',fanart)
    addDir('[B][COLOR black]Change country [/COLOR][/B]','url',3,icon,'',fanart)
    addDir('[B][COLOR black]Move VPN to France [/COLOR][/B]','url',6,fanart_france,'',fanart_france)
    addDir('[B][COLOR black]Move VPN to Italy [/COLOR][/B]','url',7,fanart_italy,'',fanart_italy)
    addDir('[B][COLOR black]Move VPN to UltraFastTV [/COLOR][/B]','url',8,icon,'',fanart)
 
def command_via_telnet(command):
    global status
    connect()
    tn.write(command)
    tn.write("exit\n")
    status = tn.read_all()
    return status

def get_params():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
                               
        return param


               
def addDir(name,url,mode,iconimage,description,fanart):
        u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)+"&description="+str(description)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, 'plot': description } )
        liz.setProperty('fanart_image', fanart)
        ok=xbmcplugin.addDirectoryItem(handle=addon_handle,url=u,listitem=liz,isFolder=True)
        return ok 

		
def country_menu():
    alist = [ ]
    cert_directory = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id, 'certificates'))
    for file in os.listdir(cert_directory):
        if file.endswith(".crt"):
           alist.append(file[:2])
    country_code = set(alist)
    i=1
    country_code_dict = {}
    for code in sorted(country_code):
        country_code_dict [i] = code
        url=code
        addDir('[B][COLOR black]'+ code +'[/COLOR][/B]',url,4,icon,'',fanart)
        i += 1
		
def key_filename_menu(code_country):
    certificate_filename = {}
    cert_directory = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id, 'certificates'))
    for file in os.listdir(cert_directory):
        if file.startswith(code_country) and file.endswith(".crt"):
            url = str(file)
            addDir('[B][COLOR black]'+ file +'[/COLOR][/B]',url,5,icon,'',fanart)
			
			
def copy_certificate(certificate_filename):
    global key_ca
    cert_directory = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id, 'certificates/'))
    ca = open (cert_directory+certificate_filename)
    key_file = certificate_filename.strip("_ca.crt")
    key = open (cert_directory+key_file+"_tls.key")
    hostname = certificate_filename.strip("_nordvpn_com_ca.crt")
    ipaddr = socket.gethostbyname(hostname+".nordvpn.com")
    key_ca = {'ca':ca.read(), 'key':key.read(), 'ip':ipaddr}
    return key_ca
 
def change_config_file(ipaddr):
    configuration = ""
    cert_directory = xbmc.translatePath(os.path.join('special://home/addons/' + addon_id))
    config_file = open (cert_directory+"/openvpn.conf")
    for line in config_file.readlines():
        if line.startswith("remote"):
            configuration += "remote "+ipaddr+" 1194\n"
        else:
            configuration += line
    return configuration 

	
params=get_params(); url=None; name=None; mode=None; site=None

try: site=urllib.unquote_plus(params["site"])
except: pass
try: url=urllib.unquote_plus(params["url"])
except: pass
try: name=urllib.unquote_plus(params["name"])
except: pass
try: mode=int(params["mode"])
except: pass 



if mode==None or url==None or len(url)<1: index()
elif mode==1:
    command_via_telnet("/etc/openvpnstate.sh \n")
    if "SUCCESS" in status:
        addDir('[B][COLOR black] The VPN is connected. Enjoy! :) [/COLOR][/B]','','',icon,'',fanart)
        output="The VPN is connected!"
    else:
        addDir('[B][COLOR black] The VPN is down. Damn! :( [/COLOR][/B]','','',icon,'',fanart)
        output="The VPN is down!"
elif mode==2: 
    command_via_telnet("killall openvpn;sleep 5;openvpn --config /tmp/openvpncl/openvpn.conf --daemon \n")
    addDir('[B][COLOR black] The VPN is restarted! Enjoy! :)[/COLOR][/B]','','',icon,'',fanart)
elif mode==3:
    country_menu()
elif mode==4:
    key_filename_menu(url)
elif mode==5:
    copy_certificate(url)
    configuration=change_config_file(key_ca['ip'])
    command_via_telnet("killall openvpn;echo '"+key_ca['ca']+"'> /tmp/openvpncl/ca.crt; echo '"+key_ca['key']+"'> /tmp/openvpncl/ta.key;echo '"+configuration+"'> /tmp/openvpncl/openvpn.conf;sleep 10;openvpn --config /tmp/openvpncl/openvpn.conf --daemon;sleep 10 \n")
    addDir('[B][COLOR black] The VPN is changed to '+url+'! Enjoy! :)[/COLOR][/B]','','',icon,'',fanart)
elif mode==6:
    copy_certificate("fr3_nordvpn_com_ca.crt")
    configuration=change_config_file(key_ca['ip'])
    command_via_telnet("killall openvpn;echo '"+key_ca['ca']+"'> /tmp/openvpncl/ca.crt; echo '"+key_ca['key']+"'> /tmp/openvpncl/ta.key;echo '"+configuration+"'> /tmp/openvpncl/openvpn.conf;sleep 10;openvpn --config /tmp/openvpncl/openvpn.conf --daemon;sleep 10 \n")
    addDir('[B][COLOR black] The VPN is changed to France! Enjoy! :)[/COLOR][/B]','','',icon,'',fanart)
elif mode==7:
    copy_certificate("it3_nordvpn_com_ca.crt")
    configuration=change_config_file(key_ca['ip'])
    command_via_telnet("killall openvpn;echo '"+key_ca['ca']+"'> /tmp/openvpncl/ca.crt; echo '"+key_ca['key']+"'> /tmp/openvpncl/ta.key;echo '"+configuration+"'> /tmp/openvpncl/openvpn.conf;sleep 10;openvpn --config /tmp/openvpncl/openvpn.conf --daemon;sleep 10 \n")
    addDir('[B][COLOR black] The VPN is changed to Italy! Enjoy! :)[/COLOR][/B]','','',icon,'',fanart)
elif mode==8:
    copy_certificate("us321_nordvpn_com_ca.crt")
    configuration=change_config_file(key_ca['ip'])
    command_via_telnet("killall openvpn;echo '"+key_ca['ca']+"'> /tmp/openvpncl/ca.crt; echo '"+key_ca['key']+"'> /tmp/openvpncl/ta.key;echo '"+configuration+"'> /tmp/openvpncl/openvpn.conf;sleep 10;openvpn --config /tmp/openvpncl/openvpn.conf --daemon;sleep 10 \n")
    addDir('[B][COLOR black] The VPN is changed to UltraFastTV! Enjoy! :)[/COLOR][/B]','','',icon,'',fanart)


xbmcplugin.endOfDirectory(int(sys.argv[1]))