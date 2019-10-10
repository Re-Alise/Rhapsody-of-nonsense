import cv2
import os
import numpy as np
from time import sleep

path = "1570695288/"
fileName = "color2.avi"
fileName = "original.avi"
gaussian = (13, 13)
kernel = np.ones((3,3),np.uint8)
"""
" ":next frame
"x":quit
似乎 不要找黑色 改成找不是地板和色塊比較容易?
先判斷色塊 把他剃掉?
"""

def imgand(img1, img2):
    return np.logical_and(img1, img2)

def imgor():
    return np.logical_or(img1, img2)

# 穩定版
def detect(sframe):
    """顏色轉換時EX 紅-> 綠有機會誤判藍 之類的，須加上一部份延遲做防誤判。
    """
    sframe = cv2.GaussianBlur(frame, gaussian, 0)
    r = sframe[:,:,2]
    g = sframe[:,:,1]
    b = sframe[:, :, 0]
    a = r-g+220
    c = b-r+220
    ans = cv2.hconcat([a, c])
    ans = cv2.cvtColor(ans, cv2.COLOR_GRAY2BGR)
    _, a = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)
    _, c = cv2.threshold(c, 100, 255, cv2.THRESH_BINARY_INV)
    na = cv2.countNonZero(a)
    nb = cv2.countNonZero(c)
    if na>5000:
        if nb>2500:
            print("G", na, nb)
            return ans
        else:
            print("R", na, nb)
            return ans
    else:
        if nb>2500:
            print("B", na, nb)
            return ans
        else:
            print("XX", na, nb)
            return ans
    return ans

# 測試版
def detect2(sframe):
    """顏色轉換時EX 紅-> 綠有機會誤判藍 之類的，須加上一部份延遲做防誤判。
    """
    sframe = cv2.GaussianBlur(frame, gaussian, 0)
    r = sframe[:,:,2]
    g = sframe[:,:,1]
    b = sframe[:, :, 0]
    a = r/g*200
    a = np.asarray(a, np.uint8)+10
    c = b/r*200
    c = np.asarray(c, np.uint8)+40
    ans = cv2.hconcat([a, c])
    ans = cv2.cvtColor(ans, cv2.COLOR_GRAY2BGR)
    _, a = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)
    _, c = cv2.threshold(c, 100, 255, cv2.THRESH_BINARY_INV)
    na = cv2.countNonZero(a)
    nb = cv2.countNonZero(c)
    print("~~~~")
    if na > 5000:
        if nb>2500:
            print("G", na, nb)
            return ans
        else:
            print("R", na, nb)
            return ans
    else:
        if nb>2500:
            print("B", na, nb)
            return ans
        else:
            print("XX", na, nb)
            return ans
    return ans

def black(frame):
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    gray = frame[:,:,2]
    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thr = cv2.threshold(gray,150,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    # thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 2)
    thr = cv2.cvtColor(thr, cv2.COLOR_GRAY2BGR)
    return thr

def test(frame):
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    r = frame[:,:,2]
    b = frame[:, :, 0]
    # c = b-r+180
    c = np.minimum(np.maximum(b/r*400-300, 0), 255)
    c = np.asarray(c, np.uint8)
    _, c_ = cv2.threshold(c, 160, 255, cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    # c__ = cv2.morphologyEx(c_, cv2.MORPH_CLOSE, kernel)
    # thr = cv2.adaptiveThreshold(mix, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    # WHAT?????????????????????????????????????????????????????????????????????
    # c is a vary good 2value dealt????????????????????????????????????????????
    # how~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # ans = cv2.hconcat([a, b, c, gray])
    ans = cv2.hconcat([c, c_])
    ans = cv2.cvtColor(ans, cv2.COLOR_GRAY2BGR)
    return ans

def floor(frame):
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    r = frame[:,:,2]>>3
    g = frame[:,:,1]>>3 
    mix = g
    _, thr = cv2.threshold(mix,100,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    # thr = cv2.adaptiveThreshold(mix, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    """
    r>>
    g>>
    """
    thr = cv2.cvtColor(thr, cv2.COLOR_GRAY2BGR)
    return thr
    pass

def rad(frame):
    """ 
    r>>
    b<<
    """
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    r = frame[:,:,2]
    b = frame[:, :, 0]
    # _, thr = cv2.threshold(r,100,255,cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    _, thr = cv2.threshold(b,150,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    thr = cv2.cvtColor(thr, cv2.COLOR_GRAY2BGR)
    return thr

if __name__ == "__main__":
    try:
        cap = cv2.VideoCapture(path+fileName) 
        stop = 0
        while cap.isOpened():
            if stop:
                break
            ret, frame = cap.read()
            if ret:
                # ....
                cv2.imshow('Replay', cv2.hconcat([frame, detect(frame)]))
                # detect(frame)
                while 1:
                    inn = cv2.waitKey(0)
                    if inn & 0xFF == ord(' '):
                        break
                    if inn & 0xFF == ord('x'):
                        stop = 1
                        break
                    sleep(0.1)
    finally:
        cap.release()
        cv2.destroyAllWindows()
