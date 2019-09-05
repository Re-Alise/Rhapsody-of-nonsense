from time import time

import cv2
import numpy as np

ORIGINAL_IMAGE_SIZE = (640, 480)
IMAGE_SIZE = (320, 240)

LINE_THRESHOLD = (96, 96, 96)
BLUR_PIXEL = (5, 5)
CONTOUR_COLOR = (0, 255, 64)  # BGR
CENTROID_COLOR = (0, 0, 255)  # BGR

capture = cv2.VideoCapture(0)
# capture.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_SIZE[0])
# capture.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_SIZE[1])


def make_contour(im, imm):
    contours, _ = cv2.findContours(im, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    output = np.zeros((IMAGE_SIZE[1], IMAGE_SIZE[0]), np.uint8)

    if len(contours) == 0:
        print('No contour found')
        return None, output

    # print(contours)
    size_list = []
    for i in range(len(contours)):
        contour = contours[i]
        # print(type(contour), contour.shape)

        min_bound = contour.min(axis=0)
        max_bound = contour.max(axis=0)

        # print(min_bound[0], max_bound[0])
        bound = max_bound-min_bound
        contour_size = (bound[0][0], bound[0][1], i)
        size_list.append(contour_size)
        # print('Contour size:', contour_size)

    size_list_sorted = sorted(size_list, key=lambda x: x[0]*x[1], reverse=True)
    contour_index = size_list_sorted[0][-1]
    target_contour = contours[contour_index]

    # convex = cv2.convexHull(target_contour, returnPoints=True)
    # print(convex)

    cv2.fillConvexPoly(output, target_contour, 255)

    # cv2.drawContours(imm, contours, contour_index, CONTOUR_COLOR, 3)
    return target_contour, output


def make_centroid(im, imm):
    moments = cv2.moments(im)
    # print(moments)

    if 0 in moments.values():
        print('No moments OwO')
        return (-1, -1)

    center_x = int(moments['m10']/moments['m00'])
    center_y = int(moments['m01']/moments['m00'])

    cv2.circle(imm, (center_x, center_y), 5, CENTROID_COLOR, -1)
    return (center_x, center_y)


if __name__ == '__main__':
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, IMAGE_SIZE[0])
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, IMAGE_SIZE[1])
    fourcc = cv2.VideoWriter_fourcc(*'DIVX')
    out = cv2.VideoWriter(str(time()) + '.avi', fourcc,
                          30.0, (IMAGE_SIZE[0], IMAGE_SIZE[1]))
    while True:
        cret, frame = capture.read()
        out.write(frame)
        cv2.imshow('VideoWriter test', frame)

        if cv2.waitKey(1) & 0xFF == ord(' '):
            break

    out.release()
    capture.release()
    cv2.destroyAllWindows()
