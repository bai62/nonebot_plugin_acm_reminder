from json import loads
from time import strptime, mktime
from html import unescape
from typing import Literal, TypedDict
from httpx import AsyncClient
from httpx._types import URLTypes
from bs4 import BeautifulSoup, ResultSet

class ContestType(TypedDict):
    id: int  # 竞赛ID
    name: str  # 竞赛名称
    writes: list[str]  # 竞赛主办方
    length: int  # 竞赛时长 [分钟]
    time: float  # 竞赛开始时间戳
    platform: Literal["Codeforces", "Nowcoder"]  # 竞赛平台


async def req_get(url: URLTypes) -> str:
    """
    生成一个异步的GET请求

    Args:
        url (URLTypes): 对应的URL

    Returns:
        str: URL对应的HTML
    """
    async with AsyncClient() as client:
        r = await client.get(url)
    return r.content.decode("utf-8")

def html_parse_cf(content: str) -> list[ContestType]:
    """
    处理Codeforces的竞赛列表

    Args:
        content (str): HTML

    Returns:
        list: 竞赛列表
    """
    contest_data: list[ContestType] = []
    
    soup = BeautifulSoup(content, 'html.parser')
    datatable = soup.find('div', class_='datatable')  # 获取到数据表
    if datatable is None:
        return contest_data

    # 解析竞赛信息
    contest_list = datatable.find_all("tr")  # type: ignore
    for i in range(0,2):
        contest=contest_list[i+1]
        cdata = contest.find_all("td")
        if cdata:
            ctime = mktime(strptime(cdata[2].find("span").string, "%b/%d/%Y %H:%M"))
            ctime+=5*60*60
            clength = strptime(str(cdata[3].string).strip("\n").strip(), "%H:%M")
            contest_data.append({"name": str(cdata[0].string).strip("\n").strip(),
                                "time": ctime, 
                                "length": clength.tm_hour * 60 + clength.tm_min,
                                "id": contest.get("data-contestid")})
    return contest_data

def html_parse_nc(content: str) -> list[ContestType]:
    """
    处理牛客的竞赛列表 

    Args:
        content (str): HTML

    Returns:
        list: 竞赛列表
    """
    contest_data: list[ContestType] = []
    soup = BeautifulSoup(content, 'html.parser')
    datatable: ResultSet = soup.find('div', class_='platform-mod js-current').find_all('div', class_='platform-item js-item') #type: ignore
    for i in range(0, 2):
        contest = datatable[i]
        cdata = loads(unescape(contest.get("data-json")))
        if cdata:
            contest_data.append({"name": cdata["contestName"],
                                "time":  cdata["contestStartTime"] / 1000, 
                                "length": cdata["contestDuration"] / 1000 / 60,
                                "id": cdata["contestId"]})
    return contest_data

def html_parse_acw(content: str) -> list[ContestType]:
    """
    处理AcWing的竞赛列表

    Args:
        content (str): HTML

    Returns:
        list: 竞赛列表
    """
    contest_data: list[ContestType] = []
    soup = BeautifulSoup(content, 'html.parser')
    cdata: ResultSet = soup.find('div', class_='activity-index-block') #type: ignore

    if cdata:
        ctime = mktime(strptime(cdata.find_all("span",{'class':'activity_td'})[1].string, "%Y-%m-%d %H:%M:%S"))
        cname = 'AcWing'+str(cdata.find('span',{'class':'activity_title'}).string).replace(" ","")
        contest_data.append({"name":cname,
                             "time": ctime,
                             "length": 75,
                             "id": 1})
    return contest_data