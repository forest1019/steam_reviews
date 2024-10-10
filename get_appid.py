import time
import pandas as pd
from parsel import Selector
from selenium.webdriver import Chrome, ChromeOptions



options = ChromeOptions()
options.add_experimental_option('prefs', {'intl.accept_languages': 'en_US'})
driver = Chrome(options=options)

url='https://store.steampowered.com/search/?sort_by=Released_DESC&ndl=1'
driver.get(url)

def get_appid(max_scroll):
    games = list()
    game_data = list()
    for i in range(max_scroll):
        time.sleep(1)
        r = driver.page_source
        s = Selector(r)
        current_games = s.xpath('//a[contains(@class, "search_result_row")]')
        current_count = len(current_games)
        games.extend(current_games)
        time.sleep(1)
        r = driver.page_source
        s = Selector(r)
        new_games = s.xpath('//a[contains(@class, "search_result_row")]')
        new_count= len(new_games)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        if new_count <= current_count:
            break

    for game in games:
        #appid
        appid = game.xpath('//a/@data-ds-appid').get()
        # 获取游戏名称
        game_title = game.xpath('//span[@class="title"]/text()').get()

        # 获取平台信息
        platforms = game.xpath('//span[contains(@class, "platform_img")]/@class').getall()
        platforms = [platform.split()[-1] for platform in platforms]  # 提取平台标识

        # 获取发布时间
        release_date = game.xpath('//div[contains(@class, "search_released")]/text()').get().strip()

        # 获取价格
        price = game.xpath('//div[contains(@class, "discount_final_price")]/text()').get()
        
        result = [appid, game_title, platforms, release_date, price]
        games.append(result)
    return games

def save_to_csv(data, filename):
    columns = ["Appid", "Game_title", "Platform", "Release_date", "Price"]
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(filename, index=False, encoding='utf-8') 

game=get_appid(10)
save_to_csv(game,'game_info.csv')
