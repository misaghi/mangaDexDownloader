from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException, WebDriverException
from selenium.webdriver.common.by import By
from pathlib import Path
import pyautogui
import time
import pyperclip
import sys
import re

IMAGESXPATH = "/html/body/div[1]/div[1]/div[2]/div[3]/div/div[1]/div[2]/div[1]/div/div/img"
ERRORXPATH = '/html/body/div[1]/div[1]/div[2]/div[3]/div/div[1]/div[2]/div[1]/div/div'
GAPCONTBUTPATH = '/html/body/div[1]/div[1]/div[2]/div[3]/div/div[3]/div[1]/div[2]/div/div[3]/button[2]'
NEXTCHAP = '/html/body/div[1]/div[1]/div[2]/div[3]/div/div[1]/div[4]/a'
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
    1. RETRY: Clicking on the retry button(s).
    2. REFRESH: Refreshing the whole web page.
    3. GAP: Skipping to next chapter in case of encountering a gap.
    """
    if type == RETRY:
        for possibleError in possibleErrors:
            try:
                if possibleError.text.lower() == 'click to retry':
                    print('error was encountered loading the page; retrying')
                    possibleError.location_once_scrolled_into_view
                    time.sleep(0.125)
                    possibleError.click()
            except StaleElementReferenceException:
                pass

    elif type == REFRESH:
        print('error was encountered loading the page; refreshing')
        driver.refresh()
    elif type == GAP:
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
    _, platform, requestedURL = sys.argv
    platform = platform.lower()
elif len(sys.argv) > MAXARGS:
    print('too many arguments!')
    exit()
else:
    print('not enough arguments!')
    exit()

if platform == 'linux':
    from tbselenium import tbdriver
    driver = tbdriver.TorBrowserDriver(Path.home() / 'tor-browser')
elif platform == 'windows':
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

loadingTitleRegex = re.compile(r'''
                                Loading\.\.\.
                               [ ]-[ ]
                               MangaDex
                                ''',
                               re.VERBOSE)

while True:
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
        pages = tbdriver.WebDriverWait(driver, TIMEOUT).until(
            EC.visibility_of_all_elements_located((By.XPATH, IMAGESXPATH))
        )

        possibleErrors = tbdriver.WebDriverWait(driver, 1).until(  # No need for more waiting here
            EC.visibility_of_all_elements_located((By.XPATH, ERRORXPATH))
        )
    except TimeoutException:
        if stuckInLoading():
            errorHandling(REFRESH)
        else:
            errorHandling(RETRY)
    else:
        if len(pages) < len(possibleErrors):
            time.sleep(TIMEOUT)  # Some extra delay here to load completely
            errorHandling(RETRY)
            continue  # Errors were incountered, and we are going to start over

        pageTitle = driver.title
        titleComponents = regex.search(pageTitle)
        if titleComponents:
            titleComponents = list(titleComponents.groups())
            pageNumber, chapterTitle, chapterNumber, fraction, mangaName = int(
                titleComponents[1]), titleComponents[2], int(titleComponents[4]), titleComponents[5], titleComponents[6]

        # Chapter's number is a floating point number
        if fraction:                                                 # Adding preceding zeroes can be variable
            directoryPath = Path.home() / 'Downloads' / mangaName / '{} {:02d}{}'.format(
                chapterTitle, chapterNumber, fraction
            )
        else:
            directoryPath = Path.home() / 'Downloads' / mangaName / \
                '{} {:02d}'.format(chapterTitle, chapterNumber)
        Path.mkdir(directoryPath, exist_ok=True, parents=True)

        for page in pages:
            pathToSaveImage = directoryPath / '{:02d}'.format(pageNumber)

            page.location_once_scrolled_into_view

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
            if platform == 'linux':
                pyautogui.moveTo(228, 52)  # Address bar
            else:
                pyautogui.moveTo(574, 620)  # Address bar
            time.sleep(0.125)
            pyautogui.doubleClick()
            time.sleep(0.125)
            pyautogui.rightClick()
            time.sleep(0.125)
            if platform == 'windows':
                pyautogui.press('down')
                time.sleep(0.125)
            pyautogui.press('down')
            time.sleep(0.125)
            pyautogui.press('down')
            time.sleep(0.125)
            pyautogui.press('down')
            time.sleep(0.125)
            pyautogui.press('enter')  # Paste path to save image
            time.sleep(0.125)
            if platform == 'linux':
                pyautogui.moveTo(1792, 1056)  # Clicking save button
            else:
                pyautogui.moveTo(1094, 707)
            time.sleep(0.125)
            pyautogui.click()
            time.sleep(0.125)

            pageNumber += 1

        nextChapterButton = driver.find_element(By.XPATH, NEXTCHAP)
        nextChapterButton.location_once_scrolled_into_view
        nextChapterButton.click()

        newURL = getTrueURL(driver.current_url)
        pyperclip.copy(newURL)
