import json, smtplib, os
import aiosqlite, discord, security
from email.mime.text import MIMEText
from email.headerregistry import Address
from email.mime.multipart import MIMEMultipart
from discord_webhook.webhook import DiscordWebhook

embedcolor = 0xff00ff
embedwarning = 0xff9900
embedsuccess = 0x00ff00
embederrorcolor = 0xff0000

cooldown_file = "cooldowns.txt"
smtp_server = security.smtp_server
smtp_user = security.smtp_user
smtp_password = security.smtp_password

def send(username, content, avatar_url, url):
    webhook = DiscordWebhook(url=f'{security.webhook}', content=f'{content}', username=f'{username}', avatar_url=f'{avatar_url}')
    webhook.execute()

async def addstock(_name, _price):
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.execute("INSERT INTO stock (name, price) VALUES (?, ?)", (_name, _price))
    await economy_aiodb.commit()
    await aiocursor.close()

async def getstock():
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.cursor()
    await aiocursor.execute("SELECT name, price FROM stock")
    data = await aiocursor.fetchall()
    await aiocursor.close()
    return data

async def removestock(_name):
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.cursor()
    await aiocursor.execute("DELETE FROM stock WHERE name=?", (_name, ))
    await economy_aiodb.commit()
    await aiocursor.close()

async def adduser_stock(user_id, _name, _count):
    # 주식이 존재하는지 확인합니다.
    stocks = await getstock()
    stock_info = next(((name, price) for name, price in stocks if name == _name), None)
    if stock_info is None:
        raise ValueError(f"{_name} 주식은 존재하지 않습니다.")
    else:
        _, stock_price = stock_info
    # 사용자가 충분한 돈을 가지고 있는지 확인합니다.
    user_money = await getmoney(user_id)
    total_price = stock_price * _count
    if user_money < total_price:
        raise ValueError(f"돈이 부족합니다. 필요한 금액: {total_price}, 현재 잔액: {user_money}")
    # 돈을 차감하고 주식을 추가합니다.
    await removemoney(user_id, total_price)
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.cursor()
    await aiocursor.execute("INSERT INTO user_stock (id, name, count) VALUES (?, ?, ?)", (user_id, _name, _count))
    await economy_aiodb.commit()
    await aiocursor.close()

async def getuser_stock(user_id):
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.cursor()
    await aiocursor.execute("SELECT name, count FROM user_stock WHERE id=?", (user_id,))
    data = await aiocursor.fetchall()
    await aiocursor.close()
    return data

async def removeuser_stock(user_id, _name, _count):
    # 주식이 존재하는지 확인합니다.
    stocks = await getstock()
    stock_info = next((price for name, price in stocks if name == _name), None)

    if stock_info is None:
        raise ValueError(f"{_name} 주식은 존재하지 않습니다.")
    else:
        stock_price = stock_info

    # 주식을 판매하고 돈을 지급합니다.
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.cursor()
    await aiocursor.execute("UPDATE user_stock SET count = count - ? WHERE id = ? AND name = ? AND count >= ?", (_count, user_id, _name, _count))
    
    await aiocursor.execute("SELECT count FROM user_stock WHERE id = ? AND name = ?", (user_id, _name))
    new_count = await aiocursor.fetchone()

    # 주식의 개수가 0이면 레코드를 삭제합니다.
    if new_count and new_count[0] == 0:
        await aiocursor.execute("DELETE FROM user_stock WHERE id = ? AND name = ?", (user_id, _name))

    await economy_aiodb.commit()
    await aiocursor.close()

    sell_price = stock_price * _count
    await addmoney(user_id, sell_price)

async def addmoney(_id, _amount):
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.execute("select * from money where id=?", (_id,))
    dat = await aiocursor.fetchall()
    if not dat:
        await aiocursor.execute("insert into money (id, money) values (?, ?)", (_id, _amount))
    else:
        await aiocursor.execute("update money set money = ? where id = ?", (dat[0][1] + _amount, _id))
    await economy_aiodb.commit()
    await aiocursor.close()

async def getmoney(_id):
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.execute("select * from money where id=?", (_id, ))
    dat = await aiocursor.fetchall()
    await aiocursor.close()
    if dat == False: return 0
    return dat[0][1]

async def removemoney(_id, _amount):
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.execute("select * from money where id=?", (_id, ))
    dat = await aiocursor.fetchall()
    await aiocursor.close()
    if dat == False: return False
    if dat[0][1] < _amount: return False
    aiocursor = await economy_aiodb.execute("update money set money = ? where id = ?", (dat[0][1] - _amount, _id))
    await economy_aiodb.commit()
    await aiocursor.close()
    return True

async def member_status(ctx):
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (ctx.author.id,))
    dbdata = await aiocursor.fetchone()
    await aiocursor.close()
    if dbdata == None:
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value=f"{ctx.author.mention}\n가입되지 않은 유저입니다.")
        await ctx.send(embed=embed, ephemeral=True)
        await exit()
    else:
        tos = dbdata
        if tos == 0:
            embed = discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="이용제한된 유저입니다.")
            await ctx.send(embed=embed, ephemeral=True)
            await exit()

async def database_create(ctx):
    # 서버 아이디 및 서버 이름 가져오기
    server_id = str(ctx.guild.id)
    # 데이터베이스 생성
    conn = await aiosqlite.connect(f'database\\{server_id}.db')
    # 비동기로 커서를 가져옵니다.
    cursor = await conn.cursor()
    # 이후 쿼리를 실행합니다.
    await cursor.execute(f'CREATE TABLE IF NOT EXISTS 경고 (아이디 INTEGER , 관리자 INTEGER, 맴버 INTEGER, 경고 INTEGER, 사유 INTEGER)')
    await cursor.execute(f'CREATE TABLE IF NOT EXISTS 설정 (공지채널 INTEGER , 처벌로그 INTEGER, 입장로그 INTEGER, 퇴장로그 INTEGER, 인증역할 INTEGER, 인증채널 INTEGER)')
    await conn.commit()
    await conn.close()

def send_email(ctx, recipient, verifycode):
    msg = MIMEMultipart()
    msg['From'] = str(Address("CodeStone", addr_spec=smtp_user))  
    msg['To'] = recipient
    msg['Subject'] = '스톤봇 이메일 인증'

    # HTML을 사용하여 이메일 본문을 꾸미기
    body = f"""
    <html>
    <body style="background-color:#368AFF;">
    <center>
    <h1>CodeStone</h1>
    <hr>
    <p>인증번호 : <strong>{verifycode}</strong></p>
    <p>
    안녕하세요.<br>
    {ctx.author.name} 님의 {ctx.guild.name} 인증 코드는 <strong>{verifycode}</strong>입니다.<br>
    {ctx.guild.name} 인증채널에 위 코드를 입력하고 가입을 완료하세요, 이 코드는 1분 후에 만료됩니다.<br>
    감사합니다.
    </p>
    </center>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))  # 'plain' 대신 'html' 사용
    
    server = smtplib.SMTP(smtp_server, 587)
    server.starttls()
    server.login(smtp_user, smtp_password)
    server.send_message(msg)
    server.quit()

# 쿨다운 정보를 로드하는 함수
def load_cooldowns():
    try:
        with open(cooldown_file, "r") as f:
            try:
                cooldowns = json.load(f)
            except json.JSONDecodeError:
                cooldowns = {}
    except FileNotFoundError:
        cooldowns = {}
    return cooldowns

# 쿨다운 정보를 저장하는 함수
def save_cooldowns(cooldowns):
    with open(cooldown_file, "w") as f:
        json.dump(cooldowns, f)

async def addwarn(ctx, _user, _warn, _reason):
    db_path = os.path.join(os.getcwd(), "database", f"{ctx.guild.id}.db")
    if not os.path.exists(db_path):
            await database_create(ctx)
    try:
        aiodb = await aiosqlite.connect(db_path)
        aiocursor = await aiodb.cursor()     # 커서 생성
    except Exception as e:
        print(f"Database connection error: {e}")
        return
    aiocursor = await aiodb.execute("select * from 경고 order by 아이디 desc")
    dat = await aiocursor.fetchone()
    await aiocursor.close()
    if dat is None:
        dat = [0, "asdf"]
    new_id = dat[0] + 1 if dat else 1
    aiocursor = await aiodb.execute("INSERT INTO 경고 (아이디, 관리자, 맴버, 경고, 사유) VALUES (?, ?, ?, ?, ?)", (new_id, ctx.author.id, _user.id, _warn, _reason))
    await aiodb.commit()
    await aiocursor.close()
    aiocursor = await aiodb.execute("SELECT SUM(경고) FROM 경고 WHERE 맴버 = ?", (_user.id,))
    accumulatewarn_result = await aiocursor.fetchone()
    await aiocursor.close()
    accumulatewarn = accumulatewarn_result[0] if accumulatewarn_result and accumulatewarn_result[0] else 0
    embed = discord.Embed(color=embedsuccess)
    embed.add_field(name="✅경고를 지급했어요", value="", inline=False)
    embed.add_field(name="대상", value=_user.mention)
    embed.add_field(name="누적 경고", value=f"{accumulatewarn} / 10 (+ {_warn})")
    embed.add_field(name="사유", value=_reason, inline=False)
    await ctx.send(embed=embed)
    aiocursor = await aiodb.execute("SELECT 처벌로그 FROM 설정")
    설정_result = await aiocursor.fetchone()
    await aiocursor.close()
    return new_id, accumulatewarn, 설정_result  # 설정_result 추가

async def getwarn(ctx, user):
    db_path = os.path.join(os.getcwd(), "database", f"{ctx.guild.id}.db")
    if not os.path.exists(db_path):
        await database_create(ctx)
    aiodb = await aiosqlite.connect(db_path)
    aiocursor = await aiodb.execute(f"SELECT * FROM 경고 WHERE 맴버 = {user.id}")
    dat = await aiocursor.fetchall()
    await aiocursor.close()
    aiocursor = await aiodb.execute("SELECT SUM(경고) FROM 경고 WHERE 맴버 = ?", (user.id,))
    accumulatewarn_result = await aiocursor.fetchone()
    await aiocursor.close()
    accumulatewarn = accumulatewarn_result[0] if accumulatewarn_result and accumulatewarn_result[0] else 0
    return dat, accumulatewarn

async def removewarn(ctx, warn_id):
    db_path = os.path.join(os.getcwd(), "database", f"{ctx.guild.id}.db")
    if not os.path.exists(db_path):
        await database_create(ctx)
    aiodb = await aiosqlite.connect(db_path)
    aiocursor = await aiodb.execute("SELECT * FROM 경고 WHERE 아이디 = ?", (warn_id,))
    dat = await aiocursor.fetchall()
    if not dat:
        return None
    else:
        await aiocursor.execute("DELETE FROM 경고 WHERE 아이디 = ?", (warn_id,))
        await aiodb.commit()  # 변경 사항을 데이터베이스에 확정합니다.
        return warn_id