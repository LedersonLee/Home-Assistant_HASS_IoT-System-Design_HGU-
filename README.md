# Home Assistant ESPCAM Component

## Description

This is a Home Assistant custom component for ESP32CAM camera. 
This compoenent assumes that ESP32CAM is running a webserver with a GET interface that serves 
image data. The component will poll the ESP32CAM for image data, performs OCR on the image and
displays the result in the Home Assistant UI.


## Installation

### HACS (Recommended)
1. Add this repository as a custom repository in HACS.
2. Install the component from HACS.

### Manual Installation
1. Clone this repository.
2. Copy the `hass_espcam` folder to your `custom_components` folder. 

## Configuration 

Add the following to your `configuration.yaml` file:

```yaml
camera:
  - platform: espcam
    snapshot_url: <URL_TO_ESPCAM_WEB>
    roi_x: <COORDINATES_OF_ROI>
    roi_y:
    roi_width:
    roi_height:
    debug: <True/False>
    decimals: <DECIMALS_FROM_RIGHT>
```

3. Restart Home Assistant.
4. Add the ESPCAM Entity to your Lovelace UI.

## Remarks

- User must provide the URL to the ESP32CAM webserver. The webserver must be running on the ESP32CAM and
  must serve image data on a GET request.
- User must provide coordinates for the Region of Interest (ROI) on the image. The ROI is the area of the
  image that will be used for OCR. The coordinates are relative to the image size. For example, if the
  image is 640x480, then the ROI coordinates are 0-640 for x and 0-480 for y.
- User can enable debug mode. This will save the image that is used for OCR in .homeassistant folder
- User can set decimals to determine how many decimals to the right of the decimal point to display. For
  example, if the OCR result is 123456, then setting decimals to 2 will display 1234.56
- User can set the polling interval. The default is 5 seconds.


## Authors
- Juho Hong
- Jeongeon Lee