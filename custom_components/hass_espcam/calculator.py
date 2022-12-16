import cv2
import numpy as np
import pytesseract
from PIL import Image
from io import BytesIO

from custom_components.hass_espcam.const import LOGGER


class ElectricityCalculator:

    @staticmethod
    def crop_for_detection(image, roi):
        # rotate image 180 degrees
        image = image.rotate(180)
        roi = [int(x) for x in roi.values()]
        roi[2] += roi[0]
        roi[3] += roi[1]
        return image.crop(roi)

    @staticmethod
    def recognize_digits(image, decimals):
        image.save('/home/homeassistant/test-image-cropped.png')

        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        invert = 255 - thresh

        # Perfrom OCR with Pytesseract
        data = pytesseract.image_to_string(
            invert,
            lang='eng',
            config='--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        )

        data = str(int(data))
        decimalized = data[:-decimals] + '.' + data[-decimals:]
        return float(decimalized)

    async def update_value_recognized(self, session, snapshot_url, roi, decimals, debug):
        # Open async session
        LOGGER.info('Start fetching image from esp32cam...')
        if debug:
            image = Image.open('/home/homeassistant/test-image.png')
        else:
            async with session.get(snapshot_url) as response:
                response.raise_for_status()
                image = Image.open(BytesIO(await response.read()))
                LOGGER.info('Finished fetching image from esp32cam!')

        image = self.crop_for_detection(image, roi)
        return self.recognize_digits(image, decimals)
