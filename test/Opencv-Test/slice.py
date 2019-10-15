from time import time
import numpy as np

import os
import cv2

ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)
IMAGE_SIZE = (240, 320)
path = "video_water/Night/"
fileName = "1570964034.avi"
cap = cv2.VideoCapture(path+fileName)

# cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_SIZE[0])
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_SIZE[1])
fourcc = cv2.VideoWriter_fourcc(*'XVID')
time_str = str(int(time()))
# os.mkdir(time_str)
out = cv2.VideoWriter('slice_video/' + fileName, fourcc,
    30.0, (IMAGE_SIZE[1], IMAGE_SIZE[0]))
print('start')
print(cap.isOpened())
while(cap.isOpened()):
  ret, frame = cap.read()
  if ret == True:
    frame = frame[0:IMAGE_SIZE[0], 0:IMAGE_SIZE[1], :]
    # 寫入影格
    if type(frame) is not np.ndarray:
        break
    print(frame.shape)
    out.write(frame)

    cv2.imshow('frame',frame)
    if cv2.waitKey(1) & 0xFF == ord(' '):
      break
  else:
    break

# 釋放所有資源
cap.release()
out.release()
cv2.destroyAllWindows()