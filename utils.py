import easyocr
import cv2
from config import plates_list

    
reader = easyocr.Reader(['en'], gpu=True)

def perform_ocr_on_image(img, coordinates):

    x, y, w, h = map(int, coordinates)
    cropped_img = img[y:y+h, x:x+w]

    gray_img = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    results = reader.readtext(gray_img)

    text = ""
    for res in results:
        if len(results) == 1 or (len(res[1]) > 6 and res[2] > 0.2):
            text = res[1]

    return str(text).upper()

def is_authorized_plate(plate_text):
    if plate_text in plates_list:
        return True
    else:
        return False
