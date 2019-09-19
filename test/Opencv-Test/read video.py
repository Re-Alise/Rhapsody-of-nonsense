from time import time, sleep

import os
import cv2

path = '/home/yumi/Desktop/1568871048/original.avi'

cap = cv2.VideoCapture(path)
while(cap.isOpened()):
  ret, frame = cap.read()
  if ret == True:

    cv2.imshow('frame',frame)
    while not cv2.waitKey(0) & 0xFF == ord(' '):
        sleep(0.1)       
  else:
    break

# 釋放所有資源
cap.release()
cv2.destroyAllWindows()