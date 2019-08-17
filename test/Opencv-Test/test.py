import cv2
from time import time, sleep
import numpy as np
cap = cv2.VideoCapture(2)
target = 0

ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)

LINE_THRESHOLD = (96, 96, 96)
BLUR_PIXEL = (5, 5)
CONTOUR_COLOR = (0, 255, 64) #BGR
CENTROID_COLOR = (0, 0, 255)  # BGR

ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)

LINE_THRESHOLD = (96, 96, 96)
BLUR_PIXEL = (5, 5)
CONTOUR_COLOR = (0, 255, 64)  # BGR
CENTROID_COLOR = (0, 0, 255)  # BGR

MASK_ALL = np.zeros([240, 320], dtype=np.uint8)
MASK_ALL[0:240, 0:320] = 255

MASK_FORWARD = np.zeros([240, 320], dtype=np.uint8)
MASK_FORWARD[10:90, 10:310] = 255

MASK_TOP = np.zeros([240, 320], dtype=np.uint8)
MASK_TOP[0:120, 0:320] = 255

MASK_BUTTON = np.zeros([240, 320], dtype=np.uint8)
MASK_BUTTON[121:240, 0:320] = 255

MASK_LINE_MIDDLE = np.zeros([240, 320], dtype=np.uint8)
MASK_LINE_MIDDLE[101:140, 81:240] = 255

MASK_RIGHT = np.zeros([240, 320], dtype=np.uint8)
MASK_RIGHT[106:320, 0:240] = 255


def find_center(frame, mask):
    frame = cv2.bitwise_and(frame, frame, mask=mask)
    contours, _ = cv2.findContours(frame, 1, 2)
    sumX = 0
    sumY = 0
    sumW = 0
    for cnt in contours:
        M = cv2.moments(cnt)
        sumX += M['m10']
        sumY += M['m01']
        sumW += M['m00']
        # M['M00'] weight
        # M['m10'] xMoment
        # M['m01'] yMoment
    # 全畫面的黑色的中心座標
    if sumW == 0:
        print('Not found')
        return -1, -1, 0
    cX = int(sumX/sumW)
    cY = int(sumY/sumW)
    return cX, cY, sumW
    



if __name__ == "__main__":
    pp = []
    while 1:
        # get a frame
        # 我用筆電測試約0.03s能取出一張圖，時間沒到會卡在這，有點像是通訊在等對方丟值過來的感覺
        ret, ori = cap.read()
        now = time()
        frame = cv2.resize(ori, IMAGE_SIZE)
        frame = cv2.GaussianBlur(frame, (9, 9), 0)
        # 處理
        r = frame[:,:,2]
        g = frame[:,:,1]
        b = frame[:,:,0]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if target == 0:
            img = b-gray
        elif target == 1:
            img = g-gray
        elif target == 2:
            img = r-gray
        elif target == 3:
            img = gray
        # # 二值化(需要非常穩定)
        # retval, thresh = cv2.threshold(blurred, 90, 255, cv2.THRESH_BINARY_INV)
        # # 找輪廓
        # xx, yy, ww = find_center(thresh, MASK_ALL)
        ret3,th1 = cv2.threshold(r-gray+100,150,255,cv2.THRESH_BINARY)
        ret3,th2 = cv2.threshold(g-gray+100,120,255,cv2.THRESH_BINARY)
        ret3,th3 = cv2.threshold(b-gray+100,100,255,cv2.THRESH_BINARY)
        ret3,th0 = cv2.threshold(gray,100,255,cv2.THRESH_BINARY)
        # show image
        # PS.他顯示的白色是黑色，黑色是白色
        # pp.append(time()-now)
        ans = np.hstack((th1, th2, th3, th0))
        cv2.imshow("capture", ans)
        # print(xx-160)
        if cv2.waitKey(1) & 0xFF == ord(' '):
            break
    print(pp)   
    cap.release()
    cv2.destroyAllWindows()
