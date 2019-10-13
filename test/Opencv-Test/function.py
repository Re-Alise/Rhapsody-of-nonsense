import cv2
import os
import numpy as np
from time import sleep

# IMAGE_SIZE = (240, 320)# 高寬
IMAGE_SIZE = (320, 240)
path = "1570940397/"
# path = "./../video/"
fileName = "original.avi"
# fileName = "test8.avi"
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
def detect_light(sframe):
    """顏色轉換時EX 紅-> 綠有機會誤判藍 之類的，須加上一部份延遲做防誤判。
    """
    sframe = cv2.GaussianBlur(frame, gaussian, 0)
    r = sframe[:,:,2]
    g = sframe[:,:,1]
    b = sframe[:, :, 0]
    a = r-g+220
    c = b-r+200
    ans = cv2.hconcat([a, c])
    ans = cv2.cvtColor(ans, cv2.COLOR_GRAY2BGR)
    _, a = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)
    _, c = cv2.threshold(c, 100, 255, cv2.THRESH_BINARY_INV)
    na = cv2.countNonZero(a)
    nb = cv2.countNonZero(c)
    if na>10000:
        if nb>5000:
            print("G", na, nb)
            return ans
        else:
            print("R", na, nb)
            return ans
    else:
        if nb>5000:
            print("B", na, nb)
            return ans
        else:
            print("XX", na, nb)
            return ans
    return ans

# 測試版
def detect(sframe):
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
    if na>10000:
        if nb>5000:
            print("G", na, nb)
            return ans
        else:
            print("R", na, nb)
            return ans
    else:
        if nb>5000:
            print("B", na, nb)
            return ans
        else:
            print("XX", na, nb)
            return ans
    return ans

def black(frame):
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    r = frame[:,:,2]
    b = frame[:,:,0]
    c = b-r+180
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thr = cv2.threshold(gray,70,255,cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    # thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 2)
    # thr = cv2.cvtColor(thr, cv2.COLOR_GRAY2BGR)
    return cv2.hconcat([gray, thr])

def test(frame):
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    r = frame[:,:,2]
    g = frame[:, :, 1]
    b = frame[:, :, 0]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    _, s_ = cv2.threshold(s,100,255,cv2.THRESH_BINARY)
    # v = np.bitwise_or(s_, v)
    _, v_ = cv2.threshold(s,80,255,cv2.THRESH_BINARY)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]/180*255-(54-10)*255/180
    h = np.asarray(h, np.uint8)


    _, bb_ = cv2.threshold(h,20,255,cv2.THRESH_BINARY_INV)
    ans1 = cv2.hconcat([r, g, b])
    ans1 = cv2.cvtColor(ans1, cv2.COLOR_GRAY2BGR)
    ans1 = cv2.hconcat([frame, ans1])
    ans2 = cv2.hconcat([b-r+180, s_, s, h])
    ans2 = cv2.cvtColor(ans2, cv2.COLOR_GRAY2BGR)
    ans = cv2.vconcat([ans1, ans2])
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

def fake_line(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s,180,255,cv2.THRESH_BINARY_INV)
    v = hsv[:, :, 2]
    v = np.bitwise_and(s_, v)
    _, v_ = cv2.threshold(s,80,255,cv2.THRESH_BINARY)
    

    pass

def mixbin(frame):
    """
    normal: use b-r+180
    rgb light: use v and use muti line to create a fake line
    rgb floor: use v and use muti line to create a fake line
    """
    pass

def _general_binarization(frame):
    # fun1
    # frame = cv2.GaussianBlur(frame, (25, 25), 0)
    # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # # _, thr = cv2.threshold(gray,60,255,cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    # thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 13, self.c)
    # # thr = cv2.morphologyEx(thr, cv2.MORPH_CLOSE, kernel)
    # thr = cv2.morphologyEx(thr, cv2.MORPH_OPEN, kernel)


    # fun 2
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    r = frame[:,:,2]
    b = frame[:, :, 0]
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, gray_ = cv2.threshold(gray, 80, 255, cv2.THRESH_BINARY_INV)# +cv2.THRESH_OTSU)
    c = b-r+180
    # c = np.minimum(np.maximum(c, 0), 255)
    c = np.asarray(c, np.uint8)
    _, c_ = cv2.threshold(c, 160, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
    binarized_frame = np.bitwise_and(c_, gray_)
    return binarized_frame

def _mask(frame2d, mask=(None, None, 0, 0), img_size=IMAGE_SIZE):
    """mask -> (width, hight, offset_x, offset_y),width and hight are half value
    """
    width, hight, offset_x, offset_y = mask
    mask = np.zeros(img_size,dtype=np.uint8)
    center_point_x = img_size[1]//2 + offset_x
    center_point_y = img_size[0]//2 + offset_y
    if not hight and not width:
        return frame2d
    elif not hight:
        x1 = center_point_x-width
        x2 = center_point_x+width
        y1 = 0
        y2 = img_size[0]
        # vartical
        pass
    elif not width:
        x1 = 0
        x2 = img_size[1]
        y1 = center_point_y-hight
        y2 = center_point_y+hight
        # horz.tal
        pass
    else:
        x1 = center_point_x-width
        x2 = center_point_x+width
        y1 = center_point_y-hight
        y2 = center_point_y+hight
    
    mask[y1:y2,x1:x2] = 255
    masked = np.bitwise_and(frame2d, mask)
    return masked


    pass


def _find_center(frame2d, mask, data, error_num=10):
    "mask: (width, hight, offset_x, offset_y),\ndata: 'x', 'y', 'w'"
    thr =_mask(frame2d, mask=mask)

    center_point_x = IMAGE_SIZE[1]//2 + mask[2]
    center_point_y = IMAGE_SIZE[0]//2 - mask[3]
    sumX=0
    sumY=0
    sumW=0
    
    contours, _ = cv2.findContours(thr,1,2)

    for cnt in contours:
        M=cv2.moments(cnt)
        if M['m00']<100:
            continue
        sumX += M['m10']
        sumY += M['m01']
        sumW += M['m00']
        # M['M00'] weight
        # M['m10'] xMoment
        # M['m01'] yMoment
    # 全畫面的黑色的中心座標
    if sumW == 0:
        print('Not found')
        # 因為 很多程式重複使用 故無法繼續使用舊值
        cX = center_point_x
        cY = center_point_y
    else:
        cX = sumX/sumW  
        cY = sumY/sumW
    
    if data == 'x':
        self.feedback_queue.put((0, (center_point_x, center_point_y), (int(cX), center_point_y)))
        return cX - center_point_x
    if data == 'y':
        self.feedback_queue.put((0, (center_point_x, center_point_y), (center_point_x, int(cY))))
        return center_point_y - cY
    if data == 'w':
        return sumW

def floor_has_color(frame):
    # b100, r180, g54
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]
    _, s_ = cv2.threshold(s,100,255,cv2.THRESH_BINARY)
    hW = _find_center(s_, (None, None, 0, 0), data='w')
    if hW > 3000:
        return 1
    else:
        return 0

def detect_floor(frame, color='r'):
    # b100, r180, g54
    hRange=10
    if color=='r':
        offset=255
    elif color=='g':
        offset=54*255/180
    elif color=='b':
        offset=100*255/180
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]/180*255-offset+hRange
    h = np.asarray(h, np.uint8)
    _, h_ = cv2.threshold(h,2*hRange,255,cv2.THRESH_BINARY_INV)
    hW = _find_center(h_, (50, 50, 0, 0), data='w')
    # print(hW)
    if hW > 3000:
        return 1
    else:
        return 0


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
                cv2.imshow('Replay', test(frame))
                if floor_has_color(frame):
                    if detect_floor(frame, color='b'):
                        print('bbbbbb')
                    if detect_floor(frame, color='r'):
                        print('rrrrrr')
                    if detect_floor(frame, color='g'):
                        print('gggggg')
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
