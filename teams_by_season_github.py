# -*- coding: utf-8 -*-
"""Teams_by_season_GitHub.ipynb"""

import random
import requests
import time
from bs4 import BeautifulSoup
import logging
import pandas as pd
from tqdm import tqdm
from time import sleep
from random import randint
from requests.exceptions import ConnectionError, Timeout, ReadTimeout
import boto3
import os

# Scarica la lista di User-Agent
def get_user_agents():
    try:
        response = requests.get('https://raw.githubusercontent.com/AlessandroVaccarino/user-agents/main/agents/desktop.txt')
        if response.status_code == 200:
            return response.text.splitlines()
        else:
            return ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"]
    except requests.RequestException:
        return ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"]

# Funzione per estrarre i link delle squadre
def get_squad_urls(url):
    squad_urls = []
    user_agents_list = get_user_agents()
    session = requests.Session()
    headers = {
        'User-Agent': random.choice(user_agents_list),
        'Referer': 'https://www.transfermarkt.com/',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    try:
        response = session.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print("❌ Problema con la richiesta! Potresti essere stato bloccato.")
            return squad_urls
        soup = BeautifulSoup(response.content, 'html.parser')
        div_yw1 = soup.find('div', {'id': 'yw1'})
        if not div_yw1:
            print("⚠️ 'yw1' non trovato! Provo con un altro div...")
            div_yw1 = soup.find('div', {'class': 'responsive-table'})
        if not div_yw1:
            print("⚠️ Ancora nulla! Il layout potrebbe essere cambiato o sei stato bloccato.")
            return squad_urls
        rows = div_yw1.find_all('tr')
        for row in rows:
            cell = row.find('td')
            if cell:
                link = cell.find('a')
                if link and 'href' in link.attrs:
                    squad_url = "https://www.transfermarkt.com" + link['href']
                    squad_urls.append(squad_url)
        time.sleep(random.uniform(1, 3))
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la richiesta: {e}")
    return squad_urls

# Parametri principali
years = ['2010', '2011','2012', '2013','2014', '2015','2016', '2017', '2018', '2019','2020', '2021','2022', '2023','2024']
leagues = [
#    {"name": "laliga", "label": "ES1"},
#   {"name": "premier-league", "label": "GB1"},
#  {"name": "bundesliga", "label": "L1"},
    {"name": "serie-a", "label": "IT1"}
#    {"name": "ligue-1", "label": "FR1"}
]

# Liste per i dati e gli URL falliti
data = []
failed_urls = []

# Configurazione retry
max_retries = 3
retry_sleep = 5

for league in leagues:
    league_name = league["name"]
    league_label = league["label"]
    for year in years:
        url_league = f"https://www.transfermarkt.com/{league_name}/startseite/wettbewerb/{league_label}/plus/?saison_id={year}"
        print(f"\n--- Processing league: {league_name}, season: {year} ---")
        squad_urls = []
        # Retry per ottenere squad_urls
        for attempt in range(max_retries):
            squad_urls = get_squad_urls(url_league)
            if squad_urls:
                break
            print(f"Retry [{attempt+1}/{max_retries}] per {league_name} {year} (no squadre trovate)")
            time.sleep(retry_sleep)
        if not squad_urls:
            print(f"❌ Nessuna squadra trovata per {league_name} {year} dopo {max_retries} tentativi!")
            failed_urls.append({"url": url_league, "league": league_name, "season": year, "reason": "No squads found"})
            continue

        for url in tqdm(squad_urls, desc=f"Processing {league_name} season {year}", unit=" URL"):
            url_parts = url.split("/")
            squad_id = url_parts[-3]
            squad_name = url_parts[-6].title()
            for attempt in range(max_retries):
                try:
                    time.sleep(randint(1, 3))
                    user_agent = random.choice(get_user_agents())
                    headers = {'User-Agent': user_agent, 'Referer': 'https://www.transfermarkt.com/'}
                    response = requests.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    if response.status_code == 429:
                        time.sleep(retry_sleep)
                        continue
                    soup = BeautifulSoup(response.content, 'html.parser')
                    break
                except requests.exceptions.RequestException:
                    time.sleep(retry_sleep)
            else:
                print(f"Failed to process URL: {url} after {max_retries} attempts")
                failed_urls.append({"url": url, "league": league_name, "season": year, "reason": "Squad page failed"})
                continue

            try:
                table = soup.find('table', class_="items")
                if not table:
                    failed_urls.append({"url": url, "league": league_name, "season": year, "reason": "No table found"})
                    continue
                rows = table.find_all('tr', {'class': ['odd', 'even']})
                for row in rows:
                    shirt_number_td = row.find('td', class_="zentriert")
                    shirt_number = shirt_number_td.text.strip() if shirt_number_td else ""
                    td = row.find('td', class_="posrela")
                    if not td:
                        continue
                    td_elements = row.find_all('td', class_="zentriert")
                    td_age = td_elements[1] if len(td_elements) > 1 else None
                    td_value = row.find('td', class_="rechts hauptlink")
                    if not (td and td_value and td_age):
                        continue
                    a_tag = td.find_all('a')
                    href_value = a_tag[-1]['href']
                    href_parts = href_value.split("/")
                    name = a_tag[-1].get_text(strip=True) if len(a_tag) > 1 else a_tag[0].get_text(strip=True)
                    role = td.find('table').find_all('tr')[1].find('td').text.strip() if td.find('table') else ""
                    value = td_value.a.string if td_value.a else "0"
                    try:
                        value_num = float(value.replace('€', '').replace('m', '').replace('k', '').replace(',', '').strip())
                        if 'm' in value:
                            value_num *= 1_000_000
                        elif 'k' in value:
                            value_num *= 1_000
                    except ValueError:
                        value_num = 0.0
                    birth_date = td_age.get_text(strip=True) if td_age else ""
                    data.append([href_parts[-1], name, shirt_number, role, birth_date, value_num, squad_name, squad_id, year, league_name])
            except Exception as e:
                print(f"Data extraction error for URL: {url}, error: {e}")
                failed_urls.append({"url": url, "league": league_name, "season": year, "reason": str(e)})

# Salvataggio dati
if data:
    df = pd.DataFrame(data, columns=["PlayerID", "Name", "ShirtNumber", "Role", "BirthDate", "Value", "SquadName", "SquadID", "Season", "League"])
    df.to_csv("serie-a.csv", index=False)

if failed_urls:
    failed_df = pd.DataFrame(failed_urls)
    failed_df.to_csv("failed_urls.csv", index=False)
    print("Failed URLs saved to failed_urls.csv")

# Upload su S3
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"
S3_BUCKET_NAME = "transfermarkt-raw-data-2025"
S3_FOLDER_PATH = "Teams-by-season/"
s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)

def upload_to_s3(file_path, bucket_name, s3_filename):
    if not os.path.exists(file_path):
        print(f"❌ Il file {file_path} non esiste!")
        return
    try:
        s3.upload_file(file_path, bucket_name, s3_filename)
        print(f"✅ File caricato su S3: s3://{bucket_name}/{s3_filename}")
    except Exception as e:
        print(f"❌ Errore upload S3: {e}")

upload_to_s3("serie-a.csv", S3_BUCKET_NAME, f"{S3_FOLDER_PATH}seriea-a.csv")
if failed_urls:
    upload_to_s3("failed_urls.csv", S3_BUCKET_NAME, f"{S3_FOLDER_PATH}failed_urls.csv")
