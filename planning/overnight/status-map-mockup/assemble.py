import os
d=open('data.json',encoding='utf-8').read().replace('</','<\/')
h=open('head.html',encoding='utf-8').read()+open('body.html',encoding='utf-8').read().replace('__DATA__',d)
open('factory-status-map.html','w',encoding='utf-8').write(h); print(len(h)//1024,'KB')
