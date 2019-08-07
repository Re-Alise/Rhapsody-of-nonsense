import numpy as np
import cv2

MASK_ALL = np.zeros([240, 320],dtype=np.uint8)
MASK_ALL[0:240, 0:320] = 255

MASK_FORWARD = np.zeros([240, 320],dtype=np.uint8)
MASK_FORWARD[10:90, 10:310] = 255

MASK_FORWARDs = np.zeros([240, 320],dtype=np.uint8)
MASK_FORWARDs[30:70, 10:310] = 255

MASK_TOP = np.zeros([240, 320],dtype=np.uint8)
MASK_TOP[0:120, 0:320] = 255

MASK_BUTTON = np.zeros([240, 320],dtype=np.uint8)
MASK_BUTTON[121:240, 0:320] = 255

MASK_LINE_MIDDLE = np.zeros([240, 320],dtype=np.uint8)
MASK_LINE_MIDDLE[101:140, 81:240] = 255

MASK_RIGHT = np.zeros([240, 320],dtype=np.uint8)
MASK_RIGHT[106:320, 0:240] = 255


# cv2.imshow('123', MASK_LINE_MIDDLE)
# cv2.waitKey(0)
# cv2.destroyAllWindows()