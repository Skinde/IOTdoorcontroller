from ultralytics import YOLO
import cv2
import math
import pytesseract
import logging
import torch
from utils import perform_ocr_on_image, is_authorized_plate
from config import classNames, PROCESS_EVERY_NTH_FRAME 

#print(torch.version)
#print(torch.cuda.is_available())
#print(torch.cuda.device_count())
#print(torch.cuda.get_device_name(0))
#torch.cuda.set_device('cuda:0')

# Create and configure logger
logging.basicConfig(filename="detections.log",
                    format='%(asctime)s %(message)s',
                    datefmt='%H:%M:%S',
                    filemode='w')

# Creating an object
logger = logging.getLogger()
logger.setLevel(logging.INFO)


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    equal = cv2.equalizeHist(blur)
    return equal

def detect_plate(image):
    preprocessed = preprocess_image(image)
    edges = cv2.Canny(preprocessed, 30, 200)
    contours, _ = cv2.findContours(edges.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
    
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.018 * perimeter, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            plate = image[y:y+h, x:x+w]
            return plate
    return None

def ocr_plate(plate_image):
    gray = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    text = pytesseract.image_to_string(thresh, config=config)
    logger.info(f"OCR Text ---> {text}")
    return ''.join(filter(str.isalnum, text))



def plate_validation():
    cap = cv2.VideoCapture(1)
    cap.set(3, 1280)
    cap.set(4, 720)

    model = YOLO('yolo11n.pt')


    frame_count = 0
    plate_count = 0
    plate = ""

    while True:
        success, img = cap.read()
        if not success:
            break

        frame_count += 1
        if frame_count % PROCESS_EVERY_NTH_FRAME != 0:
            continue

        results = model(img, stream=True)
        
        for r in results:
            boxes = r.boxes

            for box in boxes:
                cls = int(box.cls[0])
                confidence = math.ceil((box.conf[0]*100))/100
                if (classNames[cls] == "car" or classNames[cls] == "person" or classNames[cls] == "truck") and confidence > 0.5:
                    #logger.info(f"Class name --> {classNames[cls]}")

                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2) # convert to int values

                    #cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 255), 3)

                    logger.info(f"Confidence --->{confidence}")

                    # object details
                    org = [x1, y1]
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    fontScale = 1
                    color = (255, 0, 0)
                    thickness = 2

                    #cv2.putText(img, classNames[cls], org, font, fontScale, color, thickness)

                    # OCR
                    coordinates = (x1, y1, x2-x1, y2-y1)
                    curr_plate = perform_ocr_on_image(img, coordinates)
                    logger.info(f"Plate detected ---> {curr_plate}")
                    print(f"Plate detected ---> {curr_plate}")
                    if is_authorized_plate(curr_plate):
                            logger.info(f"Plate detected authorized ---> {curr_plate}")
                            print(f"Plate detected authorized ---> {curr_plate}")
                            plate_count = 0
                            return True

                    # if curr_plate != plate:
                    #     plate = curr_plate
                    #     plate_count += 1
                    # else:
                    #     print(plate_count)
                    #     if plate_count > 0 and is_authorized_plate(plate):
                    #         logger.info(f"Plate detected authorized ---> {plate}")
                    #         plate_count = 0
                    #         return True

                    print(f"Plate detected ---> {plate}")
                    #logger.info(f"OCR Text ---> {text}")

                    """
                    plate = detect_plate(img)
                    if plate is not None and plate.size > 0:
                        cv2.imshow('Plate', plate)
                    else:
                        print("La imagen 'plate' está vacía o no se generó correctamente.")

                    if plate is not None:
                        plate_text = ocr_plate(plate)
                        logger.info(f"Plate detected ---> {plate_text}")
                    if plate_text and len(plate_text) > 0:
                        logger.info(f"Plate detected sucessfully ---> {plate_text}")
                    """
                else: 
                    logger.info("No car detection")
                    continue
        
        #cv2.imshow('Webcam', img)
        #if cv2.waitKey(1) == ord('q'):
            #break

    #cap.release()
    #cv2.destroyAllWindows()

if __name__ == "__main__":
    plate_validation()