import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

max_id_lock = Lock()
max_id = None
survival_dreams = []
dead_dreams = []

def get_max_id():
    global max_id
    url = "http://yume.ly/global?page=1"
    response = requests.get(url)
    response.encoding = 'utf-8'
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    
    first_entry = soup.find('div', class_='entryMain')
    id_str = first_entry.get('id')
    entry_id = int(id_str.split('_')[1])
    
    with max_id_lock:
        max_id = entry_id

def check_state(DreamId):
    url = f"http://yume.ly/dream/{DreamId}"
    response = requests.get(url)
    response.encoding = 'utf-8'
    html_content = response.text
    soup = BeautifulSoup(html_content, 'html.parser')
    
    div_element = soup.find('div', class_='entry clearit')
    if div_element:
        print(f'{DreamId}号梦境存活')
        return DreamId, 'survival'
    else:
        print(f'{DreamId}号梦境未存活')
        return DreamId, 'dead'

def main():
    get_max_id()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = []
        for DreamId in range(1, max_id + 1):
            futures.append(executor.submit(check_state, DreamId))
        
        for future in futures:
            result = future.result()
            dream_id = result[0]
            status = result[1]
            if status == 'survival':
                survival_dreams.append(dream_id)
            elif status == 'dead':
                dead_dreams.append(dream_id)
    
    survival_dreams.sort()
    dead_dreams.sort()
    
    with open('./api/dream/survival', 'w', encoding='utf-8') as file:
        for dream_id in survival_dreams:
            file.write(f'{dream_id}\n')
    
    with open('./api/dream/dead', 'w', encoding='utf-8') as file:
        for dream_id in dead_dreams:
            file.write(f'{dream_id}\n')

if __name__ == "__main__":
    main()
