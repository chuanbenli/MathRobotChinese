#!/usr/bin/env python3

# NOTE: this example requires PyAudio because it uses the Microphone class

import speech_recognition as sr

# obtain audio from the microphone
r = sr.Recognizer()
while 1:
    with sr.Microphone() as source:
        print("Say something!")
        audio = r.listen(source)
        print 'I hear you are saying somthing.'

        # recognize speech using Microsoft Bing Voice Recognition
    BING_KEY = "ad4279229115417eb12f105cc29d615a"  # Microsoft Bing Voice Recognition API keys 32-character lowercase hexadecimal strings
    try:
        print("Microsoft Bing Voice Recognition thinks you said " + r.recognize_bing(audio, key=BING_KEY, language="zh-CN"))
    except sr.UnknownValueError:
        print("Microsoft Bing Voice Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Microsoft Bing Voice Recognition service; {0}".format(e))
    #XUNFEI_KEY = "007b0f3f955944b78d5889a54f104917"  # Microsoft Bing Voice Recognition API keys 32-character lowercase hexadecimal strings
    
    #print("Xunfei Voice Recognition thinks you said " + r.recognize_xunfei(audio, key=XUNFEI_KEY, language="zh-CN"))
    

