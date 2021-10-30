# coding=utf-8

import os
import sys
import subprocess
import datetime
import json
from shutil import copyfile

import platform
if(platform.system()=="Linux"):
    reload(sys)
    sys.setdefaultencoding('utf8')

class NewNode:
    value = ""
    childs = []
    def __init__(self, value):
        self.value = value
        childs = []


# 执行打包
def compile():
    command = "chmod +x gradlew" + "\n"
    command += "./gradlew clean -q" + "\n"
    command += "./gradlew assembleRelease -q > outputs/log.txt"
    subprocess.call(command, shell=True)

def compileLog():
    command = "chmod +x gradlew" + "\n"
    command += "./gradlew clean -q" + "\n"
    command += "./gradlew assembleRelease"
    subprocess.call(command, shell=True)
# 获取文件大小
def get_FileSize(path):
    fsize = os.path.getsize(path)
    fsize = fsize/float(1024*1024)
    return round(fsize,3)

# 更新业务库依赖的所有aar列表
def updateDepend(run,aarList):
    lines=[]
    lines.append('ext {\n')
    lines.append('\trun='+run+'\n')
    lines.append('\taars=[\n')
    for aar in aarList:
        lines.append("\t\t\""+aar+"\",\n")
    lines.append('\t]\n')
    lines.append('}')
    with open(aarGradle, 'w') as f:
        f.writelines(lines)

if __name__ == '__main__':
    time=datetime.datetime.now()
    currentPath = os.getcwd()
    outputPath = os.path.join(currentPath,"outputs")
    if not os.path.exists(outputPath):
        os.makedirs(outputPath) 
    apkPath = os.path.join(currentPath,"app/build/outputs/apk/release/app-release.apk")
    
    aarList = os.path.join(currentPath,"aarlist.json")
    with open(aarList, 'r') as f:
      orderResult = json.load(f)
      f.close
    print("> 总共 "+str(len(orderResult))+" 个依赖需要计算")
    print("> -----正在执行打包-----")
    aarGradle=os.path.join(currentPath,"aar.gradle")
    updateDepend('false',[])

    baseApkPath = os.path.join(outputPath,"base.apk")
    if(not os.path.exists(baseApkPath)):
        compile()
        copyfile(apkPath,baseApkPath)
    baseSize=get_FileSize(baseApkPath)
    baseSizeByte = os.path.getsize(baseApkPath)
    print("> 基础包大小："+str(baseSize)+"MB")
    results=[]
    index=0
    for result in orderResult:
        index+=1  
        print("> "+result+" "+str(len(orderResult))+"/"+str(index))
        temp=[]
        temp.append(result)
        updateDepend('true',temp)    
        compile()
        if(not os.path.exists(apkPath)):
            compileLog()
            if(not os.path.exists(apkPath)):
                raise Exception("打包失败，请查看原因")
        size=str(round(get_FileSize(apkPath)-baseSize,3))
        node={}
        node['name']=result.split(":")[0]+":"+result.split(":")[1]
        node['size']=size
        node['size_byte']=os.path.getsize(apkPath)-baseSizeByte
        results.append(node)
        print("> "+result+" : "+size+"MB")

    updateDepend('false',[])

    resultPath = os.path.join(outputPath,"result.json")
    with open(resultPath, 'w') as f:
        f.writelines(json.dumps(results))
        f.close()
    print("> 请从 outputs/result.json 文件中获取结果")
    time=datetime.datetime.now()-time
    star_time = str(time).split(".")[0]
    minutes = star_time.split(":")[1]
    seconds = star_time.split(":")[2]
    if(minutes=="00"):
      print("> 总耗时 "+seconds+" 秒")
    elif (minutes.startswith("0")):
      minutes = minutes.replace("0","")
      print("> 总耗时 "+minutes+" 分 "+seconds+" 秒")
    else:
      print("> 总耗时 "+minutes+" 分 "+seconds+" 秒")



