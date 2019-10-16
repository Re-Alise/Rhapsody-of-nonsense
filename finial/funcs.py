import cv2
import os
import numpy as np
from time import sleep, time

# from menu import MENU

useCarema = 1

IMAGE_SIZE = (320, 240)
IMAGE_SIZE = (240, 320)
path = "slice_video/"

path = "./../video/"
# path = "C:\\Users\\YUMI.Lin\\Desktop\\video\\"
# fileName = "radline.avi"
save_path = 'paraout/'

fileName = "1570964034.avi"
fileName = "color2.avi"
gaussian = (13, 13)
kernel = np.ones((3,3),np.uint8)
adjust = 0

select = 0
display = 0
show_num = 6


target_color = 0
step = -1

# PARAMETER
use_auto_c = 0
normal_offset = 180
normal_threshold = 100
gray_threshold = 100
na_offset = 220
nb_offset = 220
light_threshold = 100
saturation_threshold = 145
hue_range = 20
hue_threshold = 2*hue_range
hue_red = 180 # use overfloat value don't use value like 1, 0, 5 etc..
hue_green = 90
hue_blue = 120
hue_floor = 24

default_drop_color = 3
default_land_color = 2


# 條件
na_min = 4000
nb_min = 4000
drop_min = 20000
has_color_min = 10000
has_finishline_min = 1000
big_red_min = drop_min
big_color_min = 20000
floor_forward_min = 10
floor_min = 100

# MASK
MASK_FORWARD = (None, 25, 0, 85)
MASK_DROP = (None, 60, 0, 0)
"""
parameters:
    normal_offset:      
    normal_threshold:   up to more
    gray_threshold:             
    na_offset:              
    nb_offset:              
    light_threshold:                
    saturation_threshold:               
    hue_range:              
    hue_threshold:              *hue_range
    hue_red:                
    hue_green:              
    hue_blue:               

"""
"""
TODO:
    全部數字 參數化
    並設計快速條參數程式
    錄影與再放程式更改為正式使用版(橫向與切割) -> 方便條參數 frame, h, s, v, r-g+220, b-r+220, b-r+180, gray, 顯示各大判斷式的原始數值(與判斷標準)
    可能 自動條參數?
        (讀取影片) 拍照(多張) FOR  SAVE選定參數 上下微調 確定 NEXT SAVE
    條件偵測優化 防誤判
    選單方向鍵控制
"""


names = [
    'normal_offset',
    'normal_threshold',
    'gray_threshold',
    'na_offset',
    'nb_offset',
    'light_threshold',
    'saturation_threshold',
    'hue_range',
    'hue_threshold',
    'hue_red',
    'hue_green',
    'hue_blue',
    'hue_floor',
]
modes = [
    'normal,\tc, gray',
    'light,\ta, b, a_',
    'color,\ts',
    'red, r,\ts, h',
    'green,\tg, s, h',
    'blue,\tb, s, h',
    'floor,\tf, s'
]

# def select_pics()

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
    global step
    global color
    print('step:', step)
    if step == 0:
        if has_light(frame):
            step = 1
        return normal_map(frame)
    elif step == 1:
        if detect_light(frame)>1:# or timeout
            color = detect_light
            step = 2
        return light_map(frame)
    elif step == 2:
        if has_color(frame):
            step = 3
        return normal_map(frame)
    elif step == 3:
        if not has_color(frame):
            step = 4
        if has_color == color:
            pass
            # drop
        return color_map(frame)
    elif step == 4:
        if has_finish_line(frame):
            step = 5
        return normal_map(frame)
    elif step == 5:
        # 盲走
        if has_big_red(frame):
            step = 6
        return frame
    elif step == 6:
        if has_finish_color(frame):
            step = 7
        return red_map(frame)
    elif step == 7:
        if on_the_finish_color(frame):
            step = 8
        return finish_color_map
    else:
        return frame

def normal_map(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    r = frame[:,:,2]
    b = frame[:, :, 0]
    c = b-r+ normal_offset
    _, c_ = cv2.threshold(c, normal_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    # c_ = cv2.cvtColor(c_, cv2.COLOR_GRAY2BGR)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, gray_ = cv2.threshold(gray, gray_threshold, 255, cv2.THRESH_BINARY_INV)# +cv2.THRESH_OTSU)
    # binarized_frame = np.bitwise_and(c_, gray_)
    binarized_frame = c_
    binarized_frame = cv2.cvtColor(binarized_frame, cv2.COLOR_GRAY2BGR)
    gray_ = cv2.cvtColor(gray_, cv2.COLOR_GRAY2BGR)
    binarized_frame = cv2.hconcat([frame, binarized_frame, gray_])
    return binarized_frame

def light_map(frame):
    frame = cv2.GaussianBlur(frame, gaussian, 0)
    r = frame[:,:,2]
    g = frame[:,:,1]
    b = frame[:, :, 0]
    a = r-g+ na_offset
    c = b-r+ nb_offset
    _, a_ = cv2.threshold(a, 100, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    tmp = cv2.hconcat([a, c, a_])
    tmp = cv2.cvtColor(tmp, cv2.COLOR_GRAY2BGR)
    a_ = cv2.hconcat([frame, tmp])
    return a_

def color_map(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    s_ = cv2.cvtColor(s_, cv2.COLOR_GRAY2BGR)
    s_ = cv2.hconcat([frame, s_])
    return s_

def red_map(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    h = hsv[:, :, 0]/180*255-int((hue_red-hue_range)/180*255)
    h = np.asarray(h, np.uint8)
    _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    red = np.bitwise_and(s_, h_)
    tmp = cv2.hconcat([red, s_, h_])
    tmp = cv2.cvtColor(tmp, cv2.COLOR_GRAY2BGR)
    tmp = cv2.hconcat([frame, tmp])
    return tmp

def green_map(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    h = hsv[:, :, 0]/180*255-int((hue_green-hue_range)/180*255)
    h = np.asarray(h, np.uint8)
    _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    green = np.bitwise_and(s_, h_)
    tmp = cv2.hconcat([green, s_, h_])
    tmp = cv2.cvtColor(tmp, cv2.COLOR_GRAY2BGR)
    tmp = cv2.hconcat([frame, tmp])
    return tmp

def blue_map(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    h = hsv[:, :, 0]/180*255-int((hue_blue-hue_range)/180*255)
    h = np.asarray(h, np.uint8)
    _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    blue = np.bitwise_and(s_, h_)
    tmp = cv2.hconcat([blue, s_, h_])
    tmp = cv2.cvtColor(tmp, cv2.COLOR_GRAY2BGR)
    tmp = cv2.hconcat([frame, tmp])
    return tmp

def floor_map(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]/180*255-int((hue_floor-hue_range)/180*255)
    h = np.asarray(h, np.uint8)
    _, floor = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    # floor = np.bitwise_and(s_, h_)
    tmp = cv2.hconcat([floor, h])
    tmp = cv2.cvtColor(tmp, cv2.COLOR_GRAY2BGR)
    tmp = cv2.hconcat([frame, tmp])
    return tmp

def finish_color_map(frame):
    if color == 2:
        color_offset = hue_blue
    else: # 如果是然色或是綠色 通通 去綠色降落
        color_offset = hue_green
        
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    h = hsv[:, :, 0]/180*255-int((color_offset-hue_range)/180*255)
    h = np.asarray(h, np.uint8)
    _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    color = np.bitwise_or(s_, h_)
    return color

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
    a = r-g+ na_offset
    c = b-r+ nb_offset
    ans = cv2.hconcat([a, c])
    ans = cv2.cvtColor(ans, cv2.COLOR_GRAY2BGR)
    ans = cv2.hconcat([frame, ans])
    _, a = cv2.threshold(a, light_threshold, 255, cv2.THRESH_BINARY_INV)
    _, c = cv2.threshold(c, light_threshold, 255, cv2.THRESH_BINARY_INV)
    na = cv2.countNonZero(a)
    nb = cv2.countNonZero(c)
    ab = na/nb if nb else 999
    ba = nb/na if na else 999
    if na > na_min or nb > nb_min:
        if ab>30:
            print('R', na, nb)
            return 1
        elif ba>30:
            print('B', na, nb)
            return 2
        else:
            print('G', na, nb)
            return 3
    else:
        # print('X', na, nb)
        return 0

    return ans

def has_drop_color(frame):
    # if color == 3:
    #     color_offset = hue_green
    # else: # 如果是藍色或是其他 通通 去藍色投擲(因為剛進去比較穩?)
    #     color_offset = hue_blue
        
    # frame = cv2.GaussianBlur(frame, (13, 13), 0)
    # hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    # s = hsv[:, :, 1]
    # _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    # h = hsv[:, :, 0]/180*255-int((color_offset-hue_range)/180*255)
    # h = np.asarray(h, np.uint8)
    # _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    # color = np.bitwise_and(s_, h_)
    # color_mask = _mask(color, (None, 100, 0, 0))
    # nc = cv2.countNonZero(color_mask)
    # if nc > drop_min:
    #     return 1
    # else:
    #     return 0
    saturation_binarized = get_saturation_binarized(frame)
    saturation_binarized = _mask(saturation_binarized, MASK_DROP)
    green_hue_binarized = get_hue_binarized(frame, hue_green)
    green_binarized = bin_and(saturation_binarized, green_hue_binarized)
    if get_weight(green_binarized) > drop_min:
        return 1
    if color == 3:
        blue_hue_binarized = get_hue_binarized(frame, hue_blue)
        blue_binarized = bin_and(saturation_binarized, blue_hue_binarized)
        if get_weight(blue_binarized) > drop_min:
            return 1
    return 0


def has_finish_color(frame):
    if color == 2:
        color_offset = hue_blue
    else: # 如果是綠色或是其他 通通 去綠色投擲(因為分散風險?)
        color_offset = hue_green
        
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    h = hsv[:, :, 0]/180*255-int((color_offset-hue_range)/180*255)
    h = np.asarray(h, np.uint8)
    _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    color = np.bitwise_or(s_, h_)
    color_mask = _mask(color, (None, None, 0, 0))
    nc = cv2.countNonZero(color_mask)
    if nc > 5000:
        return 1
    else:
        return 0

def has_color(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    s__ = _mask(s_, (None, 80, 0, 40))
    # s_ = cv2.cvtColor(s_, cv2.COLOR_GRAY2BGR)
    ns = cv2.countNonZero(s__)
    if ns > has_color_min:
        return 1
    else:
        return 0


def has_light(frame):
    if detect_light(frame)>0:
        return 1
    else:
        return 0

def has_finish_line(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]/180*255-int((180-15)/180*255)
    h = np.asarray(h, np.uint8)
    _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    nh = cv2.countNonZero(h_)
    if nh>has_finishline_min:
        return 1
    else:
        return 0
    return h_

def has_big_red(frame):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]/180*255-int((180-15)/180*255)
    h = np.asarray(h, np.uint8)
    _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    nh = cv2.countNonZero(h_)
    if nh>big_color_min:
        return 1
    else:
        return 0

def on_the_finish_color(frame):
    if color == 2:
        color_offset = hue_blue
    else: # 如果是然色或是綠色 通通 去綠色降落
        color_offset = hue_green

    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]/180*255-int((color_offset-hue_range)/180*255)
    h = np.asarray(h, np.uint8)
    _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    nh = cv2.countNonZero(h_)
    # maybe error 小於某值 且不=0
    if nh>20000:
        return 1
    else:
        return 0
    pass

def _mask(frame, mask=(None, None, 0, 0), img_size=IMAGE_SIZE):
    """mask -> (width, hight, offset_x, offset_y),width and hight are half value
    """
    width, hight, offset_x, offset_y = mask
    mask = np.zeros(img_size,dtype=np.uint8)
    center_point_x = img_size[1]//2 + offset_x
    center_point_y = img_size[0]//2 - offset_y

    if not width:
        x1 = 0
        x2 = img_size[1]
    else:
        x1 = center_point_x-width
        x2 = center_point_x+width

    if not hight:
        y1 = 0
        y2 = img_size[0]
    else:
        y1 = center_point_y-hight
        y2 = center_point_y+hight
    
    mask[y1:y2,x1:x2] = 255
    masked = np.bitwise_and(frame, mask)
    return masked

def condition_all_floor():
    floor_bin = get_hue_binarized(hue_floor, invert=1)
    floor_bin_forward = _mask(floor_bin, MASK_FORWARD)
    if cv2.countNonZero(floor_bin) < floor_forward_min:
        if cv2.countNonZero(floor_bin_forward) < floor_min:
            return 1
    return 0

def get_hue_binarized(frame, hue=180, invert=0):
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    h = hsv[:, :, 0]/180*255-int((hue-hue_range)/180*255)
    h = np.asarray(h, np.uint8)
    if invert:
        _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    else:
        _, h_ = cv2.threshold(h, hue_threshold, 255, cv2.THRESH_BINARY_INV)#+cv2.THRESH_OTSU)
    return h_

def get_saturation_binarized(frame):    
    frame = cv2.GaussianBlur(frame, (13, 13), 0)
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    s = hsv[:, :, 1]
    _, s_ = cv2.threshold(s, saturation_threshold, 255, cv2.THRESH_BINARY)#+cv2.THRESH_OTSU)
    return s_

def get_weight(bined):
    return cv2.countNonZero(bined)

def bin_and(frame1, frame2):
    return np.bitwise_and(frame1, frame2)

def bin_or(frame1, frame2):
    return np.bitwise_or(frame1, frame2)


class MENU():
    def __init__(self, ):
        self.display = 0
        self.select = 0
        self.show_num = 6
        self.mode = 0
    
    def creat_list(self, ):
        global normal_offset
        global normal_threshold
        global gray_threshold
        global na_offset
        global nb_offset
        global light_threshold
        global saturation_threshold
        global hue_range
        global hue_threshold
        global hue_red
        global hue_green
        global hue_blue
        dd = {
            0: ('normal_offset', normal_offset,''),
            1: ('normal_threshold', normal_threshold,''),
            2: ('gray_threshold', gray_threshold,''),
            3: ('na_offset', na_offset,''),
            4: ('nb_offset', nb_offset,''),
            5: ('light_threshold', light_threshold,''),
            6: ('saturation_threshold', saturation_threshold,''),
            7: ('hue_range', hue_range,''),
            8: ('hue_threshold', hue_threshold,''),
            9: ('hue_red', hue_red,''),
            10: ('hue_green', hue_green,''),
            11: ('hue_blue', hue_blue,''),
            12: ('hue_floor', hue_floor, ''),
            13: ('----end----', '', ''),
            # '----end----': 
        }
        return dd

    def show_menu(self, ):
        img = np.zeros(IMAGE_SIZE,dtype=np.uint8)
        color_select_background = 230
        color_select_word = 0
        color_word = 180
        text_size = 0.5
        ss = self.creat_list()
        for i in range(6):
            # ss[i][0], ss[i][1]
        # for i, s in enumerate(ss):
            if i == select:
                cv2.rectangle(img, (0, 10+i*20), (IMAGE_SIZE[0], 10+i*20+20), (color_select_background, color_select_background, color_select_background), -1)
                cv2.putText(img, ss[i+display][0], (10, 25+i * 20), cv2.FONT_HERSHEY_SIMPLEX, text_size, (color_select_word, color_select_word, color_select_word), 1)
                cv2.putText(img, str(ss[i+display][1]), (180, 25+i * 20), cv2.FONT_HERSHEY_SIMPLEX, text_size, (color_select_word, color_select_word, color_select_word), 1)
            else:
                cv2.putText(img, ss[i+display][0], (10, 25+i * 20), cv2.FONT_HERSHEY_SIMPLEX, text_size, (color_word, color_word, color_word), 1)
                cv2.putText(img, str(ss[i+display][1]), (180, 25+i * 20), cv2.FONT_HERSHEY_SIMPLEX, text_size, (color_word, color_word, color_word), 1)
        cv2.putText(img, modes[self.mode], (10, 200), cv2.FONT_HERSHEY_SIMPLEX, 1, (color_word, color_word, color_word), 1)
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    def up(self, ):
        global select, display
        if select == 0:
            if not display == 0:
                display -= 1
        else:
            select -= 1

    def down(self, ):
        global select, display
        if select == self.show_num-1:
            if not display == 14-self.show_num:
                display += 1
        else:
            select += 1

    def left(self, offect_num):
        global names
        global normal_offset
        global normal_threshold
        global gray_threshold
        global na_offset
        global nb_offset
        global light_threshold
        global saturation_threshold
        global hue_range
        global hue_threshold
        global hue_red
        global hue_green
        global hue_blue
        global hue_floor
        now_select = names[display+select]
        if now_select == 'normal_offset':
            normal_offset = normal_offset - offect_num
        if now_select == 'normal_threshold':
            normal_threshold = normal_threshold - offect_num
        if now_select == 'gray_threshold':
            gray_threshold = gray_threshold - offect_num
        if now_select == 'na_offset':
            na_offset = na_offset - offect_num
        if now_select == 'nb_offset':
            nb_offset = nb_offset - offect_num
        if now_select == 'light_threshold':
            light_threshold = light_threshold - offect_num
        if now_select == 'saturation_threshold':
            saturation_threshold = saturation_threshold - offect_num
        if now_select == 'hue_range':
            hue_range = hue_range - offect_num
        if now_select == 'hue_threshold':
            hue_threshold = hue_threshold - offect_num
        if now_select == 'hue_red':
            hue_red = hue_red - offect_num
        if now_select == 'hue_green':
            hue_green = hue_green - offect_num
        if now_select == 'hue_blue':
            hue_blue = hue_blue - offect_num
        if now_select == 'hue_floor':
            hue_floor = hue_floor-offect_num

    def right(self, offect_num):
        global names
        global normal_offset
        global normal_threshold
        global gray_threshold
        global na_offset
        global nb_offset
        global light_threshold
        global saturation_threshold
        global hue_range
        global hue_threshold
        global hue_red
        global hue_green
        global hue_blue
        global hue_floor
        now_select = names[display+select]
        if now_select == 'normal_offset':
            normal_offset = normal_offset + offect_num
        if now_select == 'normal_threshold':
            normal_threshold = normal_threshold + offect_num
        if now_select == 'gray_threshold':
            gray_threshold = gray_threshold + offect_num
        if now_select == 'na_offset':
            na_offset = na_offset + offect_num
        if now_select == 'nb_offset':
            nb_offset = nb_offset + offect_num
        if now_select == 'light_threshold':
            light_threshold = light_threshold + offect_num
        if now_select == 'saturation_threshold':
            saturation_threshold = saturation_threshold + offect_num
        if now_select == 'hue_range':
            hue_range = hue_range + offect_num
        if now_select == 'hue_threshold':
            hue_threshold = hue_threshold + offect_num
        if now_select == 'hue_red':
            hue_red = hue_red + offect_num
        if now_select == 'hue_green':
            hue_green = hue_green + offect_num
        if now_select == 'hue_blue':
            hue_blue = hue_blue + offect_num
        if now_select == 'hue_floor':
            hue_floor = hue_floor+offect_num

    def show(self):
        if self.mode == 0:
            return normal_map(frame)
        elif self.mode == 1:
            return light_map(frame)
        elif self.mode == 2:
            return color_map(frame)
        elif self.mode == 3:
            return red_map(frame)
        elif self.mode == 4:
            return green_map(frame)
        elif self.mode == 5:
            return blue_map(frame)
        elif self.mode == 6:
            return floor_map(frame)

    def chmod(self, mode):
        self.mode = mode

    def nextmode(self):
        self.mode += 1
        self.mode %= 7

if __name__ == "__main__":
    try:
        if useCarema:
            cap = cv2.VideoCapture(2)
        else: 
            cap = cv2.VideoCapture(path+fileName)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_SIZE[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_SIZE[1])
        time_str = str(int(time()))
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(save_path + time_str + '.avi', fourcc,
            30.0, (IMAGE_SIZE[1], IMAGE_SIZE[0]))
        stop = 0
        pause = 0
        pause_ = 1
        menu = MENU()
        while cap.isOpened():
            if stop:
                break
            ret, frame_ = cap.read()
            out.write(frame_)
            if not pause:
                frame = frame_
            if ret:
                print(menu.mode)
                cv2.imshow('Replay', cv2.hconcat([menu.show_menu(),menu.show()]))
                # cv2.imshow('Replay', cv2.hconcat([menu.show()]))
                # cv2.imshow('Replay', show_menu())
                # while 1: 
                inn = cv2.waitKey(1)
                # if inn & 0xFF == ord(' '):
                    # break
                # Upkey : 2490368
                # DownKey : 2621440
                # LeftKey : 2424832
                # RightKey: 2555904
                # Space : 32
                # Delete : 3014656
                switch = {
                    84: lambda : menu.down(),
                    82: lambda : menu.up(),
                    81: lambda : menu.left(1),
                    83: lambda : menu.right(1),
                    87: lambda : menu.nextmode(),
                    32: lambda : menu.nextmode(),
                    # 'h': lambda : menu.left(10),
                    # ';': lambda : menu.right(10),
                    # 'u': lambda : menu.left(1000),
                    # "o": lambda : menu.right(1000),
                }
                # print(inn)
                for key in switch:
                    if inn == key:
                        switch[key]()
                if inn & 0xFF == ord('x'):
                    stop = 1
                    # break
                if inn & 0xFF == ord('s'):
                    step = 0
                if inn & 0xFF == ord('p'):
                    if pause_:
                        pause = not pause
                        pause_ = 0
                else:
                    pause_ = 1
                    # sleep(0.1)
            else:
                break
    finally:
        cap.release()
        out.release()
        cv2.destroyAllWindows()