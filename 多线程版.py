import requests, time, re, json, os, random, threading
from bs4 import BeautifulSoup as BS
from PIL import Image


# 文件存在就算了，不存在就创建
def make_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)
    return 0


# 解析网页
def analysis(url):
    header = {
        "authority":"www.haoman8.com",
        "user-agent":"Mozilla/5.0",
        # "":"",
        # "":"",
    }
    r = requests.get(url, headers=header)
    
    # 获取漫画名称
    soup = BS(r.text, "html.parser")
    title = soup.find("h1", {"class":"title"}).attrs["title"]
    
    # 获取漫画简介并保存
    describe = soup.find("p", {"class":"desc-content"}).text
    make_dir(title)
    with open(f"{title}/简介.txt", "wt", encoding="utf-8") as fo:
        fo.write(describe)
    
    # 获取漫画每一章节的信息，并转为json数据
    json_data = re.findall(r"var chapter_list = (.*)", r.text)[0].strip(" ;\r\n")
    # 使用过 sub 把单引号替换为双引号
    json_data = re.sub(r"'", r'"', json_data)
    data = json.loads(json_data)
    # print(type(data))
    return data, title


# 获取爬取章节的起始及结束号
def get_num(num_str):
    try:
        start, end = [int(num) for num in num_str.split(',')]
    except:
        print("章节序号有问题")
        return 0, 0
    # 修改起始章节号
    if start > 0:
        start -= 1
    elif start == 0:
        print("章节序号有问题")
        return 0, 0
    else:
        None
    # 修改结束章节号
    if end == -1:
        end = None
    elif end < -1:
        end += 1
    else:
        None
    return start, end


def multi_thread(chapts, comic_title, start_num=1):
    threads = []
    for index, chapt in enumerate(chapts, start=start_num):
        threads.append(threading.Thread(target=get_pic, args=(chapt, comic_title, index)))
    for thread in threads:
        time.sleep(1+random.random())
        thread.start()
    for thread in threads:
        thread.join()
    print("多线程完毕，真他妈的吊")
    return 0


# 将漫画的图片转为pdf格式
def img2pdf(title, chapt_title):
    print("开始将图片转化为PDF", end="")
    # 要保存的PDF路径
    make_dir(f"{title}/PDF")
    pdf_path = f"{title}/PDF/{chapt_title}.pdf"
    img_list = os.listdir(f"{title}/{chapt_title}")
    # 整理图片顺序
    img_list.sort()
    # 创建Image类型的列表
    image_list = [Image.open(f"{title}/{chapt_title}/{img}") for img in img_list]
    # 保存为PDF
    pdf_header = image_list.pop(0)
    pdf_header.save(pdf_path, "PDF", save_all=True, append_images=image_list)
    print(f"\r章节 {chapt_title} 已转为PDF")
    return 0


# 下载图片
def get_pic(chapt_dic, title, chapt_num):
    # 获取章节名并更改为符合Windows文件命名方式的形式，并尝试更改章节序号格式
    chapt_title = re.sub(r'[\/|":?*<>]+', "_", chapt_dic["name"])
    try:
        # 将章节号修改为四位序号
        chapt_title = re.sub(r"^\d+", f"{chapt_num:0>4d}", chapt_title)
    except:
        # 修改失败就算了
        pass
    make_dir(f"{title}/{chapt_title}")
    # 获取章节图片链接
    chapt_url = "https://www.haoman8.com" + chapt_dic["url"]
    r = requests.get(chapt_url)
    soup = BS(r.text, "html.parser")
    div = soup.find("div", {"class":"acgn-reader-chapter__item-box"})
    img_ls = [img.attrs["data-echo"] for img in div.find_all("img")]
    # 保存图片并显示进度
    for index, img in enumerate(img_ls):
        with open(f"{title}/{chapt_title}/{index:0>3d}.{img.split('.')[-1]}", "wb") as fo:
            fo.write(requests.get(img).content)
        print(f"\r章节 {chapt_title} 下载进度：{index+1}/{len(img_ls)}", end="")
    else:
        print(f"\r章节 {chapt_title} 下载完毕，共 {len(img_ls)} 页.")
    # 图片转为PDF
    img2pdf(title, chapt_title)
    return 0


def main(url):
    chapt_info, comic_title = analysis(url)             # 解析网页
    print(f"漫画名：{comic_title}")
    num = input("请输入要获取的章节序号(第一章为1，最后一章为-1，用英文逗号分隔)：")
    # 获取需要爬取的章节，并判断是否合理，不合理就重新输入
    while True:
        start_chapt, end_chapt = get_num(num)
        if start_chapt == end_chapt == 0:
            continue
        else:
            break
    start_num = int(input("请输入章节起始序号(如无特殊需求则输入1)："))
    print("开始下载漫画")
    # 开启多线程下载漫画
    multi_thread(chapt_info[start_chapt:end_chapt], comic_title, start_num)
    return 0


if __name__ == "__main__":
    url = input("请输入漫画url：").strip()
    start_time = time.time()
    main(url)
    print(f"\n\n爬虫运行完毕，耗时{time.time()-start_time:.1f}s")
