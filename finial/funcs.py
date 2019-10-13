import cv2
import os
import numpy as np
from time import sleep

IMAGE_SIZE = (320, 240)
path = "./../video/"
# path = "./../video/"
# fileName = "radline.avi"
fileName = "test8.avi"
gaussian = (13, 13)
kernel = np.ones((3,3),np.uint8)

def show_all(frame):
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    r = frame[:,:,2]
    g = frame[:, :, 1]
    b = frame[:, :, 0]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]

    ans1 = cv2.hconcat([r, g, b])
    ans1 = cv2.cvtColor(ans1, cv2.COLOR_GRAY2BGR)
    ans1 = cv2.hconcat([frame, ans1])
    ans2 = cv2.hconcat([gray, h, s, v])
    ans2 = cv2.cvtColor(ans2, cv2.COLOR_GRAY2BGR)
    ans = cv2.vconcat([ans1, ans2])
    return ans

def mission(frame):
    return cv2.hconcat([frame, cv2.cvtColor(normal(frame), cv2.COLOR_GRAY2BGR)])
    pass

def normal(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    r = frame[:,:,2]
    b = frame[:, :, 0]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # _, gray_ = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)# +cv2.THRESH_OTSU)
    c = b-r+180
    # c = np.minimum(np.maximum(c, 0), 255)
    # c = np.asarray(c, np.uint8)
    _, c_ = cv2.threshold(c, 100, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    # binarized_frame = np.bitwise_or(c_, gray_)
    return c_

def light(frame):
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    r = frame[:,:,2]
    g = frame[:,:,1]
    a = r-g+220
    _, a_ = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    a_ = cv2.cvtColor(a_, cv2.COLOR_GRAY2BGR)
    a_ = cv2.hconcat([frame, a_])
    return a_

def color(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s, 145, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    s_ = cv2.cvtColor(s_, cv2.COLOR_GRAY2BGR)
    s_ = cv2.hconcat([frame, s_])
    return s_

def detect_light(frame):
    """顏色轉換時EX 紅-> 綠有機會誤判藍 之類的，須加上一部份延遲做防誤判。
    """
    """
    R na>>nb
    G na~~nb
    B na<<nb                           

    """
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    r = frame[:,:,2]
    g = frame[:,:,1]
    b = frame[:, :, 0]
    a = r-g+220
    c = b-r+220
    ans = cv2.hconcat([a, c])
    ans = cv2.cvtColor(ans, cv2.COLOR_GRAY2BGR)
    ans = cv2.hconcat([frame, ans])
    _, a = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)
    _, c = cv2.threshold(c, 100, 255, cv2.THRESH_BINARY_INV)
    na = cv2.countNonZero(a)
    nb = cv2.countNonZero(c)
    ab = na/nb if nb else 999
    ba = nb/na if na else 999
    if na > 4000 or nb > 4000:
        if ab>30:
            print('R', na, nb)
        elif ba>30:
            print('B', na, nb)
        else:
            print('G', na, nb)
    else:
        print('X', na, nb)

    return ans

def detect_color(frame):
    pass

def has_color(frame):
    pass

def has_light(frame):
    pass

def has_finish_line(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]/180*255-int((180-15)/180*255)
    h = np.asarray(h, np.uint8)
    # h = h-(180+10)/180*255
    _, h_ = cv2.threshold(h, 40, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    h_ = cv2.cvtColor(h_, cv2.COLOR_GRAY2BGR)
    h_ = cv2.hconcat([frame, h_])
    return h_


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
                # cv2.imshow('Replay', show_all(frame))
                cv2.imshow('Replay', has_finish_line(frame))
                # if floor_has_color(frame):
                #     if detect_floor(frame, color='b'):
                #         print('bbbbbb')
                #     if detect_floor(frame, color='r'):
                #         print('rrrrrr')
                #     if detect_floor(frame, color='g'):
                #         print('gggggg')
                # detect(frame)
                while 1: 
                    inn = cv2.waitKey(0)
                    if inn & 0xFF == ord(' '):
                        break
                    if inn & 0xFF == ord('x'):
                        stop = 1
                        break
                    sleep(0.1)
            else:
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()