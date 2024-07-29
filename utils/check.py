import os, re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

DreamCount_lock = Lock()
DreamCount = None

"""读取文件"""
def readFile(filename, binary=True):
    if os.path.exists(filename):
        with open(filename, 'rb' if binary else 'r', encoding=None if binary else 'utf-8') as f:
            return f.read()
    return None

"""写入文件"""
def saveFile(filename, data, binary=True):
    with open(filename, 'wb' if binary else 'w', encoding=None if binary else 'utf-8') as f:
        f.write(data)

'''获取Soup'''
def getSoup(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup

'''获取梦境总数'''
def getDreamCount():
    global DreamCount
    url = "http://yume.ly/global?page=1"
    soup = getSoup("http://yume.ly/global?page=1")
    first_entry = soup.find('div', class_='entryMain')
    id_str = first_entry.get('id')
    entry_id = int(id_str.split('_')[1])
    with DreamCount_lock:
        DreamCount = entry_id

'''获取梦境状态'''
def getDreamById(DreamId):
    soup = getSoup(f"http://yume.ly/dream/{DreamId}")
    dreamInfo = {}
    # 存活状态
    div_element = soup.find('div', class_='entry clearit')
    dreamInfo['status'] = 'alive' if div_element else 'dead'
    # 用户信息
    a_element = soup.find('a', class_='name')
    dreamInfo['userId'] = a_element.get('href')[8:]
    dreamInfo['name'] = a_element.text
    title_element = soup.find('a', href=f'/dream/{DreamId}')
    dreamInfo['title'] = title_element.text
    return dreamInfo


def main():
    alive_dreams = []
    dead_dreams = []
    killAD_Dreams = []
    AD_Dreams = []
    blacklist = readFile('./api/blacklist.txt', binary=False).splitlines()[1::2]
    # getDreamCount()
    DreamCount = 10

    def processDream(DreamId):
        dreamInfo = getDreamById(DreamId)
        status = dreamInfo['status']
        userId = dreamInfo['userId']
        if (status == 'alive'):
            alive_dreams.append(DreamId)
            if (userId in blacklist):
                AD_Dreams.append(DreamId)
                print(f'{DreamId}号梦境已存活 已标记为AD')
            else:
                killAD_Dreams.append(DreamId)
                print(f'{DreamId}号梦境已存活 未标记')
        else:
            dead_dreams.append(DreamId)
            print(f'{DreamId}号梦境已死亡')

    with ThreadPoolExecutor(max_workers=10) as executor:
        for DreamId in range(1, DreamCount+1):
            executor.submit(processDream, DreamId)
    
    # 使用TimSort进行排序
    alive_dreams.sort()
    dead_dreams.sort()
    AD_Dreams.sort()
    killAD_Dreams.sort()
    alive_dreams = '\n'.join(str(item) for item in alive_dreams)
    dead_dreams = '\n'.join(str(item) for item in dead_dreams)
    AD_Dreams = '\n'.join(str(item) for item in AD_Dreams)
    killAD_Dreams = '\n'.join(str(item) for item in killAD_Dreams)
    saveFile('./api/dream/alive', alive_dreams, binary=False)
    saveFile('./api/dream/dead', dead_dreams, binary=False)
    saveFile('./api/dream/AD', AD_Dreams, binary=False)
    saveFile('./api/dream/killAD', killAD_Dreams, binary=False)

if __name__ == "__main__":
    main()
