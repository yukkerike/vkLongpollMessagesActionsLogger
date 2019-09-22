import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType   
import sqlite3
import os
import json
import signal
import threading
import time
import sys

ACCESS_TOKEN = ""
if len(sys.argv)>1 :
        ACCESS_TOKEN = sys.argv[1]
if ACCESS_TOKEN == "":
        raise Exception("Не задан ACCESS_TOKEN")

def interuppt_handler(signum, frame):
        conn.commit()
        cursor.close()
        tableWatcher.cancel()
        os._exit(0)
signal.signal(signal.SIGINT, interuppt_handler)

def bgWatcher():
        cursor.execute("""DELETE FROM messages WHERE timestamp < ?""", (int(time.time())-86400,))
        conn.commit()

def activityReport(message_id, timestamp, isEdited=False, attachments=None, message=""):
        try:
                peer_name = user_name = oldMessage = oldAttachments = date = fwd = ""
                row = "<tr><td>"
                date = time.ctime(timestamp)
                if not os.path.exists(os.path.join(cwd, "mesAct")):
                        os.makedirs(os.path.join(cwd, "mesAct"))
                if not os.path.exists(os.path.join(cwd, "mesAct", "messages_"+time.strftime("%d%m%y",time.localtime())+".html")):
                        f = open(os.path.join(cwd, "mesAct", "messages_"+time.strftime("%d%m%y",time.localtime())+".html"),'w')
                        f.write("""
<html>
        <head>
                <meta charset="utf-8">
                <script>
                        function spoiler(elem_id) {
                                for (i = 1; i < document.getElementById(elem_id).children.length; i++) {
                                        let data = document.getElementById(elem_id).children[i].getAttribute('data-src');
                                        if (document.getElementById(elem_id).children[i].hidden == !0) {
                                                document.getElementById(elem_id).children[i].removeAttribute("hidden");
                                                if (data !== null) 
                                                        document.getElementById(elem_id).children[i].src = document.getElementById(elem_id).children[i].getAttribute('data-src')
                                        } else {
                                                if (data !== null) 
                                                        document.getElementById(elem_id).children[i].removeAttribute("src");
                                                document.getElementById(elem_id).children[i].hidden = !0
                                        }
                                }
                        }
                </script>
        </head>
        <body>
                <table cellspacing="0" border="1" width="100%" frame="hsides" white-space="pre-wrap">
                </table>
        </body>
</html>""")
                        f.close()
                messagesActivities = open(os.path.join(cwd, "mesAct", "messages_"+time.strftime("%d%m%y",time.localtime())+".html"),'r')
                messagesDump = messagesActivities.read()
                messagesActivities.close()
                messagesActivities = open(os.path.join(cwd, "mesAct", "messages_"+time.strftime("%d%m%y",time.localtime())+".html"),'w')
                cursor.execute("""SELECT * FROM messages WHERE message_id = ?""", (message_id,))
                fetch = cursor.fetchone()
                peer_name = fetch[1]
                user_name = fetch[3]
                if not fetch[5] is None:
                        oldMessage = fetch[5]
                if not fetch[6] is None:
                        oldAttachments = fetch[6]
                elif isEdited and message.find("youtu") != -1:
                        row = None
                        return
                if not fetch[8] is None:
                        fwd = fetch[8]
                row+="""{}</td><td>""".format(str(message_id))
                if fetch[0] > 2000000000:
                        row+="""
<a href='https://vk.com/im?sel=c{}' target="_blank">{}</a>
</td><td>""".format(str(fetch[0]-2000000000),peer_name)
                else:
                        row+="""
<a href='https://vk.com/id{}' target="_blank">{}</a>
</td><td>""".format(str(fetch[0]),peer_name)
                row+="""
<a href='https://vk.com/id{}' target="_blank">{}</a>
</td>""".format(str(fetch[2]),user_name)
                if isEdited:
                        row+="<td><b>Старое </b><br />"
                        if oldMessage != "":
                                row+=oldMessage
                        if oldAttachments != "":
                                oldAttachments=json.loads(oldAttachments)
                                if oldMessage != "":
                                        row+="<br />"
                                row+="""
<div id="{0}_{1}_old" style="display: table;">
        <button id="{0}_{1}_old" onClick="spoiler(this.id)" style="display: table-cell;">Вложения</button>""".format(message_id,timestamp)
                                for i in range(oldAttachments['count']):
                                        urlSplit = oldAttachments['urls'][i].split(".")
                                        if len(urlSplit) < 4: #Сниппет со стороннего сайта
                                                row+="""<a href="{0}" target="_blank" hidden>{0}</a>""".format(oldAttachments['urls'][i])
                                                continue
                                        if len(urlSplit[3].split(",")) == 1:
                                                urlSplit = urlSplit[3]
                                                if urlSplit == "jpg":
                                                        row+="""<img data-src="{}" hidden></img>""".format(oldAttachments['urls'][i])
                                                if urlSplit == "mp3":
                                                        row+="""<audio src="{}" controls hidden></audio>""".format(oldAttachments['urls'][i])
                                        elif len(urlSplit[3].split(",")) == 2:
                                                urlSplit = [".".join(urlSplit[:3]),]+urlSplit[3].split(",")
                                                row+="""
<a href="{}" target="_blank" hidden>Видео
        <img src="{}" loading="lazy"></img>
</a>""".format("../vkGetVideoLink.html?"+urlSplit[2],urlSplit[0]+"."+urlSplit[1])
                                        else:
                                                row+="""<a href="{}" target="_blank" hidden>Документ</a>""".format(oldAttachments['urls'][i])
                                row+="</div>"
                        if fwd != "":
                                if oldMessage != "" or oldAttachments != "":
                                        row+="<br />"
                                row+="""
<div id="{0}_{1}_old_fwd" style="display: table;">
        <button id="{0}_{1}_old_fwd" onClick="spoiler(this.id)" style="display: table-cell;">Пересланные</button><p hidden>""".format(message_id,timestamp)
                                row+="<br />".join("&nbsp;".join(fwd.split(" ")).split("\n"))
                                row+="</p></div>"
                        row+="</td><td><b>Новое </b><br />"
                        if message != "":
                                row+=message
                        if not attachments is None:
                                attachments=json.loads(attachments)
                                if message != "":
                                        row+="<br />"
                                row+="""
<div id="{0}_{1}_new" style="display: table;">
        <button id="{0}_{1}_new" onClick="spoiler(this.id)" style="display: table-cell;">Вложения</button>""".format(message_id,timestamp)
                                for i in range(attachments['count']):
                                        urlSplit = attachments['urls'][i].split(".")
                                        if len(urlSplit) < 4: #Сниппет со стороннего сайта
                                                row+="""<a href="{0}" target="_blank" hidden>{0}</a>""".format(attachments['urls'][i])
                                                continue
                                        if len(urlSplit[3].split(",")) == 1:
                                                urlSplit = urlSplit[3]
                                                if urlSplit == "jpg":
                                                        row+="""<img data-src="{}" hidden></img>""".format(attachments['urls'][i])
                                                if urlSplit == "mp3":
                                                        row+="""<audio src="{}" controls hidden></audio>""".format(attachments['urls'][i])
                                        elif len(urlSplit[3].split(",")) == 2:
                                                urlSplit = [".".join(urlSplit[:3]),]+urlSplit[3].split(",")
                                                row+="""
                                                        <a href="{}" target="_blank" hidden>Видео
                                                        <img src="{}" loading="lazy"></img>
                                                </a>""".format("../vkGetVideoLink.html?"+urlSplit[2],urlSplit[0]+"."+urlSplit[1])
                                        else:
                                                row+="""<a href="{}" target="_blank" hidden>Документ</a>""".format(attachments['urls'][i])
                                row+="</div>"
                        if fwd != "":
                                if message != "" or not attachments is None:
                                        row+="<br />"
                                row+="""
<div id="{0}_{1}_new_fwd" style="display: table;">
        <button id="{0}_{1}_new_fwd" onClick="spoiler(this.id)" style="display: table-cell;">Пересланные</button><p hidden>""".format(message_id,timestamp)
                                row+="<br />".join("&nbsp;".join(fwd.split(" ")).split("\n"))
                                row+="</p></div>"
                        row+="</td><td>"
                        row+=date+"</td>"
                else:
                        row+="<td colspan='2'><b>Удалено </b><br />"
                        if oldMessage != "":
                                row+=oldMessage
                        if oldAttachments != "":
                                oldAttachments=json.loads(oldAttachments)
                                if oldMessage != "":
                                        row+="<br />"
                                row+="""
<div id="{0}_{1}_del" style="display: table;">
        <button id="{0}_{1}_del" onClick="spoiler(this.id)" style="display: table-cell;">Вложения</button>""".format(message_id,timestamp)
                                for i in range(oldAttachments['count']):
                                        urlSplit = oldAttachments['urls'][i].split(".")
                                        if len(urlSplit) < 4: #Сниппет со стороннего сайта
                                                row+="""<a href="{0}" target="_blank" hidden>{0}</a>""".format(oldAttachments['urls'][i])
                                                continue
                                        if len(urlSplit[3].split(",")) == 1:
                                                urlSplit = urlSplit[3]
                                                if urlSplit == "jpg":
                                                        row+="""<img data-src="{}" hidden></img>""".format(oldAttachments['urls'][i])
                                                if urlSplit == "mp3":
                                                        row+="""<audio src="{}" controls hidden></audio>""".format(oldAttachments['urls'][i])
                                        elif len(urlSplit[3].split(",")) == 2:
                                                urlSplit = [".".join(urlSplit[:3]),]+urlSplit[3].split(",")
                                                row+="""
                                                <a href="{}" target="_blank" hidden>Видео
                                                        <img src="{}" loading="lazy"></img>
                                                </a>""".format("../vkGetVideoLink.html?"+urlSplit[2],urlSplit[0]+"."+urlSplit[1])
                                        else:
                                                row+="""<a href="{}" target="_blank" hidden>Документ</a>""".format(oldAttachments['urls'][i])
                                row+="</div>"
                        if fwd != "":
                                if oldMessage != "" or oldAttachments != "":
                                        row+="<br />"
                                row+="""
                                <div id="{0}_{1}_del_fwd" style="display: table;">
                                        <button id="{0}_{1}_del_fwd" onClick="spoiler(this.id)" style="display: table-cell;">Пересланные</button><p hidden>
                                """.format(message_id,timestamp)
                                row+="<br />".join("&nbsp;".join(fwd.split(" ")).split("\n"))
                                row+="</p></div>"
                        row+="</td><td>"
                        row+=date+"</td>"
        except BaseException as e:
                f = open(os.path.join(cwd, 'errorLog.txt'), 'a+')
                f.write(str(e)+" "+row+" "+str(timestamp)+"\n")
                f.close()
        finally:
                if not row is None:
                        row+="</tr>"
                        messagesDump = messagesDump[:1443]+row+messagesDump[1443:]
                        if not attachments is None:
                                attachments = json.dumps(attachments)
                messagesActivities.write(messagesDump)
                messagesActivities.close()
                if isEdited:
                        cursor.execute("""UPDATE messages SET message = ?, attachments = ? WHERE message_id = ?""", (message, attachments, message_id,))
                        conn.commit()


def getAttachments(attachments):
        fwd_messages = None
        try:
                if attachments['fwd_messages'] == []:
                        fwd_messages = json.dumps(attachments['reply_message'],indent=1,ensure_ascii=False,)
                else:
                        fwd_messages = json.dumps(attachments['fwd_messages'],indent=1,ensure_ascii=False,)
        except(KeyError):
                pass
        attachments = attachments['attachments']
        count = len(attachments)
        urls = {'count': count, 'urls':[]}
        for i in range(count):
                type = attachments[i]['type']
                if type == 'photo':
                        urls['urls'].append(attachments[i][type]['sizes'][len(attachments[i][type]['sizes'])-1]['url'])
                elif type == 'sticker':
                        return "sticker", None
                elif type == 'video':
                        urls['urls'].append(attachments[i][type]['photo_320']+","+str(attachments[i][type]['owner_id'])+"_"+str(attachments[i][type]['id'])+"_"+str(attachments[i][type]['access_key']))
                elif type == 'audio_message':
                        urls['urls'].append(attachments[i][type]['link_mp3'])
                elif type == 'poll':
                        urls['count']-=1
                elif type == 'wall':
                        urls['urls'].append("https://vk.com/wall"+str(attachments[i][type]['from_id'])+"_"+str(attachments[i][type]['id']))
                else:
                        urls['urls'].append(attachments[i][type]['url'])
        if urls['count'] == 0:
                urls = None
        else:
                urls = json.dumps(urls,ensure_ascii=False,)
        return urls,fwd_messages

vk_session = vk_api.VkApi(token=ACCESS_TOKEN)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session, wait=60, mode=2, preload_messages=True)

cwd = os.path.dirname(os.path.abspath(__file__))

if not os.path.exists(os.path.join(cwd, "messages.db")):
        conn = sqlite3.connect(os.path.join(cwd, "messages.db"),check_same_thread=False)
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE "messages" (
        "peer_id"	INTEGER NOT NULL,
        "peer_name"	TEXT NOT NULL,
        "user_id"	INTEGER NOT NULL,
        "user_name"	TEXT NOT NULL,
        "message_id"	INTEGER NOT NULL UNIQUE,
        "message"	TEXT,
        "attachments"	TEXT,
        "timestamp"	INTEGER NOT NULL,
        "fwd_messages"  TEXT
)""")
        cursor.execute("""CREATE TABLE "chats_cache" (
        "chat_id"	INTEGER NOT NULL UNIQUE,
        "chat_name"	TEXT NOT NULL
)""")
        cursor.execute("""CREATE TABLE "users_cache" (
        "user_id"	INTEGER NOT NULL UNIQUE,
        "user_name"	TEXT NOT NULL
)""")
        conn.commit()
else:
        conn = sqlite3.connect(os.path.join(cwd, "messages.db"),check_same_thread=False)
        cursor = conn.cursor()

tableWatcher = threading.Thread(target=bgWatcher)
tableWatcher.start()

if not os.path.exists(os.path.join(cwd, "vkGetVideoLink.html")):
        f = open(os.path.join(cwd, 'vkGetVideoLink.html'), 'w')
        f.write("""<!DOCTYPE html>
<html>
        <body>
                <input id="videos"></input>
                <input type="submit" id="submit" value="Отправить">
                <script>
                        let ACCESS_TOKEN = '{}';
                        document.getElementById('submit').onclick = function() {{
                        document.getElementById('submit').disabled = true;
                        var script = document.createElement('SCRIPT');
                        script.src = "https://api.vk.com/method/video.get?v=5.101&access_token=" + ACCESS_TOKEN + "&videos=" + videos.value + "&callback=callbackFunc";
                        document.getElementsByTagName("head")[0].appendChild(script);
                        }}
                        function callbackFunc(result) {{
                        var frame = document.createElement('iframe');
                        frame.src = result.response.items[0]["player"];
                        frame.style = "position:absolute;top:0;left:0;width:100%;height:100%;"
                        document.getElementsByTagName("div")[0].appendChild(frame);
                        }}
                        let videos = document.getElementById('videos');
                        videos.value = document.location.search.slice(1);
                        if (videos.value != "") document.getElementById('submit').click()
                </script>
                <div style="position:relative;padding-top:56.25%;"></div>
        </body>
</html>""".format(ACCESS_TOKEN))
        f.close()



tableWatcher.join()
tableWatcher = threading.Timer(3600,bgWatcher)
tableWatcher.start()
flags = [262144, 131072, 65536, 512, 256, 128, 64, 32, 16, 8, 4, 2, 1]
for event in longpoll.listen():
        peer_name = user_name = message = urls = fwd_messages = None    
        try:
                if event.type == VkEventType.MESSAGE_NEW:
                        if event.attachments != {}:
                                urls,fwd_messages = getAttachments(event.message_data)
                                if urls == "sticker":
                                        continue
                        else:
                                urls = None
                        if event.from_chat:
                                cursor.execute("""SELECT * FROM chats_cache WHERE chat_id = ?""", (event.peer_id,))
                                fetch = cursor.fetchone()
                                if fetch is None:
                                        name = vk_session.method("messages.getChat",{"chat_id":event.peer_id-2000000000})["title"]
                                        cursor.execute("""INSERT INTO chats_cache (chat_id,chat_name) VALUES (?,?)""", (event.peer_id,name,))
                                        conn.commit()
                                        peer_name = name
                                else:
                                        peer_name = fetch[1]
                                cursor.execute("""SELECT * FROM users_cache WHERE user_id = ?""", (event.message_data['from_id'],))
                                fetch = cursor.fetchone()
                                if fetch is None:
                                        name = vk_session.method("users.get",{"user_id":event.message_data['from_id']})[0]
                                        name = name['first_name'] + " " + name['last_name']
                                        cursor.execute("""INSERT INTO users_cache (user_id,user_name) VALUES (?,?)""", (event.message_data['from_id'],name,))
                                        conn.commit()
                                        user_name = name
                                else:
                                        user_name = fetch[1]        
                        elif event.from_user:
                                cursor.execute("""SELECT * FROM users_cache WHERE user_id = ?""", (event.peer_id,))
                                fetch = cursor.fetchone()
                                if fetch is None:
                                        name = vk_session.method("users.get",{"user_id":event.peer_id})[0]
                                        name = name['first_name'] + " " + name['last_name']
                                        cursor.execute("""INSERT INTO users_cache (user_id,user_name) VALUES (?,?)""", (event.peer_id,name,))
                                        conn.commit()
                                        peer_name = name
                                else:
                                        peer_name = fetch[1]
                                cursor.execute("""SELECT * FROM users_cache WHERE user_id = ?""", (event.message_data['from_id'],))
                                fetch = cursor.fetchone()
                                if fetch is None:
                                        name = vk_session.method("users.get",{"user_id":event.message_data['from_id']})[0]
                                        name = name['first_name'] + " " + name['last_name']
                                        cursor.execute("""INSERT INTO users_cache (user_id,user_name) VALUES (?,?)""", (event.message_data['from_id'],name,))
                                        conn.commit()
                                        user_name = name
                                else:
                                        user_name = fetch[1]
                        else:
                            continue
                        if event.message != "":
                                message = event.message
                        else:
                                message = None
                        cursor.execute("""INSERT INTO messages(peer_id,peer_name,user_id,user_name,message_id,message,attachments,timestamp,fwd_messages) VALUES (?,?,?,?,?,?,?,?,?)""",(event.peer_id,peer_name,event.message_data['from_id'],user_name,event.message_id,message,urls,event.timestamp,fwd_messages,))
                        conn.commit()
                elif event.type == VkEventType.MESSAGE_EDIT:
                        cursor.execute("""SELECT * FROM messages WHERE message_id = ?""", (event.message_id,))
                        fetch = cursor.fetchone()
                        if fetch is None:
                                continue
                        if event.attachments != {}:
                                attachments,fwd_messages = getAttachments(event.message_data)
                        else:
                                attachments = None
                        activityReport(event.message_id, int(time.time()), True, attachments, event.text)
                elif event.type == VkEventType.MESSAGE_FLAGS_SET:
                        cursor.execute("""SELECT * FROM messages WHERE message_id = ?""", (event.message_id,))
                        fetch = cursor.fetchone()
                        if fetch is None:
                                continue
                        if event.mask != 4096: #На голосовые сообщения, отправленные владельцем токена, устанавливается маска, равная 4096, чего в норме быть не может. Это ошибочно расценивается, как удаление сообщения.
                                mask = event.mask
                        else:
                                continue
                        messageFlags = []
                        for i in flags:
                                mask-=i
                                if mask < 0:
                                        mask+=i
                                else:
                                        messageFlags.append(i)
                        if (131072 in messageFlags or 128 in messageFlags):
                                activityReport(event.message_id, int(time.time()))
        except BaseException as e:
                f = open(os.path.join(cwd, 'errorLog.txt'), 'a+')
                f.write(str(e)+" "+str(event.message_id)+" "+str(int(time.time()))+"\n")
                f.close()