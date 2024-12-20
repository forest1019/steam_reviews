import time
import pandas as pd
from parsel import Selector
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By



options = ChromeOptions()
options.add_experimental_option('excludeSwitches',['enable-automation'])   
options.add_experimental_option('useAutomationExtension', False)    
#隐藏特征内容     
options.add_argument("--disable-blink-features=AutomationControlled") 
options.add_experimental_option('prefs', {'intl.accept_languages': 'en_US'})
driver = Chrome(options=options)

#url='https://store.steampowered.com/search/?sort_by=Released_DESC&ndl=1&page=1'
#driver.get(url)

def get_appid(min_page,max_page):
    games = list()
    game_data = list()
    url=f'https://store.steampowered.com/search/?sort_by=Released_DESC&ndl=1&page={min_page}'
    driver.get(url)
    for i in range(min_page,max_page+1):
        try:
            r = driver.page_source
            s = Selector(text=r) 
            games = s.xpath('//a[contains(@class, "search_result_row")]')
            for game in games:
            #appid
                appid = game.xpath('.//@data-ds-appid').get()
            # 获取游戏名称
                game_title = game.xpath('.//span[@class="title"]/text()').get()
            # 获取平台信息
                platforms = game.xpath('.//span[contains(@class, "platform_img")]/@class').getall()
                platforms = [platform.split()[-1] for platform in platforms]  # 提取平台标识
            # 获取发布时间
                release_date = game.xpath('.//div[contains(@class, "search_released")]/text()').get().strip()
            # 获取价格
                price = game.xpath('.//div[contains(@class, "discount_final_price")]/text()').get()
            # 获取原价
                original_price = game.xpath('.//div[contains(@class, "discount_original_price")]/text()').get()
            
                result = [appid, game_title, platforms, release_date, price,original_price]
                game_data.append(result)

            button=driver.find_element(By.XPATH, '//a[@class="pagebtn" and contains(text(), ">")]')
            button.click()
            time.sleep(3)
        except Exception as e:
            print(f"Error occurred: {e}")
            print(i)
            break
 
    driver.quit()
    
    return game_data
    '''
    while True:
        r = driver.page_source
        s = Selector(text=r) #第一次加载
        current_games = s.xpath('//a[contains(@class, "search_result_row")]')
        current_count = len(current_games)
        games = current_games  #增加到列表里
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")#滚动
        time.sleep(10) 
        r = driver.page_source
        s = Selector(text=r)#新一次加载
        new_games = s.xpath('//a[contains(@class, "search_result_row")]')
        new_count = len(new_games)
        if new_count <= current_count:
            break
'''
'''
    for i in range(max_scroll):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(5)
        r = driver.page_source
        s = Selector(r)
        if len(s.xpath('//a[contains(@class, "search_result_row")]')) > len(games):
            games = s.xpath('//a[contains(@class, "search_result_row")]')
        else:
            break
'''

def save_to_csv(data, filename):
    columns = ["Appid", "Game_title", "Platform", "Release_date", "Price","original_price"]
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(filename, index=False, encoding='utf-8') 

game=get_appid(1503,1511)  #改成需要的页码
save_to_csv(game,'game_info.csv') #改成输出文件
