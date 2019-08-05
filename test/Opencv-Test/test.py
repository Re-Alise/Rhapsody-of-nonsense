import cv2
from time import time, sleep
cap = cv2.VideoCapture(0)
while 1:
    # get a frame
    # 我用筆電測試約0.03s能取出一張圖，時間沒到會卡在這，有點像是通訊在等對方丟值過來的感覺
    ret, frame = cap.read()
    # 處理
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    # 二值化(需要非常穩定)
    retval, thresh = cv2.threshold(blurred, 90, 255, cv2.THRESH_BINARY_INV)
    # 找輪廓
    contours,hierarchy=cv2.findContours(thresh,1,2)
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
    cX = int(sumX/sumW)
    cY = int(sumY/sumW)
    # show image
    # PS.他顯示的白色是黑色，黑色是白色
    cv2.imshow("capture", thresh)
    if cv2.waitKey(1) & 0xFF == ord(' '):
        break
cap.release()
cv2.destroyAllWindows()