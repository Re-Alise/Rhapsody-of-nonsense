import cv2
import numpy as np


LINE_THRESHOLD = (31, 31, 4)
BLUR_PIXEL = (5, 5)

COLOR_SEARCH_LIMIT = 100000
HUE_RED = [0, 3]  # 0
HUE_GREEN = [10, 11]  # 11.66
HUE_BLUE = [20, 21]  # 21.33


def threshold_by_colors(im, colors: list, debug=False):
    '''
    Arguments:
    im -- image to process
    colors -- colors ('r', 'g', 'b', 'k') use to do thresholding
    '''
    blurred = cv2.GaussianBlur(im, BLUR_PIXEL, 0)
    im_hsv = cv2.cvtColor(blurred, cv2.COLOR_RGB2HSV)
    # convert to 5 bit color, which has 32 levels (0-31) each value
    im_hsv //= 8

    pixels_red = []
    pixels_green = []
    pixels_blue = []
    pixels_black = []

    count_red = 0
    count_green = 0
    count_blue = 0
    count_black = 0

    u, count = np.unique(
        im_hsv.reshape(-1, im_hsv.shape[2]), return_counts=True, axis=0)
    # if debug:
    #     print(u)
    for i in range(len(u)):
        pixel = u[i]
        # if len(pixels_red) + len(pixels_green) + len(pixels_blue) + len(pixels_black) >= len(colors) * COLOR_SEARCH_LIMIT:
        #     break

        if 'k' in colors and pixel[2] < LINE_THRESHOLD[2]:
            if count_black >= COLOR_SEARCH_LIMIT:
                continue
            pixels_black.append(pixel)
            count_black += count[i]
        else:
            if pixel[1] < 8:
                continue
            if 'g' in colors and pixel[0] in HUE_GREEN and pixel[2] > 8:
                if count_green >= COLOR_SEARCH_LIMIT:
                    continue
                pixels_green.append(pixel)
                count_green += count[i]
            elif 'b' in colors and pixel[0] in HUE_BLUE and pixel[2] > 4:
                if count_blue >= COLOR_SEARCH_LIMIT:
                    continue
                pixels_blue.append(pixel)
                count_blue += count[i]
            elif 'r' in colors and pixel[0] in HUE_RED and pixel[2] > 8:
                if count_red >= COLOR_SEARCH_LIMIT:
                    continue
                pixels_red.append(pixel)
                count_red += count[i]

    result = np.zeros(blurred.shape[:2], dtype=int)
    if debug:
        result_debug = []

    # print(im_hsv)

    if 'r' in colors:
        if len(pixels_red) == 0:
            print('Red not found')
            r_ranged = np.zeros(im_hsv.shape[:2], dtype=int)
        else:
            # print(pixels_red)
            r_ranged = cv2.inRange(im_hsv, np.min(
                pixels_red, axis=0), np.max(pixels_red, axis=0))
        if debug:
            result_debug.append(r_ranged)
        result = np.logical_or(result, r_ranged)
    if 'g' in colors:
        if len(pixels_green) == 0:
            print('Green not found')
            g_ranged = np.zeros(im_hsv.shape[:2], dtype=int)
        else:
            # print(pixels_green)
            g_ranged = cv2.inRange(im_hsv, np.min(
                pixels_green, axis=0), np.max(pixels_green, axis=0))
        if debug:
            result_debug.append(g_ranged)
        result = np.logical_or(result, g_ranged)
    if 'b' in colors:
        if len(pixels_blue) == 0:
            print('Blue not found')
            b_ranged = np.zeros(im_hsv.shape[:2], dtype=int)
        else:
            # print(pixels_green)
            b_ranged = cv2.inRange(im_hsv, np.min(
                pixels_blue, axis=0), np.max(pixels_blue, axis=0))
        if debug:
            result_debug.append(b_ranged)
        result = np.logical_or(result, b_ranged)
    if 'k' in colors:
        # print(pixels_black)
        low = np.asarray((0, 0, 0), dtype=np.uint8)
        k_ranged = cv2.inRange(
            im_hsv, low, np.max(pixels_black, axis=0))
        if debug:
            result_debug.append(k_ranged)
        result = np.logical_or(result, b_ranged)
    
    result = result.astype(np.uint8)
    result *= 255

    if debug:
        result_debug.append(result)
        return result_debug
    return result


if __name__ == "__main__":
    # np.set_printoptions(threshold=np.inf)
    original = cv2.imread('scale-owo.png')
    result = threshold_by_colors(original, colors=['r', 'g', 'b', 'k'], debug=True)
    # print(result)
    # for im in result:
    #     print(im.shape)
    image = np.hstack(result)
    cv2.imwrite('thresholding.png', image)
    # cv2.imshow('Thresholding test', image)
    # input('owwo')
    # cv2.destroyAllWindows()
