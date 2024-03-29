from time import time

import os
import cv2

ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)
cap = cv2.VideoCapture(2)

# 設定擷取影像的尺寸大小
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

# # 使用 XVID 編碼
# fourcc = cv2.VideoWriter_fourcc(*'XVID')

# 建立 VideoWriter 物件，輸出影片至 output.avi
# FPS 值為 20.0，解析度為 640x360

cap.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_SIZE[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_SIZE[1])
fourcc = cv2.VideoWriter_fourcc(*'XVID')
time_str = str(int(time()))
os.mkdir(time_str)
out = cv2.VideoWriter(time_str + '/original' + '.avi', fourcc,
    30.0, (IMAGE_SIZE[1], IMAGE_SIZE[0]))
# out = cv2.VideoWriter('output.avi', fourcc, 20.0, (640, 360))

while(cap.isOpened()):
  ret, frame = cap.read()
  if ret == True:
    frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    # 寫入影格
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