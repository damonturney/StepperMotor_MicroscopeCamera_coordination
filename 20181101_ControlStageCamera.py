# -*- coding: utf-8 -*-

"""
Control Microscope Stage and Microscope Camera simultaneously
Damon
"""


# set baud rate of COM1 to 300
import time
import serial
import os
import pywinauto
import cv2
import numpy as np
import datetime
import threading
import queue


flag = 1

# Gaussian radius (should really be an argument):
def get_sharpness(frame):
    switch=True
    while switch == True:
        try:
            meanframe = frame.mean(axis=2)
            blurred = cv2.GaussianBlur(meanframe, (21, 21), 0) #51 is the radius of sharpness calculations
            sharp = np.abs(meanframe - blurred)
            switch=False
        except AttributeError:
            frame=snapimage(ToupView)
    return sharp

def stdd(image, N):
    width = image.shape[0]
    heigth = image.shape[1]
    desv = np.zeros((width,heigth))
    for i in range (width):
        for j in range (heigth):
            if i < N :
                mini = 0
            else :
                mini = i - N
            if (i+N) > width :
                maxi = width
            else :
                maxi = N + i
            if j < N :
                minj = 0
            else :
                minj = j - N
            if (j+N) > heigth :
                maxj = heigth
            else :
                maxj = N + j
            window = image[mini:maxi,minj:maxj]
            desv[i,j] = window.std()
    return desv

def snapimage(ToupView):
    switch=True
    while switch==True:
        try:
            files=os.listdir('C:\\Users\Maccor\Desktop\Damon\stack')
            files=[file for file in files if file[0]!='.']
            if len(files)==0:
                Toupview_handles=pywinauto.findwindows.find_windows(title='ToupView')
                if len(Toupview_handles)>1:
                    app=pywinauto.application.Application().connect(handle=Toupview_handles[0])
                    app.top_window().set_focus()
                    app.top_window().type_keys('{ENTER 2}')
                else: 
                    app=pywinauto.application.Application().connect(handle=Toupview_handles[0])
                    while len(os.listdir('C:\\Users\Maccor\Desktop\Damon\stack'))==0:
                        app.top_window().type_keys('^Q') #Sends Control-Q to the window
                        time.sleep(1)
                        frame=cv2.imread('C:\\Users\Maccor\Desktop\Damon\stack/'+os.listdir('C:\\Users\Maccor\Desktop\Damon\stack')[0])
                try:
                    frame.mean(axis=2)
                    switch=False
                except AttributeError:
                    switch=True
            else:
                erasestackfolder()
        except PermissionError:
            time.sleep(1)
    return(frame)

def erasestackfolder():
    switch=True
    while switch==True:
        try:
            files=os.listdir('C:\\Users\Maccor\Desktop\Damon\stack')
            files=[file for file in files if file[0]!='.']
            for file in files: os.remove('C:\\Users\Maccor\Desktop\Damon\stack/'+file)
            time.sleep(1)
            switch=False
        except PermissionError:
            time.sleep(1)



def collectimages():
    t=threading.current_thread()
    app = pywinauto.application.Application()
    app.connect(title="ToupView") #connects the application object to the ToupView Windows application object
    #app.windows()   lists all the windows associated with ToupView
    ToupView=app.window(title="ToupView")  #creates a dialogue with the main ToupView window
    ser = serial.Serial('COM1',timeout=1,baudrate=300)
    time.sleep(1)
    num_subimages=16
    k=1
    while getattr(t, "stop") == False:
        ser.setRTS(True)
        frame=snapimage(ToupView)
        print('Captured image 1.')
        time.sleep(1)
        erasestackfolder()
        ser.setRTS(True)
        if k>1: ser.write(bytearray(10*[170]))
        best_pixels = frame
        best_sharpness = get_sharpness(best_pixels)
        #local_stdev=stdd(frame,21)
        #combined_metric=best_sharpness+local_stdev
        for k in range(2,num_subimages+1,1):
            if getattr(t, "stop") == True:
                break
            frame=snapimage(ToupView)
            print('Captured image ' + str(k) + '.')
            time.sleep(1)
            erasestackfolder()
            ser.setRTS(True)
            ser.write(bytearray(10*[170]))
            sharpness = get_sharpness(frame)
            better_indexes = np.where(sharpness > best_sharpness)
            best_pixels[better_indexes] = frame[better_indexes]
            best_sharpness[better_indexes] = sharpness[better_indexes]
            try:
                item = q.get(True, 1)
                if item =='q': break
            except: pass
            time.sleep(1)
        cv2.imwrite('images/'+time.strftime("%Y%m%d%H%M%S")+".png",best_pixels)
        ser.setRTS(False)
        time.sleep(1)
        ser.setRTS(False)
        if k>1: ser.write(bytearray(10*(k)*[170]))
        for i in range(60):
            try:
                item = q.get(True, 1)
                if item =='q': break
            except: pass
            time.sleep(1)
            print(i)
        print(datetime.datetime.now())
    cv2.destroyAllWindows()
    ser.close()

#def kill_thread(n):
    #userinput='r'
    #while userinput != 'q':
    #    userinput=input('Enter q to quit: ')
    #n.stop = True
    #n.join()
    #o.stop = True
    #o.join()
    #return(userinput)

if __name__ == "__main__":
    print('Enter directory folder that contains potentiostat data.')
    print('Example: C:\\Users\\Maccor\\Documents\\Brendan\\20180629_movie')
    print('Example:C:\\Users\\Maccor\\Desktop\\Damon\\movie_collection\\20180629_movie')
    working_folder=input('Enter here:')
    os.chdir(working_folder)
    print(datetime.datetime.now())
    try: os.stat('images')
    except: os.mkdir('images')
    q = queue.Queue()
    n=threading.Thread(target=collectimages)
    n.stop = False
    n.start()
    userinput='r'
    while userinput != 'q':
        userinput=input('Enter q to quit: ')
    q.put('q')
    n.stop = True
    n.join()
    #o=threading.Thread(target=kill_thread,args=[n])
    #o.stop = False
    #o.start()
    #while userinput != 'q':
    #    time.sleep(0.5)
