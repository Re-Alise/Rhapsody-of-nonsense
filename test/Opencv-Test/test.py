import cv2
from time import time, sleep

ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)

LINE_THRESHOLD = (96, 96, 96)
BLUR_PIXEL = (5, 5)
CONTOUR_COLOR = (0, 255, 64) #BGR
CENTROID_COLOR = (0, 0, 255)  # BGR

cap = cv2.VideoCapture(0)

mask1 = cv2.imread('mask1.jpg', cv2.IMREAD_GRAYSCALE)
_, mask1 = cv2.threshold(mask1, 90, 255, cv2.THRESH_BINARY)
mask2 = cv2.imread('mask2.jpg', cv2.IMREAD_GRAYSCALE)
_, mask2 = cv2.threshold(mask2, 90, 255, cv2.THRESH_BINARY)
mask3 = cv2.imread('mask3.jpg', cv2.IMREAD_GRAYSCALE)
_, mask3 = cv2.threshold(mask3, 90, 255, cv2.THRESH_BINARY)

def find_center_error(frame, mask):
    frame = cv2.bitwise_and(frame, frame, mask=mask)
    contours, _ = cv2.findContours(frame,1,2)
    sumX=0
    sumY=0
    sumW=0
    
    for cnt in contours:
        M=cv2.moments(cnt)
        sumX += M['m10']
        sumY += M['m01']
        sumW += M['m00']
        # M['M00'] weight
        # M['m10'] xMoment
        # M['m01'] yMoment
    # 全畫面的黑色的中心座標
    if sumW == 0:
        print('No moments OwO')
        return frame, -1, -1
    cX = int(sumX/sumW)
    cY = int(sumY/sumW)
    return frame, cX, cY
    



if __name__ == "__main__":
    pp = []
    while 1:
        # get a frame
        # 我用筆電測試約0.03s能取出一張圖，時間沒到會卡在這，有點像是通訊在等對方丟值過來的感覺
        ret, frame = cap.read()
        now = time()
        frame = cv2.resize(frame, IMAGE_SIZE)
        # 處理
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        # 二值化(需要非常穩定)
        retval, thresh = cv2.threshold(blurred, 90, 255, cv2.THRESH_BINARY_INV)
        # 找輪廓
        dealt, xx, yy = find_center_error(thresh, mask3)
        # show image
        # PS.他顯示的白色是黑色，黑色是白色
        pp.append(time()-now)
        cv2.imshow("capture", dealt)
        print(xx-160)
        if cv2.waitKey(1) & 0xFF == ord(' '):
            break
    print(pp)
    cap.release()
    cv2.destroyAllWindows()