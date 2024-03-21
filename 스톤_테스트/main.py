import security
import asyncio, discord
import datetime, aiosqlite
import os, random, time, string
from def_list import *
from captcha.image import ImageCaptcha
from discord.ext import commands, tasks
from discord import app_commands

token = security.token
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
developer = int(security.developer_id)

embedcolor = 0xff00ff
embedwarning = 0xff9900
embedsuccess = 0x00ff00
embederrorcolor = 0xff0000
##################################################################################################
@tree.command(name='인증_이메일', description='이메일 인증')
@app_commands.rename(email="이메일")
async def email_verify(interaction, email: str):
    db_path = os.path.join(os.getcwd(), "database", f"{interaction.guild.id}.db")
    if not os.path.exists(db_path):
        await database_create(interaction)
    else:
        aiodb = await aiosqlite.connect(db_path)
        aiocursor = await aiodb.execute("SELECT 인증역할, 인증채널 FROM 설정")
        role_id, channel_id = await aiocursor.fetchone()
        await aiocursor.close()
        await aiodb.close()
    if role_id:
        role_id = role_id
        role = interaction.guild.get_role(role_id)
        if role:
            if channel_id:
                channel_id = channel_id
                channel = interaction.guild.get_channel(channel_id)
                if channel and channel == interaction.channel:
                    # 인증 채널에서만 작동하는 코드 작성
                    verifycode = random.randint(100000, 999999)
                    send_email(interaction, email, verifycode)
                    embed = discord.Embed(color=embedsuccess)  # Here is the change
                    embed.add_field(name="이메일 인증", value=f"**{email}** 으로 인증번호를 전송했습니다.")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    
                    def check(m):
                        return m.author == interaction.author and m.content == str(verifycode)
                    try:
                        msg = await client.wait_for('message', check=check, timeout=60)
                        if msg:
                            await interaction.channel.purge(limit=1)
                            await interaction.author.add_roles(role)
                            embed = discord.Embed(color=embedsuccess)
                            embed.add_field(name="이메일 인증", value=f"{interaction.author.mention} 메일 인증이 완료되었습니다.")
                            await interaction.response.send_message(embed=embed)
                    except TimeoutError:
                        embed = discord.Embed(color=embederrorcolor)
                        embed.add_field(name="❌ 오류", value="인증 시간이 초과되었습니다. 다시 시도해주세요.")
                        await interaction.response.send_message(embed=embed)
                else:
                    embed = discord.Embed(color=embederrorcolor)
                    embed.add_field(name="❌ 오류", value="인증 채널에서만 인증 명령어를 사용할 수 있습니다.")
                    await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="인증채널이 설정되지 않은 서버입니다.\n서버 관리자에게 문의하세요.")
                await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="**인증역할**이 설정되지 않은 서버입니다.\n서버 관리자에게 문의하세요.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="**인증역할**이 설정되지 않은 서버입니다.\n서버 관리자에게 문의하세요.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="캡챠 인증")
async def 인증(interaction):
    db_path = os.path.join(os.getcwd(), "database", f"{interaction.guild.id}.db")
    if not os.path.exists(db_path):
        await database_create(interaction)
    else:
        aiodb = await aiosqlite.connect(db_path)
        aiocursor = await aiodb.execute("SELECT 인증역할, 인증채널 FROM 설정")
        role_id, channel_id = await aiocursor.fetchone()
        await aiocursor.close()
        await aiodb.close()
    if role_id:
        role_id = role_id
        role = interaction.guild.get_role(role_id)
        if role:
            if channel_id:
                channel_id = channel_id
                channel = interaction.guild.get_channel(channel_id)
                if channel and channel == interaction.channel:
                    # 인증 채널에서만 작동하는 코드 작성
                    image_captcha = ImageCaptcha()
                    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    data = image_captcha.generate(captcha_text)
                    image_path = 'captcha.png'  # 이미지 파일 경로
                    with open(image_path, 'wb') as f:
                        f.write(data.getvalue())  # BytesIO 객체를 파일로 저장
                    embed = discord.Embed(color=embedsuccess)
                    embed.add_field(name="인증", value="코드를 입력해주세요(6 자리)")
                    file = discord.File(image_path, filename='captcha.png')
                    embed.set_image(url="attachment://captcha.png")  # 이미지를 임베드에 첨부
                    await interaction.response.send_message(embed=embed, file=file, ephemeral=True)
                    def check(m):
                        return m.author == interaction.author and m.content == captcha_text
                    try:
                        msg = await client.wait_for('message', timeout=60.0, check=check)
                        await interaction.channel.purge(limit=1)
                    except TimeoutError:
                        await interaction.channel.purge(limit=1)
                        embed = discord.Embed(color=embederrorcolor)
                        embed.add_field(name="❌ 오류", value="시간이 초과되었습니다. 다시 시도해주세요.")
                        await interaction.response.send_message(embed=embed)
                    else:
                        # 인증 완료 처리 코드 작성
                        await interaction.author.add_roles(role)
                        embed = discord.Embed(color=embedsuccess)
                        embed.add_field(name="인증 완료", value=f"{interaction.author.mention} 캡챠 인증이 완료되었습니다.")
                        await interaction.response.send_message(embed=embed)
                else:
                    embed = discord.Embed(color=embederrorcolor)
                    embed.add_field(name="❌ 오류", value="인증 채널에서만 인증 명령어를 사용할 수 있습니다.")
                    await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="인증채널을 선택해주세요.")
                await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="인증역할을 찾을 수 없습니다.")
            await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="인증역할을 선택해주세요.")
        await interaction.response.send_message(embed=embed)

@tree.command(description="문의에 답장 [개발자전용]")
@app_commands.rename(member_id="유저_id", context="내용")
async def 답장전송(interaction, member_id: str, context: str):
    if interaction.author.id == developer:
        user = client.get_user(int(member_id))
        if user == None:
            embed = discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="유저 정보가 확인되지 않습니다.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(color=embedsuccess)
            embed.add_field(name="성공", value="전송이 완료되었습니다.")
            await interaction.response.send_message(embed=embed)
            await user.send(f"보낸 사람 : {str(interaction.author)}\n```{context}```")
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="자신이나 다른유저의 지갑조회")
@app_commands.rename(member_id="유저_id")
async def 지갑(interaction, member_id: str):
    user = await client.fetch_user(member_id)
    await interaction.response.defer()
    if user is None:
        user = interaction.author
    conn = await aiosqlite.connect('economy.db')
    c = await conn.cursor()
    await c.execute('SELECT * FROM money WHERE id=?', (user.id,))
    data = await c.fetchone()
    if data is None:
        await interaction.response.send_message(f"{user.mention}, 가입되지 않은 유저입니다.", ephemeral=True)
        await conn.close()
        return
    money = data[1]
    await c.execute('SELECT tos FROM user WHERE id=?', (user.id,))
    tos_data = await c.fetchone()
    await conn.close()
    if tos_data is None:
        await interaction.response.send_message(f"{user.mention}, 이용제한된 유저입니다.", ephemeral=True)
        return
    if tos_data[0] == 1:
        tos = '정상'
    else:
        tos = '이용제한'
    embed = discord.Embed(title=f"{user.name}의 지갑", color=0x00ff00)
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.add_field(name="잔액", value=f"{money:,}원")
    embed.add_field(name="계정상태", value=f"{tos}")
    await interaction.response.send_message(embed=embed)

@tree.command(description="돈수정 [개발자전용]")
@app_commands.rename(user="유저", choice="선택", money="돈")
@app_commands.choices(choice=[app_commands.Choice(name="차감", value="차감"), app_commands.Choice(name="추가", value="추가")])
async def 돈수정(interaction, user: discord.Member,choice: app_commands.Choice[str], money: int):
    if interaction.author.id == developer:
        if choice.value == "차감":
            if not await removemoney(user.id, money):
                return await interaction.response.send_message("그 사용자의 포인트을 마이너스로 줄수없어요!")
            embed = discord.Embed(title="잔액차감", color=embedsuccess)
            embed.add_field(name="차감금액", value=f"{money:,}원")
            embed.add_field(name="대상", value=f"{user.mention}")
            await interaction.response.send_message(embed=embed)
        elif choice.value == "추가":
            await addmoney(user.id, money)
            embed = discord.Embed(title="잔액추가", color=embedsuccess)
            embed.add_field(name="추가금액", value=f"{money:,}원")
            embed.add_field(name="대상", value=f"{user.mention}")
            await interaction.response.send_message(embed=embed)
        else:
            embed=discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="차감, 추가중 선택해주세요.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="돈벌기", description="간단한 문제풀이로 3,000 ~ 30,000원을 얻습니다.")
async def earn_money(interaction):
    await member_status(interaction)
    cooldowns = load_cooldowns()
    last_execution_time = cooldowns.get(str(interaction.author.id), 0)
    current_time = time.time()
    cooldown_time = 30
    if current_time - last_execution_time < cooldown_time:
        remaining_time = round(cooldown_time - (current_time - last_execution_time))
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="쿨타임", value=f"{interaction.author.mention}, {remaining_time}초 후에 다시 시도해주세요.")
        await interaction.response.send_message(embed=embed)
        return
    number_1 = random.randrange(2, 10)
    number_2 = random.randrange(2, 10)
    operator = random.randrange(1, 5)
    random_add_money = random.randrange(3000, 30001)
    random_add_money = int(round(random_add_money, -3))
    if operator == 1 or operator == 3:
        correct_answer = number_1 + number_2
        await interaction.response.send_message(f"{number_1} + {number_2} =")
    elif operator == 2 or operator == 4:
        correct_answer = number_1 * number_2
        await interaction.response.send_message(f"{number_1} * {number_2} =")
    else:
        await interaction.response.send_message('잘못된 연산자입니다. 다음 기회에 도전해주세요.')
        return
    def check(msg):
        return msg.author == interaction.author and msg.channel == interaction.channel and int(msg.content) == correct_answer
    try:
        msg = await client.wait_for('message', timeout=7.0, check=check)
    except asyncio.TimeoutError:
        await interaction.response.send_message('시간이 초과되었습니다. 다음 기회에 도전해주세요.')
    else:
        if msg.content == str(correct_answer):
            cooldowns[str(interaction.author.id)] = current_time
            save_cooldowns(cooldowns)
            embed = discord.Embed(color=embedsuccess)
            await addmoney(interaction.author.id, random_add_money)
            embed.add_field(name="정답", value=f"{interaction.author.mention}, {random_add_money:,}원이 지급되었습니다.")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f'틀렸습니다! 정답은 {correct_answer}입니다.')

@tree.command(description="돈 송금")
@app_commands.rename(받는사람="받는사람", money="금액")
async def 송금(interaction, 받는사람: discord.Member, money: int):
    await member_status(interaction)
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (받는사람.id,))
    dbdata = await aiocursor.fetchone()
    await aiocursor.close()
    if dbdata is not None:
        if int(dbdata[0]) == 0:
            embed=discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="받는사람이 이용제한상태이므로 송금할수없습니다.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            await exit()
        else:
            pass
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="받는사람이 미가입상태이므로 송금할수없습니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await exit()
    if money < 0:
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="송금 금액은 음수가 될 수 없습니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
    송금인 = interaction.author
    송신인_잔액 = await getmoney(송금인.id)
    if 송신인_잔액 < money:
        return await interaction.response.send_message(f"{송금인.mention}님의 잔액이 부족하여 송금할 수 없습니다.")
    await removemoney(송금인.id, money)
    await addmoney(받는사람.id, money)
    embed = discord.Embed(title="송금 완료", color=embedsuccess)
    embed.add_field(name="송금인", value=f"{송금인.mention}")
    embed.add_field(name="받는사람", value=f"{받는사람.mention}")
    embed.add_field(name="송금 금액", value=f"{money:,}")
    await interaction.response.send_message(embed=embed)

@tree.command(description="도박 (확률 25%, 2배)")
@app_commands.rename(money="금액")
async def 도박(interaction, money: int):
    await member_status(interaction)
    user = interaction.author
    current_money = await getmoney(user.id)  # 현재 보유 금액 조회
    if money > current_money:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="가지고 있는 돈보다 배팅 금액이 많습니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    random_number = random.randrange(1, 101)
    if random_number <= 75: # 실패
        await removemoney(user.id, money)
        embed = discord.Embed(title="실패", description=f"{money:,}원을 잃었습니다.", color=embederrorcolor)
        await interaction.response.send_message(embed=embed)
    elif random_number > 75: # 성공
        await addmoney(user.id, money)
        embed = discord.Embed(color=embedsuccess)
        embed.add_field(name="성공", value=f"{money:,}원을 얻었습니다.")
        await interaction.response.send_message(embed=embed)

@tree.command(description="도박 (확률 50%, 1.5배, 실패시 -0.75배)")
@app_commands.rename(money="금액")
async def 도박2(interaction, money: int):
    await member_status(interaction)
    user = interaction.author
    current_money = await getmoney(user.id)  # 현재 보유 금액 조회
    if money > current_money:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="가지고 있는 돈보다 배팅 금액이 많습니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    random_number = random.randrange(1, 101)
    if random_number <= 50: # 실패
        money = round(money * 0.75)
        await removemoney(user.id, money)
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="실패", value=f"{money:,}원을 잃었습니다.")
        await interaction.response.send_message(embed=embed)
    elif random_number > 50: # 성공
        money = round(money * 0.5)
        await addmoney(user.id, money)
        embed = discord.Embed(color=embedsuccess)
        embed.add_field(name="성공", value=f"{money:,}원을 얻었습니다.")
        await interaction.response.send_message(embed=embed)

@tree.command(description="도박 (숫자맞추기 1~5, 확률 20%, 최대 3배, 실패시 -1.5배)")
@app_commands.rename(number="숫자", money="금액")
async def 숫자도박(interaction, number: int, money: int):
    await member_status(interaction)
    user = interaction.author
    current_money = await getmoney(user.id)  # 현재 보유 금액 조회
    if round(money * 1.5) > current_money:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="가진금액보다 배팅금이 많습니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return
    else:
        if number >= 6:
            embed=discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="1 ~ 5중 선택해주세요.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        elif number <= 0:
            embed=discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="1 ~ 5중 선택해주세요.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            random_number = random.randrange(1, 6)
            if random_number == number:
                await addmoney(user.id, (money * 2))
                embed = discord.Embed(color=embedsuccess)
                money = money * 2
                embed.add_field(name="성공", value=f"{money:,}원을 얻었습니다.")
                await interaction.response.send_message(embed=embed)
            else:
                money = round(money * 1.5)
                await removemoney(user.id, money)
                embed = discord.Embed(color=embederrorcolor)
                embed.add_field(name="실패", value=f"{money:,}원을 잃었습니다.")
                await interaction.response.send_message(embed=embed)

@tree.command(description="일부명령어 이용제한 [개발자전용]")
@app_commands.rename(user="유저", reason="이유")
async def 이용제한(interaction, user: discord.Member, reason: str = None):
    if interaction.author.id == developer:
        if reason is None:
            reason = "없음"
        economy_aiodb = await aiosqlite.connect("economy.db")
        aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (user.id,))
        dbdata = await aiocursor.fetchone()
        await aiocursor.close()
        if dbdata is not None:
            if int(dbdata[0]) == 0:
                embed=discord.Embed(color=embederrorcolor)
                embed.add_field(name="이용제한", value=f"{user.mention}는 이미 차단된 회원입니다.")
                await interaction.response.send_message(embed=embed)
            else:
                embed=discord.Embed(title="이용제한", color=embederrorcolor)
                embed.add_field(name="대상", value=f"{user.mention}")
                embed.add_field(name="사유", value=f"{reason}")
                await interaction.response.send_message(embed=embed)
                aiocursor = await economy_aiodb.execute("UPDATE user SET tos=? WHERE id=?", (0, user.id))
                await economy_aiodb.commit()
                await aiocursor.close()
        else:
            embed=discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value=f"{user.mention}\n가입되지 않은 회원입니다.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="일부명령어 이용제한해제 [개발자전용]")
@app_commands.rename(user="유저")
async def 제한해제(interaction, user: discord.Member):
    if interaction.author.id == developer:
        economy_aiodb = await aiosqlite.connect("economy.db")
        aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (user.id,))
        dbdata = await aiocursor.fetchone()
        await aiocursor.close()
        if dbdata is not None:
            if int(dbdata[0]) == 0:
                embed=discord.Embed(title=f"{user.mention}\n차단이 해제되었습니다.", color=embederrorcolor)
                await interaction.response.send_message(embed=embed)
                aiocursor = await economy_aiodb.execute("UPDATE user SET tos=? WHERE id=?", (1, user.id))
                await economy_aiodb.commit()
                await aiocursor.close()
            else:
                embed=discord.Embed(title=f"{user.mention}\n 차단되지 않은 유저입니다.", color=embederrorcolor)
                await interaction.response.send_message(embed=embed)
        else:
            embed=discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value=f"{interaction.author.mention}\n가입되지 않은 유저입니다.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="게임기능 가입")
async def 가입(interaction):
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (interaction.author.id,))
    dbdata = await aiocursor.fetchone()
    await aiocursor.close()
    if dbdata == None:
        aiocursor = await economy_aiodb.execute("INSERT INTO user (id, tos) VALUES (?, ?)", (interaction.author.id, 1))
        await economy_aiodb.commit()
        await aiocursor.close()
        await addmoney(interaction.author.id, 30000)
        embed=discord.Embed(color=embedsuccess)
        embed.add_field(name="✅ 가입", value=f"{interaction.author.mention} 가입이 완료되었습니다.\n지원금 30,000원이 지급되었습니다.")
        await interaction.response.send_message(embed=embed)
    else:
        if int(dbdata[0]) == 0:
            embed=discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="이용제한된 유저입니다.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed=discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value=f"{interaction.author.mention} 이미 가입된 유저입니다.")
            await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="게임기능 탈퇴")
async def 탈퇴(interaction):
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (interaction.author.id,))
    dbdata = await aiocursor.fetchone()
    await aiocursor.close()
    
    if dbdata is not None:
        if int(dbdata[0]) == 0:
            embed = discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="이용제한된 유저입니다.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(color=embedwarning)
            embed.add_field(name="탈퇴", value="경고! 탈퇴시 모든 데이터가 **즉시 삭제**되며\n보유중인 잔액이 초기화됩니다.")
            await interaction.response.send_message(embed=embed, view=authbutton(economy_aiodb, interaction.author.id))
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value=f"{interaction.author.mention}\n가입되지 않은 유저입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

class authbutton(discord.ui.View):
    def __init__(self, economy_aiodb, author_id):
        super().__init__(timeout=None)
        self.economy_aiodb = economy_aiodb
        self.author_id = author_id
        self.closed = False  # 새로운 속성 추가

    def is_closed(self):  # is_closed() 메서드 추가
        return self.closed

    @discord.ui.button(label="탈퇴", style=discord.ButtonStyle.green)
    async def 탈퇴(self, button: discord.ui.Button, interaction: discord.MessageInteraction):
        await interaction.channel.purge(limit=1)
        embed = discord.Embed(color=0x00FF00)
        embed.add_field(name="탈퇴 완료!", value="탈퇴가 완료되었습니다!")
        await interaction.response.send_message(embed=embed)
        aiocursor = await self.economy_aiodb.execute("DELETE FROM user WHERE id=?", (self.author_id,))
        aiocursor = await self.economy_aiodb.execute("DELETE FROM money WHERE id=?", (self.author_id,))
        await self.economy_aiodb.commit()
        await aiocursor.close()
        self.stop()
        button.disabled = True

    @discord.ui.button(label="취소", style=discord.ButtonStyle.red)
    async def 취소(self, button: discord.ui.Button, interaction: discord.MessageInteraction):
        await interaction.channel.purge(limit=1)
        embed = discord.Embed(color=0x00FF00)
        embed.add_field(name="탈퇴 취소", value="탈퇴가 취소되었습니다.")
        await interaction.response.send_message(embed=embed)
        self.stop()
        button.disabled = True

async def update_stock_prices():
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.cursor()
    await aiocursor.execute("SELECT name, price FROM stock")
    stocks = await aiocursor.fetchall()

    for stock in stocks:
        name, price = stock
        new_price = round(price * random.uniform(0.9, 1.1), -1)
        new_price = min(new_price, 500000)  # 주식 가격 상한가
        new_price = max(new_price, 5000)  # 주식 가격 하한가
        new_price = int(new_price)
        await aiocursor.execute("UPDATE stock SET price = ? WHERE name = ?", (new_price, name))

    await economy_aiodb.commit()
    await aiocursor.close()

@tree.command(description="주식리스트")
async def 주식리스트(interaction):
    data = await getstock()
    message = "\n".join(f"{name} | {price:,}원" for name, price in data)
    await interaction.response.send_message(message)

@tree.command(description="주식추가")
async def 주식추가(interaction, _name: str, _price: float):
    if interaction.author.id == developer:
        await addstock(_name, _price)
        price = int(_price)
        await interaction.response.send_message(f"{_name} 주식을 {price:,} 가격으로 추가하였습니다.")
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="주식삭제")
async def 주식삭제(interaction, _name: str):
    if interaction.author.id == developer:
        await removestock(_name)
        await interaction.response.send_message(f"{_name} 주식을 삭제하였습니다.")
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="보유주식확인")
async def 보유주식확인(interaction):
    stocks = await getuser_stock(interaction.author.id)
    if not stocks:
        await interaction.response.send_message("보유하고 있는 주식이 없습니다.")
    else:
        market_stocks = await getstock()
        response = "보유하고 있는 주식:\n"
        for name, count in stocks:
            stock_price = next((price for stock_name, price in market_stocks if stock_name == name), None)
            if stock_price is None:
                response += f"{name} | {count}개 (현재 가격 정보를 가져오지 못했습니다.)\n"
            else:
                response += f"{name} | {stock_price:,} | {count:,}개\n"
        await interaction.response.send_message(response)

@tree.command(description="주식구매")
async def 주식구매(interaction, _name: str, _count: int):
    try:
        stocks = await getstock()
        stock_info = next((price for name, price in stocks if name == _name), None)

        if stock_info is None:
            raise ValueError(f"{_name} 주식은 존재하지 않습니다.")
        else:
            stock_price = stock_info

        total_price = stock_price * _count
        await adduser_stock(interaction.author.id, _name, _count)
        count = int(_count)
        await interaction.response.send_message(f"{_name} 주식을 {count:,}개 구매하였습니다.\n총 구매가격은 {total_price:,}원 입니다.")
    except ValueError as e:
        await interaction.response.send_message(str(e))

@tree.command(description="주식판매")
async def 주식판매(interaction, _name: str, _count: int):
    try:
        stocks = await getstock()
        stock_info = next((price for name, price in stocks if name == _name), None)

        if stock_info is None:
            raise ValueError(f"{_name} 주식은 존재하지 않습니다.")
        else:
            stock_price = stock_info

        total_price = stock_price * _count
        await removeuser_stock(interaction.author.id, _name, _count)
        count = int(_count)
        await interaction.response.send_message(f"{_name} 주식을 {count:,}개 판매하였습니다.\n총 판매가격은 {total_price:,}원 입니다.")
    except ValueError as e:
        await interaction.response.send_message(str(e))

##################################################################################################
@tree.command(description="채널설정(로그채널 및 기타채널을 설정합니다) [관리자전용]")
@app_commands.rename(kind="종류", channel="채널")
@app_commands.choices(kind=[app_commands.Choice(name="공지채널", value="공지채널"), app_commands.Choice(name="처벌로그", value="처벌로그"), app_commands.Choice(name="입장로그", value="입장로그"), app_commands.Choice(name="퇴장로그", value="퇴장로그"), app_commands.Choice(name="인증채널", value="인증채널")])
async def 서버설정(interaction, kind: str, channel: discord.TextChannel):
    if interaction.author.guild_permissions.manage_messages:
        db_path = os.path.join(os.getcwd(), "database", f"{channel.guild.id}.db")
        if not os.path.exists(db_path):
            await database_create(interaction)
        else:
            try:
                aiodb = await aiosqlite.connect(db_path)
                aiocursor = await aiodb.execute("SELECT * FROM 설정")
                dat = await aiocursor.fetchall()
                await aiocursor.close()
                if not dat:
                    aiocursor = await aiodb.execute(
                        f"INSERT INTO 설정 ({kind.value}) VALUES (?)", (channel.id,))
                    await aiodb.commit()
                    await aiocursor.close()
                else:
                    aiocursor = await aiodb.execute(f"UPDATE 설정 SET {kind.value} = ?", (channel.id,))
                    await aiodb.commit()
                    await aiocursor.close()
                    embed = discord.Embed(color=embedsuccess)
                    embed.add_field(name="채널설정", value=f"{channel.mention}이(가) **{kind.value}**로 설정되었습니다")
                    await interaction.response.send_message(embed=embed)
            except Exception as e:
                embed = discord.Embed(color=embederrorcolor)
                embed.add_field(name="오류 발생", value=f"데이터베이스 연결 중 오류가 발생했습니다: {e}")
                await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행 가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="역할설정(인증역할 및 기타역할을 설정합니다) [관리자전용]")
@app_commands.rename(kind="종류", role="역할")
@app_commands.choices(kind=[app_commands.Choice(name="인증역할", value="인증역할")])
async def 서버설정_역할(interaction, kind: str, role: discord.Role):
    if interaction.author.guild_permissions.manage_messages:
        db_path = os.path.join(os.getcwd(), "database", f"{interaction.guild.id}.db")
        if not os.path.exists(db_path):
            await database_create(interaction)
        else:
            aiodb = await aiosqlite.connect(db_path)
            aiocursor = await aiodb.execute("SELECT * FROM 설정")
            dat = await aiocursor.fetchall()
            await aiocursor.close()
            if not dat:
                aiocursor = await aiodb.execute(
                    f"INSERT INTO 설정 ({kind}) VALUES (?)", (role.id,))
                await aiodb.commit()
                await aiocursor.close()
            else:
                aiocursor = await aiodb.execute(f"UPDATE 설정 SET {kind} = ?", (role.id,))
                await aiodb.commit()
                await aiocursor.close()
                embed = discord.Embed(color=embedsuccess)
                embed.add_field(name="역할설정", value=f"{role.mention}이(가) **{kind}**로 설정되었습니다")
                await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행 가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="서버정보", description="설정되있는 로그채널을 확인할 수 있습니다 [관리자전용]")
async def server_info(interaction: discord.Interaction):
    if interaction.user.guild_permissions.manage_messages:
        db_path = os.path.join(os.getcwd(), "database", f"{interaction.guild.id}.db")
        if not os.path.exists(db_path):
            await database_create(interaction)
        aiodb = await aiosqlite.connect(db_path)
        aiocursor = await aiodb.execute("SELECT * FROM 설정")
        dat = await aiocursor.fetchone()
        await aiocursor.close()
        embed = discord.Embed(title="서버설정", color=embedcolor)
        if dat:
            if dat[0]:
                announcement_channel = interaction.guild.get_channel(int(dat[0]))
                embed.add_field(name="공지채널", value=f"<#{announcement_channel.id}>", inline=False)
            else:
                embed.add_field(name="공지채널", value="설정되지 않음", inline=False)
            if dat[1]:
                punishment_log_channel = interaction.guild.get_channel(int(dat[1]))
                embed.add_field(name="처벌로그", value=f"<#{punishment_log_channel.id}>", inline=False)
            else:
                embed.add_field(name="처벌로그", value="설정되지 않음", inline=False)
            if dat[2]:
                entry_log_channel = interaction.guild.get_channel(int(dat[2]))
                embed.add_field(name="입장로그", value=f"<#{entry_log_channel.id}>", inline=False)
            else:
                embed.add_field(name="입장로그", value="설정되지 않음", inline=False)
            if dat[3]:
                exit_log_channel_id = dat[3]
                exit_log_channel = interaction.guild.get_channel(int(exit_log_channel_id))
                embed.add_field(name="퇴장로그", value=f"<#{exit_log_channel.id}>", inline=False)
            else:
                embed.add_field(name="퇴장로그", value="설정되지 않음", inline=False)
            if dat[4]:
                auth_role_id = dat[4]
                auth_role = interaction.guild.get_role(int(auth_role_id))
                if auth_role:  # 역할을 찾을 수 있는 경우
                    embed.add_field(name="인증역할", value=f"<@&{auth_role.id}>", inline=False)
                else:  # 역할을 찾을 수 없는 경우
                    embed.add_field(name="인증역할", value="역할을 찾을 수 없음", inline=False)
            else:
                embed.add_field(name="인증역할", value="설정되지 않음", inline=False)
            if dat[5]:
                exit_log_channel_id = dat[5]
                exit_log_channel = interaction.guild.get_channel(int(exit_log_channel_id))
                embed.add_field(name="인증채널", value=f"<#{exit_log_channel.id}>")
            else:
                embed.add_field(name="인증채널", value="설정되지 않음")
        await interaction.response.send_message(embed=embed)
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행 가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
##################################################################################################
@tree.command(description="봇 정보")
async def 봇정보(interaction):
    embed = discord.Embed(title="봇 정보", description="V 1.3.4", color=embedcolor)
    embed.add_field(name="개발 언어", value="파이썬(python)")
    embed.add_field(name="호스팅", value="개인서버")
    embed.add_field(name="서포트서버", value="[CodeStone](https://discord.gg/JxzhpUp49n)")
    embed.add_field(name="개발자", value="stone6718, sihoox2")
    await interaction.response.send_message(embed=embed)

@tree.command(description="개발자에게 후원하기!")
async def 후원(interaction):
    embed = discord.Embed(title="후원", color=embedcolor)
    embed.add_field(name="익명송금", value="https://toss.me/codestone")
    await interaction.response.send_message(embed=embed)

@tree.command(description="개발자 공지 [개발자전용]")
@app_commands.rename(content="내용")
async def 개발자_공지(interaction, *, content: str):
    if interaction.author.id == developer:
        for guild in client.guilds:
            server_remove_date = datetime.datetime.now()
            embed1 = discord.Embed(title=f"개발자 공지", description=f"```{content}```", color=embedcolor)
            embed1.set_footer(text=f'To. CodeStone({interaction.author.name})\n{server_remove_date.strftime("전송시간 %Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후")}')
            for channel in guild.text_channels:
                try:
                    if channel.topic.find("-STONE") != -1:
                        chan = channel
                except:
                    pass
            try:
                chan
                if chan.permissions_for(guild.me).send_messages:
                    await chan.send(embed=embed1)
                    del chan
            except:
                for channel in guild.text_channels:
                    if channel.permissions_for(guild.me).send_messages:
                        embed1.set_footer(text=f'To. CodeStone({interaction.author.name})\n{server_remove_date.strftime("전송시간 %Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후")}')
                        try:
                            await channel.send(embed=embed1)
                        except:
                            pass
                        break
        embed = discord.Embed(title="공지 업로드 완료!", color=embedsuccess)
        await interaction.response.send_message(embed=embed)
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="개발자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
##################################################################################################
@tree.command(description="슬로우모드 설정 [관리자전용]")
@app_commands.rename(time="시간")
@app_commands.describe(time="시간(초)")
async def 슬로우모드(interaction: discord.Interaction, time: int):
    if interaction.user.guild_permissions.manage_messages:
        if time == 0:
            await interaction.channel.edit(slowmode_delay=0)
            await asyncio.sleep(1)  # time.sleep(1)을 asyncio.sleep(1)으로 변경
            embed = discord.Embed(color=embedsuccess)
            embed.add_field(name="슬로우모드", value="✅슬로우모드를 껐어요.")
            await interaction.response.send_message(embed=embed)
            return
        elif time > 21600:
            embed = discord.Embed(color=embederrorcolor)
            embed.add_field(name="슬로우모드", value="❌슬로우모드를 6시간 이상 설정할수 없어요.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        else:
            await interaction.channel.edit(slowmode_delay=time)
            await asyncio.sleep(1)  # time.sleep(1)을 asyncio.sleep(1)으로 변경
            embed = discord.Embed(color=embedsuccess)
            embed.add_field(name="슬로우모드", value=f"✅ 성공적으로 슬로우모드를 {time}초로 설정했어요.")
            await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="청소", description="청소 [관리자전용]")
@app_commands.rename(num="개수")
async def clear(interaction: discord.Interaction, num: int):
    if interaction.user.guild_permissions.manage_messages:
        await interaction.channel.purge(limit=num)
        time.sleep(1)
        embed = discord.Embed(title="청소", color=embedsuccess)
        embed.add_field(name="", value=f"{num}개의 메시지를 지웠습니다.")
        await interaction.response.send_message(embed=embed, ephemeral=False) # 공개 메시지로 변경
    else:
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="공지", description="공지 [관리자전용]")
@app_commands.rename(content="내용")
async def notification(interaction: discord.Interaction, *, content: str):
    if interaction.user.guild_permissions.manage_messages:
        db_path = os.path.join(os.getcwd(), "database", f"{interaction.guild.id}.db")
        if not os.path.exists(db_path):
            await database_create(interaction)
        else:
            aiodb = await aiosqlite.connect(db_path)
            aiocursor = await aiodb.execute("SELECT 공지채널 FROM 설정")
            설정_result = await aiocursor.fetchone()
            await aiocursor.close()
            
            공지채널 = None
            if 설정_result:
                공지채널_id = 설정_result[0]
                공지채널 = client.get_channel(공지채널_id)
            
            if 공지채널:
                for guild in client.guilds:
                    server_remove_date = datetime.datetime.now()
                    embed1 = discord.Embed(title=f"{guild.name} 공지", description=f"```{content}```", color=embedcolor)
                    embed1.set_footer(text=f'To. {interaction.user.display_name}\n{server_remove_date.strftime("전송시간 %Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후")}')
                    try:
                        chan = guild.get_channel(공지채널_id)
                        if chan and chan.permissions_for(guild.me).send_messages:
                            await chan.send(embed=embed1)
                    except Exception as e:
                        print(e)  # 오류를 콘솔에 출력
            else:
                embed = discord.Embed(title="오류", description="공지채널이 없습니다.\n공지채널을 설정해주세요.", color=embederrorcolor)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            embed = discord.Embed(title="공지 업로드 완료!", color=embedsuccess)
            await interaction.response.send_message(embed=embed)
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)
##################################################################################################
@tree.command(description="추방 [관리자전용]")
@app_commands.rename(user="유저", reason="사유")
async def 추방(interaction, user: discord.Member, reason: str = None):
    if interaction.author.guild_permissions.kick_members:
        try:
            await interaction.guild.kick(user)
        except:
            embed = discord.Embed(title=f"{user.name}를 추방하기엔 권한이 부족해요...", color=embederrorcolor)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(title="✅추방을 완료했어요", color=embedsuccess)
            embed.add_field(name="대상", value=f"{user.mention}")
            embed.add_field(name="사유", value=f"{reason}", inline=False)
            await interaction.response.send_message(embed=embed)
            db_path = os.path.join(os.getcwd(), "database", f"{interaction.guild.id}.db")
            if not os.path.exists(db_path):
                await database_create(interaction)
            aiodb = await aiosqlite.connect(db_path)
            aiocursor = await aiodb.execute("select * from 설정 order by 공지채널 desc")
            dat = await aiocursor.fetchone()
            await aiocursor.close()
            aiocursor = await aiodb.execute("SELECT 처벌로그 FROM 설정")
            설정_result = await aiocursor.fetchone()
            await aiocursor.close()
            if 설정_result:
                경고채널_id = 설정_result[0]
                경고채널 = client.get_channel(경고채널_id)
                if 경고채널:
                    embed = discord.Embed(title="추방", color=embederrorcolor)
                    embed.add_field(name="관리자", value=f"{interaction.author.mention}")
                    embed.add_field(name="대상", value=f"{user.mention}")
                    embed.add_field(name="사유", value=f"{reason}", inline=False)
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message("경고채널을 찾을 수 없습니다.")
                    embed
            else:
                await interaction.response.send_message("경고채널이 설정되지 않았습니다.")
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="차단 [관리자전용]")
@app_commands.rename(user="유저", reason="사유")
async def 차단(interaction, user: discord.Member, reason: str=None):
    if interaction.author.guild_permissions.ban_members:
        try:
            await interaction.guild.ban(user)
        except:
            embed = discord.Embed(title=f"{user.name}를 차단하기엔 권한이 부족해요...", color=embederrorcolor)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            embed = discord.Embed(title="차단", color=embederrorcolor)
            embed.add_field(name="관리자", value=f"{interaction.author.mention}")
            embed.add_field(name="대상", value=f"{user.mention}")
            embed.add_field(name="사유", value=f"{reason}", inline=False)
            await interaction.response.send_message(embed=embed)
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="경고확인")
@app_commands.rename(user="유저")
async def 경고확인(interaction, user: discord.Member = None):
    if user is None:
        user = interaction.author
    dat, accumulatewarn = await getwarn(interaction, user)
    
    if not dat:
        embed = discord.Embed(color=embederrorcolor)
        embed.add_field(name="확인된 경고가 없습니다.", value="")
        await interaction.response.send_message(embed=embed)
    else:
        embed = discord.Embed(title=f"{user.name}님의 경고 리스트", color=embedcolor)
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name=f"누적경고 : {accumulatewarn} / 30", value="", inline=False)
        for i in dat:
            embed.add_field(name=f"경고 #{i[0]}", value=f"경고수: {i[3]}\n사유: {i[4]}", inline=False)
        await interaction.response.send_message(embed=embed)

@tree.command(description="경고지급 [관리자전용]")
async def 경고(interaction, user: discord.Member, warn_num: int = None, reason: str = None):
    if interaction.author.guild_permissions.manage_messages:
        if warn_num is None:
            warn_num = "1"
        if reason is None:
            reason = "없음"
        new_id, accumulatewarn, 설정_result = await addwarn(interaction, user, warn_num, reason)
        if 설정_result:
            경고채널_id = 설정_result[0]
            경고채널 = client.get_channel(경고채널_id)
            if 경고채널:
                embed = discord.Embed(title=f"#{new_id} - 경고", color=embederrorcolor)
                embed.add_field(name="관리자", value=interaction.author.mention, inline=False)
                embed.add_field(name="대상", value=user.mention, inline=False)
                embed.add_field(name="사유", value=reason, inline=False)
                embed.add_field(name="누적 경고", value=f"{accumulatewarn} / 10 (+ {warn_num})", inline=False)
                await 경고채널.send(embed=embed)
            else:
                await interaction.response.send_message("경고채널을 찾을 수 없습니다.")
        else:
            await interaction.response.send_message("경고채널이 설정되지 않았습니다.")
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="경고취소 [관리자전용]")
async def 경고취소(interaction, warn_id: int, reason: str = None):
    if interaction.author.guild_permissions.manage_messages:
        if reason is None:
            reason = "없음"
        warn_id = await removewarn(interaction, warn_id)
        if warn_id is None:
            embed = discord.Embed(color=embederrorcolor)
            embed.add_field(name="이미 취소되었거나 없는 경고입니다.", value="")
            await interaction.response.send_message(embed=embed)
        else:
            await aiocursor.execute("DELETE FROM 경고 WHERE 아이디 = ?", (warn_id,))
            await aiodb.commit()  # 변경 사항을 데이터베이스에 확정합니다.
            embed = discord.Embed(color=embedsuccess)
            embed.add_field(name=f"경고 #{warn_id}(이)가 취소되었습니다.", value="")
            embed.add_field(name="사유", value=reason, inline=False)
            await interaction.response.send_message(embed=embed)
            aiocursor = await aiodb.execute("SELECT 처벌로그 FROM 설정")
            set_result = await aiocursor.fetchone()
            await aiocursor.close()
            if set_result:
                warnlog_id = set_result[0]
                warnlog = client.get_channel(warnlog_id)
                if warnlog:
                    embed = discord.Embed(title=f"#{warn_id} - 경고 취소", color=embedwarning)
                    embed.add_field(name="관리자", value=interaction.author.mention, inline=False)
                    embed.add_field(name="사유", value=reason, inline=False)
                    await warnlog.send(embed=embed)
                else:
                    await interaction.response.send_message("경고채널을 찾을 수 없습니다.")
            else:
                await interaction.response.send_message("경고채널이 설정되지 않았습니다.")
        await aiocursor.close()
    else:
        embed=discord.Embed(color=embederrorcolor)
        embed.add_field(name="❌ 오류", value="관리자만 실행가능한 명령어입니다.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(description="개발자에게 문의하기")
@app_commands.rename(content="내용")
async def 문의(interaction, content: str):
    user = str(f"{interaction.author.display_name}({interaction.author.name})")
    content = f"**아이디** : {interaction.author.id}\n```내용 : {str(content)}```"
    avatar_url = interaction.author.avatar
    economy_aiodb = await aiosqlite.connect("economy.db")
    aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (interaction.author.id,))
    dbdata = await aiocursor.fetchone()
    await aiocursor.close()
    if dbdata is not None:
        if int(dbdata[0]) == 0:
            embed = discord.Embed(color=embederrorcolor)
            embed.add_field(name="❌ 오류", value="이용제한된 유저입니다.\nstone6718 DM으로 문의주세요.")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
    print("문의가 접수되었습니다.")
    embed = discord.Embed(color=embedcolor)
    embed.add_field(name="문의 접수", value=f"{user}, 문의가 접수되었습니다. 감사합니다!\n문의 답변은 DM으로 전송됩니다.")
    await interaction.response.send_message(embed=embed)
    send(user, content, avatar_url, security.webhook)
##################################################################################################
@client.event
async def on_member_join(member):
    # 데이터베이스 연결 및 비동기 커서 생성
    await database_create(member)
    db_path = os.path.join(os.getcwd(), "database", f"{member.guild.id}.db")
    aiodb = await aiosqlite.connect(db_path)
    aiocursor = await aiodb.cursor()  # 비동기 커서 생성
    try:
        # 설정 테이블에서 입장 로그 채널 아이디 가져오기
        await aiocursor.execute("SELECT 입장로그 FROM 설정")
        result = await aiocursor.fetchone()
        if result is not None:
            channel_id = result[0]
            # 채널 아이디에 해당하는 채널에 입장 로그 보내기
            channel = client.get_channel(channel_id)
            if channel is not None:
                embed = discord.Embed(title="입장로그", color=embedcolor)
                embed.add_field(name="유저", value=f"{member.mention} ({member.name})")
                embed.set_thumbnail(url=member.display_avatar.url)
                server_join_date = datetime.datetime.now()
                account_creation_date = member.created_at
                embed.add_field(name="서버입장일", value=server_join_date.strftime("%Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후"), inline=False)
                embed.add_field(name="계정생성일", value=account_creation_date.strftime("%Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후"), inline=False)
                await channel.send(embed=embed)
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
    await aiocursor.close()
    await aiodb.close()

@client.event
async def on_member_remove(member):
    # 데이터베이스 연결 및 비동기 커서 생성
    await database_create(member)
    db_path = os.path.join(os.getcwd(), "database", f"{member.guild.id}.db")
    aiodb = await aiosqlite.connect(db_path)
    aiocursor = await aiodb.cursor()  # 비동기 커서 생성
    try:
        await aiocursor.execute("SELECT 퇴장로그 FROM 설정")
        result = await aiocursor.fetchone()
        if result is not None:
            channel_id = result[0]
            channel = client.get_channel(channel_id)
            if channel is not None:
                embedcolor = 0x00FF00  # 임베드 색상 설정
                embed = discord.Embed(title="퇴장로그", color=embedcolor)
                embed.add_field(name="유저", value=f"{member.mention} ({member.name})")
                server_remove_date = datetime.datetime.now()
                embed.add_field(name="서버퇴장일", value=server_remove_date.strftime("%Y년 %m월 %d일 %p %I:%M").replace("AM", "오전").replace("PM", "오후"), inline=False)
                await channel.send(embed=embed)
    finally:
        # 데이터베이스 연결 종료
        await aiocursor.close()
        await aiodb.close()

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if isinstance(message.channel, discord.DMChannel):
        user = str(f"{message.author.display_name}({message.author.name})")
        user_message = f"**아이디** : {message.author.id}\n```내용 : {str(message.content)}```"
        avatar_url = message.author.avatar
        economy_aiodb = await aiosqlite.connect("economy.db")
        aiocursor = await economy_aiodb.execute("SELECT tos FROM user WHERE id=?", (message.author.id,))
        dbdata = await aiocursor.fetchone()
        await aiocursor.close()
        if dbdata is not None:
            if int(dbdata[0]) == 0:
                embed = discord.Embed(color=embederrorcolor)
                embed.add_field(name="❌ 오류", value="이용제한된 유저입니다.\nstone6718 DM으로 문의주세요.")
                await message.channel.send(embed=embed, ephemeral=True)
                return
        embed = discord.Embed(color=embedcolor)
        embed.add_field(name="문의 접수", value=f"{user}, 문의가 접수되었습니다. 감사합니다!")
        await message.channel.send(embed=embed)
        print("문의가 접수되었습니다.")
        send(user, user_message, avatar_url, security.webhook)

@client.event
async def on_ready():
    print("\n봇 온라인!")
    print(f'{client.user.name}')
    try:
        await tree.sync()
    except Exception as e:
        print(e)
##################################################################################################
    @tasks.loop(seconds=3)
    async def change_status():
        guild_len = len(client.guilds)
        status = [f'사람들과 도박', '편리한 기능을 제공', f'{guild_len}개의 서버를 관리']
        for i in status:
            await asyncio.sleep(3)
            await client.change_presence(status=discord.Status.online, activity=discord.Game(i))

    change_status.start()
    aiodb = None

    @tasks.loop(seconds=60)
    async def periodic_price_update():
        await update_stock_prices()
        print("주식가격이 변동됨")

    periodic_price_update.start()

async def startup():
    await client.start(token, reconnect=True)
    global aiodb
    aiodb = {}
    for guild in client.guilds:
        db_path = os.path.join(os.getcwd(), "database", f"{guild.id}.db")
        aiodb[guild.id] = await aiosqlite.connect(db_path)
    global economy_aiodb
    if economy_aiodb is None:
        economy_aiodb = await aiosqlite.connect("economy.db")

async def shutdown():
    for aiodb_instance in aiodb.values():
        await aiodb_instance.close()
    await aiodb.close()
try:
    asyncio.run(startup())
except KeyboardInterrupt:
    (asyncio.get_event_loop()).run_until_complete(shutdown())