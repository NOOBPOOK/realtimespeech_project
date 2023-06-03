import websockets
import asyncio
import streamlit as st
import pyaudio
import base64
import json
from pathlib import Path
import os

#Session State
if 'text' not in st.session_state:
    st.session_state['text'] = "Listening..."
    st.session_state['run'] = False

def startting():
    st.session_state['run'] = True

def stopping():
    st.session_state['run'] = False

def download():
    read_text = open('transcription.txt','r')
    st.download_button(
        label="Download the transcription for free!",
        data=read_text,
        file_name="transcription_output.txt",
        mime='text/plain'
    )

#AUDIO SETTINGS
FRAMES = 3200
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
p = pyaudio.PyAudio()

#OPENS A STREAM WITH DEFAULT PARAMETERS
stream = p.open(
    format = FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=FRAMES
)



st.title("NOOBPOOK Presents Real Time Transcription APP")
#st.image("logo.png",width=200)

col1,col2 = st.columns(2)

col1.button("Start", on_click=startting)
col2.button("Stop", on_click=stopping)



async def send_recieve():
    URL = f"wss://api-inference.huggingface.co/bulk/stream/cpu/facebook/bart-large-mnli"

    print("Connecting to URL Endpoint")

    async with websockets.connect(
        URL,
        extra_headers=(("Authorization", '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'),),
        ping_interval = 5,
        ping_timeout = 20
        ) as op:
            
            r = await asyncio.sleep(0.1)
            print("Recieving Messages")

            session_begins = await op.recv()
            print(session_begins)
            print("Sending messages.....")

            async def send():
                 while st.session_state['run']:
                    try:
                        data = stream.read(FRAMES)
                        data = base64.b64encode(data).decode("utf-8")
                        json_data = json.dumps({"audio data":str(data)})
                        r = await op.send(json_data)

                    except websockets.exceptions.ConnectionClosedError as e:
                        print(e)
                        assert e.code == 4008
                        break
                
                    except Exception as e:
                        print(e)
                        assert False, "Not a websocket error"

                    r = await asyncio.sleep(0.01) 

            async def recieve():
                print("Recieve Testing code")
                while st.session_state['run']:
                    try:
                        result = op.recv()
                        rd = result.read()
                        result = json.loads(rd)['text'] 

                        if json.loads(result)['message_type'] == 'FinalTranscript':
                            print(result)
                            st.session_state['text'] = result
                            st.write(st.session_state['text'])

                            transcription_txt = open('transcription.txt','a')
                            transcription_txt.write(st.session_state['text'])
                            transcription_txt.close()
                        else:
                            st.session_state['text'] = result
                            print(result)
                            st.write(st.session_state['text'])

                    except websockets.exceptions.ConnectionClosedError as e:     
                        print(e)
                        assert e.code == 4008
                        break

                    except Exception as e:
                        print(e)
                        assert False, "Not a websocket 4008 error"

            send_result , recieve_result = await asyncio.gather(send(),recieve())

asyncio.run(send_recieve())
        
if Path('transcription.txt').is_file():
    st.markdown('###DOWNLOAD')
    download()
    os.remove('transcription.txt')

            