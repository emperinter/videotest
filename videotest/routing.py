# videotest/routing.py
from django.urls import re_path
import video.consumers

websocket_urlpatterns = [
	re_path(r'ws/video/(?P<v_name>\w+)/$', video.consumers.VideoConsumer.as_asgi())
]
