![show_send_photo](https://user-images.githubusercontent.com/20177836/179466119-7b9b0082-2da5-4205-9777-e5197360da07.png)

[English](https://github.com/emperinter/videotest/blob/master/README.md) | [中文](https://github.com/emperinter/videotest/blob/master/README_CN.md)

> 最近在尝试搞搞Django的视频传输，最后找到了一个例子（上图是质量调整），怎么说呢，除了运行一段时间就卡住了，其它感觉还好，目前未找到具体卡顿的原因。如需了解完整的代码，欢迎访问如下地址去查看。


# 创建项目

> 建议还是clone完整项目去尝试运行一下,整体描述感觉有点乱。

## requirements

- `requirementx.txt`

```txt
amqp==2.6.1
celery-with-redis==3.0
celery==4.4.7
channels==3.0.5
daphne==3.0.2
django-celery-beat==2.3.0
django-celery==3.3.1
django-cors-headers==3.13.0
django-crispy-forms==1.14.0
django-filter==21.1
django-formtools==2.3
django-import-export==2.6.0
django-redis-sessions==0.6.2
django-reversion==5.0.0
django-simpleui==2022.4.9
django-timezone-field==5.0
django-tinymce==3.4.0
django-utils-six==2.0
Django==3.2
redis==4.3.1
six==1.15.0
```

- install

```shell
pip install -r requirements.txt
```

- 目录结构如图所示

![](https://www.emperinter.info/wp-content/uploads/2022/07/wp_editor_md_76c2bc055add8003beedf9e2052c85d2.jpg)

## 基本文件配置等等

- `asgi.py`配置，用于区分http和websocket的通信路由

```python
"""
ASGI config for videotest project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from . import routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'videotest.settings')

# application = get_asgi_application()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
    	URLRouter(
    		routing.websocket_urlpatterns
    	)
    ),
})
```

- `settings.py`配置，后期websocket通信要用，注意这里用到了`redis`中间件。

```python
# WebSocket
ASGI_APPLICATION = 'videotest.asgi.application'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
            'capacity': 6000,
            'expiry': 30,
        },
    },
}
```

## 路由

- 在project目录下新建立`routing.py`文件，内容如下:

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('video/', include('video.urls')),
]
```

- 配置项目`urls.py`

```python
# videotest/routing.py
from django.urls import re_path
import video.consumers

websocket_urlpatterns = [
	re_path(r'ws/video/(?P<v_name>\w+)/$', video.consumers.VideoConsumer.as_asgi())
]
```

- 配置app的`urls.py`文件

```python
# video/urls.py
from django.urls import path
from . import views

urlpatterns = [
	path('', views.index, name='index'),
	path('<str:v_name>/', views.v_name, name='v_name'),
]
```



## 视图

- 配置websocket的`consumers.py`文件，内容如下

```python
# video/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class VideoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['v_name']
        self.room_group_name = 'video_%s' % self.room_name
        print(self.room_name)
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        print("receive:", text_data)
        # print(1)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'video_message',
                'message': text_data,
            }
        )

    # Receive message from room group
    async def video_message(self, event):
        # print(1)
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))
```

- 视图views.py

```python
from django.shortcuts import render

# Create your views here.
# video/views.py

# Create your views here.
def index(request):
	return render(request, 'video/index.html')

def v_name(request, v_name):
	return render(request, 'video/video.html', {
		'v_name': v_name
	})
```



## 模板

- `settings.py`中模板路径设置

```python
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],  # 主要是这里
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

- video.html

```shell
<!--video.html-->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Video</title>
</head>
<body>

<div align="center">
    <h1>Video</h1>
    <img id="resImg" src="" />
</div>

<script src="http://apps.bdimg.com/libs/jquery/2.1.1/jquery.min.js" ></script>
<script>
        const ws = new WebSocket(
            'ws://'
            + window.location.host
            + '/ws/video/'
            + 'wms'
            + '/'
        );

        ws.onmessage = function(evt) {
            v_data = JSON.parse(evt.data);
            $("#resImg").attr("src", v_data.message);
            //console.log( "Received Message: " + v_data.message);
            // ws.close();
        };

        ws.onclose = function(evt) {
            console.log("Connection closed.");
        };
</script>
</body>
</html>
```

# 部署

## nginx配置

> 这个是必需的，nginx用来接受websocket请求并进行相关的配置。

- config

```txt
user www-data;
worker_processes auto;
pid /run/nginx.pid;
include /etc/nginx/modules-enabled/*.conf;

events {
        worker_connections 768;
        # multi_accept on;
}

http {
        ##
        # Basic Settings
        ##

        sendfile on;
        tcp_nopush on;
        tcp_nodelay on;
        keepalive_timeout 65;
        types_hash_max_size 2048;
        # server_tokens off;

        # server_names_hash_bucket_size 64;
        # server_name_in_redirect off;

        include /etc/nginx/mime.types;
        default_type application/octet-stream;

        ##
        # SSL Settings
        ##

        ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3; # Dropping SSLv3, ref: POODLE
        ssl_prefer_server_ciphers on;

        upstream django {
                server 0.0.0.0:8000;
        }

        upstream wsbackend {
                server 0.0.0.0:8001;
        }

        server {
                listen         81;
                # 这里server_name改成服务器的公网IP
                server_name    127.0.0.1;
                charset UTF-8;
                # 两个日志文件路径随意
                access_log      /var/log/nginx/mysite_access.log;
                error_log       /var/log/nginx/mysite_error.log;

                client_max_body_size 75M;
                client_body_buffer_size 256k;
                proxy_connect_timeout 180;
                proxy_send_timeout 180;
                proxy_read_timeout 180;
                proxy_buffer_size 128k;
                proxy_buffers 32 64k;
                proxy_busy_buffers_size 128k;
                proxy_temp_file_write_size 128k;

                # 通常请求交给uwsgi
                location / {
                        include uwsgi_params;
                        uwsgi_pass django;
                        # uwsgi_read_timeout 2;
                }

                # websocket请求交给daphne
                location /ws {
                        proxy_pass http://wsbackend;

                        proxy_http_version 1.1;
                        proxy_set_header Upgrade $http_upgrade;
                        proxy_set_header Connection "upgrade";

                        proxy_redirect off;
                        proxy_set_header Host $host;
                        proxy_set_header X-Real-IP $remote_addr;
                        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                        proxy_set_header X-Forwarded-Host $server_name;
                }
        }
        access_log /var/log/nginx/access.log;
        error_log /var/log/nginx/error.log;

        gzip on;

        include /etc/nginx/conf.d/*.conf;
        include /etc/nginx/sites-enabled/*;
}
```

- 重载/重启

```shell
service nginx reload
service nginx restart
```

## 项目部署

- 启动awsgi

> 一般装channels会安装，如无则用pip装一下。

```shell
daphne -b 0.0.0.0 -p 8001 videotest.asgi:application
```


### 启动项目

- uwsgi 配置

```config
# mysite_uwsgi.ini file
[uwsgi]

# Django-related settings
# 使用nginx连接时使用
socket = 0.0.0.0:8000

# 不用nginx直接当web服务器使用
# http=0.0.0.0:9000

# 项目根目录的绝对路径
chdir = /mnt/d/PROJECT/videotest

# 相对项目根目录路径的项目中wsgi.py的相对路径
wsgi-file = videotest/wsgi.py

# process-related settings
# master
master = True

# maximum number of worker processes
processes = 8
threads = 4

# ... with appropriate permissions - may be needed
# chmod-socket    = 664
# clear environment on exit
# vacuum = true
pidfile = uwsgi.pid
daemonize = uwsgi.log

buffer-size=3276800
```

- 启动

```shell
uwsgi --ini uwsgi.ini
```

# 测试

- 测试代码

```python
# send_video.py
import asyncio
import websockets
import numpy as np
import cv2
import base64
import time

capture = cv2.VideoCapture(0)
if not capture.isOpened():
    print('quit')
    quit()
ret, frame = capture.read()

encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 1]


# 向服务器端实时发送视频截图
async def send_video(websocket):
    global ret, frame
    # global cam
    while True:
        time.sleep(0.1)

        result, imgencode = cv2.imencode('.jpg', frame, encode_param)
        data = np.array(imgencode)
        img = data.tobytes()
        # base64编码传输
        img = base64.b64encode(img).decode()

        await websocket.send("data:image/jpg;base64," + img)
        ret, frame = capture.read()


async def main_logic():
    async with websockets.connect('ws://127.0.0.1:81/ws/video/wms/') as websocket:
        await send_video(websocket)


asyncio.get_event_loop().run_until_complete(main_logic())
```

- 测试

```shell
python send_video.py
```

# 参考
- [Django channels摄像头实时视频传输](https://blog.csdn.net/weixin_46068920/article/details/116339749)
- [Django-Channels使用和部署](https://www.cnblogs.com/feifeifeisir/p/13743833.html)
- [Django-Channels使用和部署](https://blog.csdn.net/sinat_41292836/article/details/107173795)