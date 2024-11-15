import requests
import time
from bs4 import BeautifulSoup
import pandas as pd


#appid = input("steam：请输入appid：")
language = input('请输入想爬取的语言')
nextCursor = "*"  # 索引下一页评论的cursor
reloadDataNum = 0  # 重新拉取次数
reloadDataNumMax = 5  # 重新拉取次数最大 = 5 ， 超过次数结束爬取。
lastedNum = 0
totalEndNum = 0


# 获取评论数据的简化函数
def extract_review_data(review):
    
    review_text = review.find('div', class_='apphub_CardTextContent').text.strip() if review.find('div', class_='apphub_CardTextContent') else "None"
    date_posted = review.find('div', class_='date_posted').text.strip() if review.find('div', class_='date_posted') else "None"
    
    found_helpful_div = review.find('div', class_='found_helpful')
    helpful_count, funny_count = "0", "0"
    if found_helpful_div:
        counts = found_helpful_div.text.strip().split('\n')
        if len(counts) > 1:
            helpful_count = counts[0].split()[0]
            funny_count = counts[1].split()[0]
    
    attitude = review.find('div', class_='title').text.strip() if review.find('div', class_='title') else "None"
    attitude_value = 1 if "Recommended" in attitude else 0
    play_record = review.find('div', class_='hours').text.strip() if review.find('div', class_='hours') else "None"
    free_get = 1 if review.find('div', class_='received_compensation') else 0
    refunded = 1 if review.find('div', class_='refunded') else 0
    award_count = review.find('div', class_='review_award_aggregated')
    award_count = award_count.text.strip() if award_count else "0"
    
    poster_block = review.find('div', class_='apphub_CardContentAuthorBlock tall')
    poster_link = poster_block.find('a', href=True)['href'] if poster_block else "None"
    poster_name = poster_block.find('div', class_='apphub_CardContentAuthorName').text.strip() if poster_block else "None"
    product_count = poster_block.find('div', class_='apphub_CardContentMoreLink') if poster_block else None
    product_count = product_count.text.strip() if product_count else "None"

    reply_count = review.find('div', class_='apphub_CardCommentCount')
    reply_count = reply_count.text.strip() if reply_count else "None"
    
    return [attitude_value, play_record, date_posted, free_get, refunded, review_text,
            helpful_count, funny_count, award_count, poster_link, poster_name, product_count, reply_count]



# 获取评论数据的主函数
def get_game_reviews(appid,language):
    full_data = []
    wrong = []  # 存储出错的 AppID 和错误信息
    isEnd = False

    while True:
        isEnd = False
        global reloadDataNum
        global nextCursor
        global lastedNum
        global totalEndNum 
        #headers = {    'Content-Type': 'application/json'}

        try:
            resp = requests.get(f"https://store.steampowered.com/appreviews/{appid}?cursor={nextCursor}&language={language}&review_type=all&purchase_type=all&filter=recent", timeout=5).json()
        except Exception as e:
            print(f"request failed：请求评论失败，尝试重新拉取...{reloadDataNum}")
            resp = ""
            isEnd = True
            wrong.append([appid, f"请求失败：{e}"])
            reloadDataNum += 1
            time.sleep(1)
    
        if isEnd:
            break  # 退出时返回
        reloadDataNum = 0  # reset

        if lastedNum == len(full_data):
            totalEndNum += 1
            print(f"请求不到更多评论...{totalEndNum}")
            if totalEndNum >= reloadDataNumMax:
                print(f"结束请求...")
                isEnd = True
                reloadDataNum = 5
                time.sleep(1)
            

        else:
            lastedNum = len(full_data)
            totalEndNum = 0
    
        cursor = resp["cursor"]
        cursor = cursor.replace("+", "%2B")
        nextCursor = cursor
        html = resp["html"]  # 本页评论数据
        soup = BeautifulSoup(html, "lxml")

        reviews = soup.find_all('div', class_='apphub_Card modalContentLink interactable')
        if not reviews:
            print("没有更多评论了")
            wrong.append([appid, "没有更多评论"])
            break

        for review in reviews:
            full_data.append(extract_review_data(review))  # 直接提取评论信息
        
        time.sleep(2)

    return full_data, wrong

# 保存错误信息到 CSV
def save_errors_to_csv(errors, filename="error_log.csv"):
    error_df = pd.DataFrame(errors, columns=["AppID", "Error Message"])
    error_df.to_csv(filename, index=False, encoding='utf-8')
    print(f"错误信息已保存到 {filename}")

# 从CSV获取游戏信息并获取评论
def main():
    game_info_df = pd.read_csv('game_info.csv')  # 读取 CSV 文件，确保包含 AppID 列
    all_data, all_errors = [], []

    for index,row in game_info_df.iterrows():
        appid = row['Appid']  # 从 CSV 获取 AppID
        game_title = row['Game Title']
        release_date = row['Release Date']
        price = row['Price']

        print(f"正在获取游戏 {game_title} 的评论...")

       
        global language
        reviews_data, wrong_data = get_game_reviews(appid, language)

        for review in reviews_data:
            all_data.append([appid, game_title, release_date, price] + review)

        if wrong_data:
            all_errors.extend(wrong_data)

    columns = ['Appid', 'Game Title', 'Release Date', 'Price', 'Attitude', 'Play Record', 'Publish Date', 'Free_get',
               'Refunded', 'Content', 'Helpful', 'Funny', 'Award Count', 'Poster Link', 'Poster Name',
               'Product Count', 'Reply Count']
    
    df = pd.DataFrame(all_data, columns=columns)
    df.to_csv("steam_reviews.csv", index=False, encoding="utf-8")
    print("评论数据已保存到 steam_reviews.csv 文件中")

    # 保存错误信息到 CSV 文件
    if all_errors:
        save_errors_to_csv(all_errors)


if __name__ == "__main__":
    main()
