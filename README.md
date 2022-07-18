# Description

> Django channels camera live video transmission

# Usage

## SetUp Enviorments

> Just for reference, here is the list of enviorments that I used to build this project:

```shell
pip install -r requirements.txt
```

## SetUp Redis

```shell
docker pull redis
docker run -d -p 6379:6379 --name redis redis
```

## SetUp Nginx

- install

```shell
yum install nginx -y
```

- nginx config

you can see  it here:[https://github.com/emperinter/videotest/blob/master/nginx.conf](https://github.com/emperinter/videotest/blob/master/nginx.conf)

- restart nginx

```shell
service nginx reload
service nginx restart
```


# SetUp Daphne

```shell
daphne -b 0.0.0.0 -p 8001 videotest.asgi:application
```

# SetUp Django

- You May change the running port in `send_video.py` 

- run it 
    
```shell
sh start.sh
```


# Test

- run test case

```shell
python send_video.py
```

- watch the video at

```shell
http://127.0.0.1:81/video/wms/
```


# Issues need to be fixed

- [ ] It can not be used after sending the video for a while.