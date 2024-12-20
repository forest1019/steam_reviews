import time
import pandas as pd
import re
from parsel import Selector
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

#from datetime import datetime


options = ChromeOptions()
options.add_experimental_option('prefs', {'intl.accept_languages': 'en_US'})




#获取评论内容
def get_data(reviews,language):

    #提取评论数据并保存至list
    results=list()

    for review in reviews:
       attitude = review.xpath(".//div[contains(@class, 'title')]/text()").get()
       attitude_value = 0 if attitude and "Not Recommended" in attitude else 1 #是否推荐,推荐为1不推荐为0
       play_record = review.xpath(".//div[contains(@class, 'hours')]/text()").get()#游戏记录
       #发布时间，发布文本，标签
       date_content = review.xpath(".//div[contains(@class, 'apphub_CardTextContent')]")
       publish_date = date_content.xpath(".//div[contains(text(), 'Posted:')]/text()").get(default="").replace("Posted: ", "").strip()#评论时间
       content = date_content.xpath("text()[normalize-space()]").getall()  #评论文本
       free_get = 1 if date_content.xpath("./div[@class='received_compensation']/text()").get() else 0 #免费获得标签，有为1否则0
       refunded = 1 if date_content.xpath("./div[@class='refunded']/text()").get() else 0    #退款标签 有为1否则0
       #他人评价：包括标签、奖励板块
       judgement = review.xpath(".//div[contains(@class, 'found_helpful')]")
       #helpful和funny数量
       helpful_count = 0
       funny_count = 0
       helpful_funny = judgement.xpath("./text()").extract()
       for part in helpful_funny:
           part = part.strip()
           if "found this review helpful" in part:
               helpful_count = int(re.search(r'(\d+)', part).group(1))   
           elif "found this review funny" in part:
               funny_count = int(re.search(r'(\d+)', part).group(1))
       #奖励数量       
       award_count = judgement.xpath("./div[@class='review_award_aggregated tooltip']/text()").get()

       #发布者模块
       poster = review.xpath("./div[@class='apphub_CardContentAuthorBlock tall']")
       poster_link = poster.xpath(".//a/@href").get() #用户链接
       nickname = poster.xpath("..//div[contains(@class, 'apphub_CardContentAuthorName')]/a/text()").get()  # 发布者昵称
       product_count = re.search(r'(\d+) products in account', poster.xpath(".//div[contains(@class, 'apphub_CardContentMoreLink')]/text()").get() or '')  
       product_count = product_count.group(1) if product_count else ''   # 账户内产品数
       reply_count = review.xpath(".//div[contains(@class, 'apphub_CardCommentCount')]/text()").get()  # 回复数量

       result=[attitude_value, play_record, publish_date, free_get, refunded, content, helpful_count, funny_count, award_count, poster_link, nickname, product_count, reply_count,language]
       results.append(result)
        
    return results




#获取不同语言的评论内容
def get_full_data(app_id,filter):
    full_data = list()
    url = f"https://steamcommunity.com/app/{app_id}/reviews/?browsefilter={filter}"  
    #appid游戏id filter{mostrecent,toprated, recentlyupdated, funny}
    driver = Chrome(options=options)
    driver.get(url)
    try:
    #点击下拉框
        dropdown_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'filterlanguage')))
        dropdown_button.click()
        options = WebDriverWait(driver, 10).until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, '#filterlanguage_options .option')))
        
        #循环获取每种语言下的页面
        for i in range(1, len(options)):   #不包括第一个all
            dropdown_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'filterlanguage')))
            dropdown_button.click()
            options = WebDriverWait(driver, 10).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, '#filterlanguage_options .option')) )
            option=options[i] #当前语言选项
            language = option.text.strip()
            option.click()
            time.sleep(2)

            #生成Html列表
            reviews=list()
            while True:
                r = driver.page_source
                s = Selector(text=r) #第一次加载
                current_reviews = s.xpath("//div[@class='apphub_Card modalContentLink interactable']")
                current_count = len(current_reviews)
                reviews = current_reviews  #增加到列表里
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")#滚动
                time.sleep(2) 
                r = driver.page_source
                s = Selector(text=r)#新一次加载
                new_reviews = s.xpath("//div[@class='apphub_Card modalContentLink interactable']")
                new_count = len(new_reviews)
                if new_count <= current_count:
                    break
            
            #调用函数获取数据
            data = get_data(reviews,language)
            full_data.extend(data)
            driver.execute_script("window.scrollTo(0, 0)")

    finally:
        driver.quit()
    return full_data


#获取单一语言的评论内容
def get_language_data(app_id, filter, language):
    full_data = []
    wrong = []
    url = f"https://steamcommunity.com/app/{app_id}/reviews/?filterLanguage={language}&snr=1_5_100010_&browsefilter={filter}&p=1"
    try:
        driver = Chrome(options=options)
       # print(url)
        driver.get(url)
        reviews = []
        while True:
            r = driver.page_source
            s = Selector(text=r)
            current_reviews = s.xpath("//div[@class='apphub_Card modalContentLink interactable']")
            reviews = current_reviews
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            r = driver.page_source
            s = Selector(text=r)
            new_reviews = s.xpath("//div[@class='apphub_Card modalContentLink interactable']")
            if len(new_reviews) <= len(current_reviews):
                break
        data = get_data(reviews, language)
        full_data.extend(data)
        driver.execute_script("window.scrollTo(0, 0)")
    except Exception as e:
        print(f"Error encountered for App ID {app_id}: {e}")
        wrong.append(app_id)
    finally:
        driver.quit()
    return full_data, wrong

def save_to_csv(data, filename):
    columns = ["Attitude", "Play Record", "Publish Date", "Free_get", "Refunded", "Content", "Helpful", "Funny", "Award Count", "Poster Link", "Nickname", "Product Count", "Reply Count", "Language"]
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(filename, index=False, encoding='utf-8')

def main():
    full_data = []
    wrong = []
    game_info_df = pd.read_csv('game_info_add4.csv')
    rows = game_info_df.values.tolist()
    for row in rows:
        try:
            reviews, current_wrong = get_language_data(str(row[0]), 'mostrecent', 'english')
            wrong.extend(current_wrong)
            if not reviews:
                continue
            for review in reviews:
                combined_data = [value if value is not None else 'N/A' for value in row] + [value if value is not None else 'N/A' for value in review]
                full_data.append(combined_data)
                #print(combined_data)
                time.sleep(3)
        except Exception as e:
            print(f"Error encountered in main loop for App ID {row[0]}: {e}")
            wrong.append(row[0])
            continue
    save_to_csv(full_data, 'review_info_add4.csv')
    print("App IDs with issues:", wrong)

if __name__ == "__main__":
    main()
