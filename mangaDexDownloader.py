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
MAXARGS = 2

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
            print('error was encountered loading the page; refreshing')
            torDriver.refresh()

    elif type == REFRESH:
        print('error was encountered loading the page; this is the last try.')
        print('refreshing the page is in progress')
        torDriver.refresh()
    else:
        print('passed error type is unknown')

def downloadFinished():
    titleComponents = regex.search(torDriver.title)
    if titleComponents:
        return False
    else:
        return True

torDriver = tbdriver.TorBrowserDriver(Path.home() / 'tor-browser')
torDriver.maximize_window()

if len(sys.argv) == MAXARGS:
    _, requestedURL = sys.argv
elif len(sys.argv) > MAXARGS:
    print('too many arguments!')
    exit()
else:
    print('too few arguments!')
    exit()

currentURL = getTrueURL(requestedURL)
newURL = currentURL

width, height = pyautogui.size()
regex = re.compile(r'''                     # 1st group: The whole match
                   ((\d+)                   # 2nd group: Chapter page number
                   [ ]\|[ ]                 # Seperator
                   (Chapter|[\w ]*)         # 3rd group: Chapter or other replacements
                   ([ ](\d+)(\.\d+)?)?      # 4th, 5th, 6th group: Chapter's number, decimal part, fraction part
                   [ ]-[ ]                  # Seperator
                   (.*)                     # 7th group: Title of the manga
                   ([ ]-[ ]MangaDex))       # 8th group: MangaDex 
                   ''',
                   re.VERBOSE)

torDriver.get(requestedURL)

while True:
    retries = 0
    try:
        tbdriver.WebDriverWait(torDriver, TIMEOUT).until(EC.visibility_of_any_elements_located((By.XPATH, IMAGEXPATH)))
    except TimeoutException:
        if downloadFinished():
            print('downloading manga finished! exiting')
            break
        if retries < MAXRETRIES:
            errorHandling(RETRY)
        elif retries == MAXRETRIES:
            errorHandling(REFRESH)
        elif retries == MAXRETRIES + 1:
            print('error was encountered loading the page, and couldn\'t be fixed. exiting')
            break
        retries += 1
    else:
        pageTitle = torDriver.title
        titleComponents = regex.search(pageTitle)
        if titleComponents:
            titleComponents = list(titleComponents.groups())
            pageNumber, chapterTitle, chapterNumber, fraction, mangaName = int(titleComponents[1]), titleComponents[2]\
                , int(titleComponents[4]), titleComponents[5], titleComponents[6]
        else:
            print('downloading manga finished! exiting')
            break;
        # Chapter's number is a floating point number
        if fraction:                                                 # Adding preceding zeroes can be variable
            directoryPath = Path.home() / 'Downloads' / mangaName / '{} {:02d}{}'.format(
                chapterTitle, chapterNumber, fraction
                )
        else:
            directoryPath = Path.home() / 'Downloads' / mangaName / '{} {:02d}'.format(chapterTitle, chapterNumber)
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
