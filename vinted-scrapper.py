import requests
from bs4 import BeautifulSoup
import concurrent.futures
import threading
import time
from fake_useragent import UserAgent
import os
from colorama import Fore, Style, init

init(autoreset=True)

base_url = "https://www.vinted.fr/member/"
ua = UserAgent()

lock = threading.Lock()
results = {}

start_id_file = "start_id.txt"

def read_start_id():
    if os.path.exists(start_id_file):
        with open(start_id_file, "r") as f:
            return int(f.read().strip())
    return 1

def write_start_id(member_id):
    with open(start_id_file, "w") as f:
        f.write(str(member_id))

def fetch_username(member_id, retries=3, backoff=5):
    url = f"{base_url}{member_id}"
    headers = {
        "User-Agent": ua.random
    }

    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.text.strip()
                    if "rate limited" in title_text.lower():
                        print(f"{Fore.YELLOW}[!] Limité par le débit! Tentative {attempt+1}/{retries}, attente de {backoff} secondes")
                        time.sleep(backoff)
                        backoff += 5
                        continue
                    elif "Vinted | Achète, vends ou échange les vêtements" in title_text:
                        return member_id, None
                    else:
                        username = title_text.replace(" - Vinted", "")
                        return member_id, username
        except requests.RequestException as e:
            print(f"{Fore.RED}[!] Exception de requête pour l'ID {member_id} : {e}")
            time.sleep(backoff)
            backoff += 5

    return member_id, None

def process_id(member_id):
    member_id, username = fetch_username(member_id)
    if username:
        with lock:
            results[member_id] = username
            print(f"{Fore.GREEN}[?] trouvé : ID {member_id} | user : {username}")
            with open("output.txt", "a") as f:
                f.write(f"ID {member_id} | user : {username}\n")
    with lock:
        write_start_id(member_id)

start_id = read_start_id()

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    member_id = start_id
    while True:
        executor.submit(process_id, member_id)
        member_id += 1
        time.sleep(1)
