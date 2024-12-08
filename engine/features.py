import os
from pipes import quote
import sqlite3
import struct
import subprocess
import time
import webbrowser
from playsound import playsound
import eel
import pyaudio
import pyautogui
from engine.command import speak
from engine.config import *
import pywhatkit as kit
import pvporcupine
from langchain_core.prompts import PromptTemplate as pt
import requests
from engine.helper import extract_yt_term, remove_words
import json, datetime
import re
con = sqlite3.connect("nexus.db")
cursor = con.cursor()

def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "")
    query = query.replace("open", "")
    query.lower()

    app_name = query.strip()

    if app_name != "":

        try:
            cursor.execute(
                'SELECT path FROM sys_command WHERE name IN (?)', (app_name,))
            results = cursor.fetchall()

            if len(results) != 0:
                speak("Opening "+query)
                os.startfile(results[0][0])

            elif len(results) == 0: 
                cursor.execute(
                'SELECT url FROM web_command WHERE name IN (?)', (app_name,))
                results = cursor.fetchall()
                
                if len(results) != 0:
                    speak("Opening "+query)
                    webbrowser.open(results[0][0])

                else:
                    speak("Opening "+query)
                    try:
                        os.system('start '+query)
                    except:
                        speak("not found")
        except:
            speak("some thing went wrong")

       

def PlayYoutube(query):
    search_term = extract_yt_term(query)
    speak("Playing "+search_term+" on YouTube")
    kit.playonyt(search_term)


def hotword():
    porcupine=None
    paud=None
    audio_stream=None
    try:
        print("enter1")
                
        porcupine = pvporcupine.create(
        access_key=PORCUPINE_API_KEY,
        keyword_paths=[r'engine\nexus_en\nexus_en.ppn']
        )

        print("enter2")
        paud=pyaudio.PyAudio()
        audio_stream=paud.open(rate=porcupine.sample_rate,channels=1,format=pyaudio.paInt16,input=True,frames_per_buffer=porcupine.frame_length)
        
        print("enter3")
        # loop for streaming
        while True:
            # print("Listening for wake words...")
            keyword=audio_stream.read(porcupine.frame_length)
            keyword=struct.unpack_from("h"*porcupine.frame_length,keyword)
            # print("Processing audio frame...")
            keyword_index=porcupine.process(keyword)

            if keyword_index>=0:
                print("hotword detected")
                import pyautogui as autogui
                autogui.keyDown("win")
                autogui.press("j")
                time.sleep(2)
                autogui.keyUp("win")

    except Exception as e:
        print(e)
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()            

def genai0(query):
    import google.generativeai as genai
    from engine.config import GEMINI_API_KEY
    from datetime import datetime

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(query + f"\nanswer in short as a voice assistant.\nextra details :-\ntime : {datetime.now().strftime(r'%Y-%m-%d %H:%M:%S')}\nlocation : India\n")
    print(response.text)
    speak(response.text)


def news(query):
    import datetime, json
    from requests import get
    import google.generativeai as genai
    
    query = query.split('about')[-1].replace(" ","")
    from engine.config import NEWS_API_TOKEN, GEMINI_API_KEY
    nowdate = datetime.date.today()
    lastdate = datetime.date.today() - datetime.timedelta(days=90)

    req = f"https://newsapi.org/v2/everything?q={query}&from={nowdate}&to={lastdate}&language=en&sortBy=publishedAt&apiKey={NEWS_API_TOKEN}"
    res = get(req)
    res = json.loads(res.text)
    n = 0
    q=""
    for news in res['articles']:

        t = news['title']
        d = news['publishedAt']
        des = news['description']
        if t=='[Removed]' or des==None:
            continue
        n+=1

        newstime = datetime.datetime.strptime(d,r"%Y-%m-%dT%H:%M:%SZ").strftime(r"%I %b %d, %Y at %H %p")

        q += str(newstime)
        q += " : "
        q += t
        q += " : "
        q += des
        q += "\n\n"

        if n==5:
            break

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    print("--working on it news--")
    response = model.generate_content(f"{q} summarize the above news properly in approx 30 words also include important dates if needed")
    print(response.text)

    speak(response.text)


def joke():
    import pyjokes
    speak(pyjokes.get_joke("en","neutral"))

def weather(query):
    import requests
    import os
    from engine.config import WEATHER_API_TOKEN
    area = query.split("in")[-1].replace(" ","")

    css = """
<title>weather-forecast</title>
<style>
  *{font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;}
  body{background-color: black;display: flex;justify-content: center;align-items: center;}
.wea_cardContainer {width: fit-content;position: relative;display: flex;align-items: center;justify-content: center;}
.wea_weathercard {position: relative;width: 520px;height: 450px;display: flex;flex-direction: column;align-items: center;justify-content: space-between;padding: 20px 10px;border-radius: 10px;backdrop-filter: blur(30px);background-color: rgba(65, 65, 65, 0.308);border: 1px solid rgba(255, 255, 255, 0.089);cursor: pointer;}
.wea_city {text-align: center;font-weight: 700;font-size: 1.3em;letter-spacing: 1.2px;color: white;}
.wea_weather {font-weight: 500;font-size: 1.1em;letter-spacing: 1.2px;color: rgb(197, 197, 197);}  
.wea_minmaxContainer {margin: 10px;width: 100%;display: flex;align-items: center;justify-content: space-between;}
.wea_min,.wea_max {align-items: flex-start;border-left: 2px solid white;border-right: 2px solid white;width: 50%;font-size: 1.3em;display: flex;flex-direction: column;align-items: center;justify-content: center;gap: 0px;padding: 0px 20px;}
.wea_maxHeading,.wea_minHeading {font-size: 0.7em;font-weight: 600;color: white;}
.wea_maxTemp,.wea_minTemp {font-size: 0.8em;font-weight: 500;color: rgb(197, 197, 197);padding: 0;margin: 0;}
.wea_cardContainer::before {width: 100px;height: 100px;content: "";position: absolute;background-color: rgb(144, 161, 255);z-index: -1;border-radius: 50%;left: 100px;top: 50px;transition: all 1s;}
.wea_cardContainer:hover::before {transform: translate(-50px, 50px);}
</style>
"""

        
    url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_TOKEN}&q={area}"
    
    response = requests.get(url=url)
    res = json.loads(response.text)
    try:

        locn = res["location"]["name"]
        locr = res["location"]["region"]
        max = res["forecast"]["forecastday"][0]["day"]['maxtemp_c']
        min = res["forecast"]["forecastday"][0]["day"]['mintemp_c']
        status = res["forecast"]["forecastday"][0]["day"]['condition']['text']
        icon = res["forecast"]["forecastday"][0]["day"]['condition']['icon']
        rise = res["forecast"]["forecastday"][0]["astro"]['sunrise']
        set = res["forecast"]["forecastday"][0]["astro"]['sunset']
        
        html = f"""
        <div class="wea_cardContainer"><div class="wea_weathercard"><p class="wea_city">
        {locn}<br>{locr}
        </p><p class="wea_weather">{status}</p>
        <img src={icon}
        alt="" 
        height="120px" width="120px">
        <div class="wea_minmaxContainer">
        <div class="wea_min">
            <p class="wea_minHeading">Sunset</p>
            <p class="wea_minTemp">{set}</p>
        </div>
        <div class="wea_min">
            <p class="wea_minHeading">Min</p>
            <p class="wea_minTemp">{min}°</p>
        </div>
        <div class="wea_max">
            <p class="wea_maxHeading">Max</p>
            <p class="wea_maxTemp">{max}°</p>
        </div>
        <div class="wea_max">
            <p class="wea_maxHeading">Sunrise</p>
            <p class="wea_maxTemp">{rise}</p>
        </div>
        </div>
    </div>
    </div>
    """
        
        weather_page = css+html
        
        wf = open("wea.html",'w')
        wf.write(weather_page)
        wf.close()

        os.startfile("wea.html")

        speak(f"weather in {locn} of region {locr} is, {status}, today")

    except Exception as e:
        print(e)
        print("location not found")
        speak("sorry but the specified location not found")
