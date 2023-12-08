from tbselenium import tbdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from pathlib import Path
import pyautogui
import time
import pyperclip
import sys
import re

IMAGEXPATH = "/html/body/div[1]/div[1]/div[2]/div[2]/div/div[1]/div[2]/div[1]/div/img"
ERRORXPATH = '/html/body/div[1]/div[1]/div[2]/div[2]/div/div[1]/div[2]/div[1]/div/div'
MAXRETRIES = 3
RETRY = 'retry'
REFRESH = 'refresh'
TIMEOUT = 60

def getTrueURL(url):
    return url[:url.find('/', len(requestedURL) - 4)]

def errorHandling(type):
    if type == RETRY:
        try:
            torDriver.find_element(By.XPATH, ERRORXPATH)
        except Exception:
            error = False
        else:
            error = True

        if error:
            print('error was encountered loading the page; retrying')
            pyautogui.moveTo(width / 2, height / 2)
            time.sleep(0.125)
            pyautogui.click()
        else: # For some reason retry button wasn't appeared or maybe the page's loading was too long
            torDriver.refresh()

    elif type == REFRESH:
        print('error was encountered loading the page; this is the last try.')
        print('refreshing the page is in progress')
        torDriver.refresh()
    else:
        print('passed error type is unknown')

torDriver = tbdriver.TorBrowserDriver(Path.home() / 'tor-browser')
torDriver.maximize_window()

if len(sys.argv) == 2:
    _, requestedURL = sys.argv
elif len(sys.argv) > 2:
    print('too many arguments!')
    exit()
else:
    print('too few arguments!')
    exit()

currentURL = getTrueURL(requestedURL)
newURL = currentURL

width, height = pyautogui.size()
regex = re.compile(r'((\d+) \| Chapter (\d+) - (.*)( - MangaDex))')

torDriver.get(requestedURL)

while True:
    retries = 0
    try:
        tbdriver.WebDriverWait(torDriver, TIMEOUT).until(EC.visibility_of_any_elements_located((By.XPATH, IMAGEXPATH)))
    except TimeoutException:
        if retries < MAXRETRIES:
            errorHandling(RETRY)
        elif retries == MAXRETRIES:
            errorHandling(REFRESH)
        elif retries == MAXRETRIES + 1:
            print('error was encountered loading the page, and couldn\'t be fixed. exiting')
            break;
        retries += 1
    else:
        pageTitle = torDriver.title
        titleComponents = list(regex.search(pageTitle).groups())
        if titleComponents[0]:
            pageNumber, chapterNumber, mangaName = int(titleComponents[1]), int(titleComponents[2]), titleComponents[3]
        else:
            print('downloading manga finished! exiting')
            break;                                              # Adding preceding zeroes can be variable
        directoryPath = Path.home() / 'Downloads' / mangaName / 'Chapter {:02d}'.format(chapterNumber)
        Path.mkdir(directoryPath, exist_ok=True, parents=True)

        pathToSaveImage = directoryPath / '{:02d}'.format(pageNumber)
        pyautogui.moveTo(width / 2, height / 2)
        time.sleep(0.125)
        pyautogui.rightClick()
        time.sleep(0.125)
        pyautogui.press('down')
        time.sleep(0.125)
        pyautogui.press('down')
        time.sleep(0.125)
        pyautogui.press('enter') # Save image
        time.sleep(0.125)
        pyperclip.copy(pathToSaveImage.__str__())
        pyautogui.moveTo(228, 52) # Address bar
        time.sleep(0.125)
        pyautogui.doubleClick()
        time.sleep(0.125)
        pyautogui.rightClick()
        time.sleep(0.125)
        pyautogui.press('down')
        time.sleep(0.125)
        pyautogui.press('down')
        time.sleep(0.125)
        pyautogui.press('down')
        time.sleep(0.125)
        pyautogui.press('enter') # Paste path to save image
        time.sleep(0.125)
        pyautogui.moveTo(1792, 1056)
        time.sleep(0.125)
        pyautogui.click()
        time.sleep(0.125)

        pyautogui.moveTo((width / 4) * 3, height / 2)
        time.sleep(0.125)
        pyautogui.click()
        newURL = getTrueURL(torDriver.current_url)
        pyperclip.copy(newURL)
