import requests
import sys
import os
import csv
import re
from pydub import AudioSegment
from bs4 import BeautifulSoup

URLS = sys.argv[1:]

class theLibraryScraper:
    def __init__(self, urls):
        self.urls = urls
        self.pages = []
        self.audio_files = []
        self.times = []
        self.texts = []

    def getPages(self):
        self.pages = [BeautifulSoup(requests.get(url).content, 'html.parser') for url in self.urls]

    def getTextAndTimes(self):
        for i, page in enumerate(self.pages):
            os.mkdir(f'./{i}')
            self.times.append([])
            self.texts.append([])
            tables = page.find_all(class_='timestamped-lecture')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    time = row.find('span').get_text()
                    text = row.find_all('td')[1].get_text().replace('\n', ' ').replace('\r', '').strip().replace('[...]', '')
                    if ':' in time:
                        self.times[i].append(self.convertTime(time))
                        self.texts[i].append(re.sub('\s+', '',text.replace('[???]', '')))
                    else:
                        continue
    def convertTime(self, time):
        parts =  [int(part) for part in time.split(':')]
        if len(parts) < 3:
            parts.insert(0,0)
            if len(parts) < 2:
                parts.insert(0,0)
        milli = (parts[0]*60*60*1000) + (parts[1]*60*1000) + (parts[2]*1000)
        return milli

    def getAudio(self):
        for i, page in enumerate(self.pages):
            player = page.find(id='audioPlayer')
            src = player.find('source')['src']
            raw_audio = requests.get('https://www.organism.earth/library/'+src)
            with open(f'./{i}/main_audio.ogg', 'wb') as f:
                f.write(raw_audio.content)

    def processAudio(self):
        for i in range(len(self.pages)):
            main_audio = AudioSegment.from_ogg(f"./{i}/main_audio.ogg")
            for j in range(len(self.times[i])):
                if j != len(self.times[i])-1:
                    audio_part = main_audio[self.times[i][j]:self.times[i][j+1]]
                else:
                    audio_part = main_audio[self.times[i][j]:]
                audio_part.export(f"./{i}/{j}.wav", format='wav')
            os.remove(f'./{i}/main_audio.ogg')

    def saveText(self):
        for i, text in enumerate(self.texts):
            with open(f'./{i}/text','w', newline='') as file:
                for paragraph in text:
                    file.write(paragraph+'\n')

    def scrapeAll(self):
        self.getPages()
        self.getTextAndTimes()
        self.saveText()
        self.getAudio()
        self.processAudio()
