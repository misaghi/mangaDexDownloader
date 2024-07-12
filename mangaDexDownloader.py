from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from pathlib import Path
import pyautogui
import time
import pyperclip
import sys
import re

IMAGEXPATH = "/html/body/div[1]/div[1]/div[2]/div[3]/div/div[1]/div[2]/div[1]/div/img"
ERRORXPATH = '/html/body/div[1]/div[1]/div[2]/div[3]/div/div[1]/div[2]/div[1]/div/div'
GAPCONTBUTPATH = '/html/body/div[1]/div[1]/div[2]/div[3]/div/div[3]/div[1]/div[2]/div/div[3]/button[2]'
ADDTOLIB = '/html/body/div[1]/div[1]/div[2]/div[3]/div/div[5]/div/button[1]/span'
RETRY = 'retry'
REFRESH = 'refresh'
GAP = 'gap'
TIMEOUT = 60
MAXARGS = 3


def getTrueURL(url):
    return url[:url.find('/', len(requestedURL) - 4)]


def errorHandling(type):
    """
    This method handles various kinds of errors which might happen during script's execution.
    Handled errors:
    1. RETRY: Clicking on the retry button.
    2. REFRESH: Refreshing the whole web page.
    3. GAP: Skipping to next chapter in case of encountering a gap.
    """
    if type == RETRY:
        try:
            errorElement = WebDriverWait(driver, TIMEOUT).until(
                EC.visibility_of_element_located((By.XPATH, ERRORXPATH)))
        except TimeoutException:
            error = False
        else:
            if errorElement.text.lower() == 'click to retry':
                error = True
            else:
                error = False

        if error:
            print('error was encountered loading the page; retrying')
            time.sleep(0.125)
            errorElement.click()
        else:
            # NOTE: Refreshing the page was not a good idea. The page has more time for loading in this approach
            pass

    elif type == REFRESH:
        print('error was encountered loading the page; refreshing')
        driver.refresh()
    elif type == GAP:
        print('gap was found; skipping to next chapter')
        gapElement = driver.find_element(By.XPATH, GAPCONTBUTPATH)
        time.sleep(0.125)
        gapElement.click()
    else:
        print('passed error type is unknown')


def downloadFinished():
    """
    Checks if download is finished or not by checking 'Add to Library' button at manga's main page
    """
    try:
        driver.find_element(By.XPATH, ADDTOLIB)
    except NoSuchElementException:
        return False
    else:
        print('downloading manga finished! exiting')
        return True


def stuckInLoading():
    """
    Sometimes web pages aren't load correctly. This method checks for mentioned cases
    """
    pageTitle = driver.title
    if regex.search(pageTitle):
        return False
    else:
        return True


def gapExists():
    """
    Checks for gap between chapters
    """
    try:
        driver.find_element(By.XPATH, GAPCONTBUTPATH)
    except NoSuchElementException:
        return False
    else:
        return True


if len(sys.argv) == MAXARGS:
    _, browser, requestedURL = sys.argv
elif len(sys.argv) > MAXARGS:
    print('too many arguments!')
    exit()
else:
    print('not enough arguments!')
    exit()

if browser.lower() == 'tor':
    from tbselenium import tbdriver
    driver = tbdriver.TorBrowserDriver(Path.home() / 'tor-browser')
elif browser.lower() == 'firefox':
    from selenium.webdriver import Firefox
    driver = Firefox()
else:
    print('browser must be either tor or firefox. exiting...')
    exit()

driver.maximize_window()

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


while True:  # Retry on connection has timed out error
    try:
        driver.get(requestedURL)
    except WebDriverException:
        print('connection has timed out; reloading')
        continue
    else:
        break

while True:
    if gapExists():
        errorHandling(GAP)
        continue
    elif downloadFinished():
        break
    try:
        WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_any_elements_located((By.XPATH, IMAGEXPATH))
        )
    except TimeoutException:
        if stuckInLoading():
            errorHandling(REFRESH)
        else:
            errorHandling(RETRY)
    except WebDriverException:
        errorHandling(REFRESH)
    else:
        pageTitle = driver.title
        titleComponents = regex.search(pageTitle)
        if titleComponents:
            titleComponents = list(titleComponents.groups())
            pageNumber, chapterTitle, fraction, mangaName = int(
                titleComponents[1]), titleComponents[2], titleComponents[5], titleComponents[6]
            try:
                chapterNumber = int(titleComponents[4])
            except TypeError:
                print("chapter doesn't have any numbers")
                chapterNumber = ''

        if chapterNumber:
            # Chapter's number is a floating point number
            if fraction:                                                 # Adding preceding zeroes can be variable
                directoryPath = Path.home() / 'Downloads' / mangaName / '{} {:02d}{}'.format(
                    chapterTitle, chapterNumber, fraction
                )
            else:
                directoryPath = Path.home() / 'Downloads' / mangaName / \
                    '{} {:02d}'.format(chapterTitle, chapterNumber)
        else:
            directoryPath = Path.home() / 'Downloads' / mangaName / '{}'.format(chapterTitle)

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
        pyautogui.press('enter')  # Save image
        time.sleep(0.125)
        pyperclip.copy(pathToSaveImage.__str__())
        pyautogui.moveTo(228, 52)  # Address bar
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
        pyautogui.press('enter')  # Paste path to save image
        time.sleep(0.125)
        pyautogui.moveTo(1792, 1056)
        time.sleep(0.125)
        pyautogui.click()
        time.sleep(0.125)

        pyautogui.moveTo((width / 4) * 3, height / 2)
        time.sleep(0.125)
        pyautogui.click()
        newURL = getTrueURL(driver.current_url)
        pyperclip.copy(newURL)
