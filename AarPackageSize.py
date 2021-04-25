# coding=utf-8

import os
import sys
import subprocess
import datetime
import json
from shutil import copyfile
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header

# import platform
# if(platform.system()=="Linux"):
reload(sys)
sys.setdefaultencoding('utf8')

class NewNode:
    value = ""
    childs = []
    def __init__(self, value):
        self.value = value
        childs = []


class Dependency:
    # 存放aar所属的业务库之间的映射
    mapping = {}

    #存放每个aar出现的次数 key是aar名称，value是出现的次数
    countList = {} 
    #存放各业务库和依赖的aar之间的映射关系
    newResult = []
    # 移除support包和Android原生依赖包
    exportArr = ["com.android.support", 
                "android.arch.lifecycle", 
                "com.google.android",
                "com.squareup.leakcanary:leakcanary-android", 
                "android.arch.core",
                "org.jetbrains",
                "androidx.",
                "com.tencent.mm.opensdk:wechat-sdk-android-without-mta",
                "project :"]

    def __init__(self):
        self.file_name = "depends.txt"
        self.__readMapping()
        self.__getAarCountList()
        self.__getDependResult()

    def __readMapping(self):
        config = os.path.join(currentPath,"config.json")
        with open(config, 'r') as f:
          self.mapping = json.load(f)


    def __getAarCountList(self):
        dep_file = os.path.join(os.getcwd(), self.file_name)
        # 逐行读取文件
        with open(dep_file) as f:
            line = f.readline()
            while line:
                line = line.rstrip("\n")
                if len(line) == 0 or (
                        not line.startswith("+") and (not line.startswith("|")) and (not line.startswith("\\"))):
                    line = f.readline()
                    continue
                line = line.replace("\\", "+").replace("+---", "    ").replace("|", " ").replace("     ", "!")
                current_level = line.count("!")
                if current_level == 0:
                    line = f.readline()
                    continue
                
                line = line.replace("!", "").replace(" -> ", ":").replace(" (*)", "")
                buffer = line.split(":")
                tmp_length = len(buffer)
                if tmp_length > 2:
                    line = "%s:%s:%s" % (buffer[0], buffer[1], buffer[-1])
                if(self.countList.__contains__(line)):
                    self.countList[line]+=1
                else:
                    self.countList[line] = 1
                
                line = f.readline()


    def __getDependResult(self):
        dep_file = os.path.join(os.getcwd(), self.file_name)
        # 逐行读取文件
        with open(dep_file) as f:
            line = f.readline()
            while line:
                line = line.rstrip("\n")
                if len(line) == 0 or (
                        not line.startswith("+") and (not line.startswith("|")) and (not line.startswith("\\"))):
                    line = f.readline()
                    continue
                line = line.replace("\\", "+").replace("+---", "    ").replace("|", " ").replace("     ", "!")
                current_level = line.count("!")
                if current_level == 0:
                    line = f.readline()
                    continue
                line = line.replace("!", "").replace(" -> ", ":").replace(" (*)", "")
                buffer = line.split(":")
                tmp_length = len(buffer)
                if tmp_length > 2:
                    line = "%s:%s:%s" % (buffer[0], buffer[1], buffer[-1])
                
                if current_level == 1 and not self.check_aar_in_export(line):
                    newNode = NewNode(line)
                    newNode.childs = [line]
                    self.newResult.append(newNode)
                else:
                    if self.countList[line] == 1 and not self.check_aar_in_export(line):
                        self.newResult[len(self.newResult)-1].childs.append(line)

                line = f.readline()

    # 校验传入的aar是否在去除列表中
    def check_aar_in_export(self, aar_name):
        result = False
        for s in self.exportArr:
            if aar_name.startswith(s):
                result = True
                break
        return result

# 执行打包
def compile():
    command = "chmod +x gradlew" + "\n"
    command += "./gradlew clean -q" + "\n"
    command += "./gradlew assembleRelease -q > outputs/log.txt"
    subprocess.call(command, shell=True)

def compileLog():
    command = "./gradlew assembleRelease"
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

def resultContains(aar):
    for result in dependency.newResult:
        if(result.value==aar):
            return True
    return False

def getNodeOrNew(aar):
    for result in realResult:
        if(result.value == aar):
            return result
    newNode = NewNode(aar)
    newNode.childs=[]
    realResult.append(newNode)
    return newNode

def getNode(name):
  for result in realResult:
    if(result.value == name):
      realResult.remove(result)
      return result
  return None

if __name__ == '__main__':
    time=datetime.datetime.now()
    currentPath = os.getcwd()
    outputPath = os.path.join(currentPath,"outputs")
    if not os.path.exists(outputPath):
        os.makedirs(outputPath) 
    apkPath = os.path.join(currentPath,"app/build/outputs/apk/release/app-release.apk")
    dependency = Dependency()
    # 将出现多次的aar添加到集合中
    for allaar in sorted(dependency.countList):
        if(dependency.countList[allaar]>1 and not resultContains(allaar)) and not dependency.check_aar_in_export(allaar):
            newNode = NewNode(allaar)
            newNode.childs = [allaar]
            dependency.newResult.append(newNode)
    print("> 程序将根据 config.json 文件中的配置处理分组映射关系")
    # 根据映射关系重新处理aar对应的业务库
    realResult = []
    for result in dependency.newResult:
        hasAdd = False
        for mapp in dependency.mapping:
            if(result.value.startswith(mapp)):
                newNode = getNodeOrNew(dependency.mapping[mapp])
                hasAdd = True
                for aar in result.childs:
                    if(not newNode.childs.__contains__(aar)):
                        newNode.childs.append(aar)
        if(not hasAdd):
            result.value=result.value.split(":")[1]
            realResult.append(result)
    print("> 程序将根据 order.json 文件中的顺序重新排序产出结果")
    # 根据指定的顺序进行排序
    orderResult = []
    order = []
    resultPath = os.path.join(currentPath,"order.json")
    with open(resultPath, 'r') as f:
      order = json.load(f)
      f.close
    for name in order:
      node = getNode(name)
      if(node):
        orderResult.append(node)
    resultNewAar = "Hi,all:\n"
    if(len(sys.argv)>1):
        resultNewAar+=sys.argv[1]
    if(len(realResult)>0):
        resultNewAar+=' 分支版本新增分组信息如下：\n'
        print("> 新增分组信息如下，请根据需要修改 config.json 文件重新指定分组：")
    for result in realResult:
        resultNewAar+=result.value+":\n"
        resultNewAar+=json.dumps(sorted(result.childs)).replace(",",",\n").replace("]","]\n")
        print(result.value+":\n")
        print(json.dumps(sorted(result.childs)).replace(",",",\n").replace("]","]\n"))
        orderResult.append(result)
   
    # 输出映射关系，可以看到业务库对应的aar列表
    resultPath = os.path.join(outputPath,"depends-mapping.txt")
    with open(resultPath, 'w') as f:
        for result in orderResult:
            f.writelines(result.value+":\n")
            f.writelines(json.dumps(sorted(result.childs)).replace(",",",\n").replace("]","]\n"))
            f.writelines("\n")
        f.close()
    print("> 已输出依赖映射关系到 outputs/depends-mapping.txt 文件中")

    # 输出aar列表，方便每个版本对比aar的变化
    resultPath = os.path.join(outputPath,"aarlist.txt")
    with open(resultPath, 'w') as f:
        for allaar in sorted(dependency.countList):
            f.writelines(allaar.split(":")[0]+":"+allaar.split(":")[1]+"\n")
        f.close()
    print("> 已输出aar列表到 outputs/aarlist.txt 文件中")
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
        print("> "+result.value+" "+str(len(orderResult))+"/"+str(index))
        updateDepend('true',result.childs)    
        compile()
        if(not os.path.exists(apkPath)):
            compileLog()
            raise Exception("打包失败，请解决后重新执行")
        size=str(round(get_FileSize(apkPath)-baseSize,3))
        node={}
        node['name']=result.value
        node['depends']=result.childs
        node['size']=size
        node['size_byte']=os.path.getsize(apkPath)-baseSizeByte
        results.append(node)
        print("> "+result.value+" : "+size+"MB")

    updateDepend('false',[])

    resultPath = os.path.join(outputPath,"result-detail.json")
    with open(resultPath, 'w') as f:
        f.writelines(json.dumps(results))
        f.close()
    
    for result in results:
        del result['depends']

    resultPath = os.path.join(outputPath,"result.json")
    with open(resultPath, 'w') as f:
        f.writelines(json.dumps(results))
        f.close()
    print("> 请从 outputs/result.json 文件中获取结果")
    time=datetime.datetime.now()-time
    strtime = str(time).split(".")[0]
    minutes = strtime.split(":")[1]
    seconds = strtime.split(":")[2]
    if(minutes=="00"):
      print("> 总耗时 "+seconds+" 秒")
    elif (minutes.startswith("0")):
      minutes = minutes.replace("0","")
      print("> 总耗时 "+minutes+" 分 "+seconds+" 秒")
    else:
      print("> 总耗时 "+minutes+" 分 "+seconds+" 秒")
    
    



