import re

import cv2
import numpy as np
import pytesseract

if __name__ == '__main__':
    image = cv2.imread('test.png')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, 1, 1, 11, 2)

    erode = cv2.erode(thresh, np.array((7, 7)), iterations=1)
    text = pytesseract.image_to_string(erode, config="--psm 6")
    text = re.sub('[^A-Za-z0-9]+', '\n', text)

    print(text)