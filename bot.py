import discord
from discord.ext import commands
import asyncio
import json
import random
import time 
import datetime
from collections import defaultdict
import threading
from dotenv import load_dotenv
import os

load_dotenv()

Token = os.getenv("DISCORD_TOKEN")


OWNER_ID = 1064709921171582986
GUILD_ID = 1463735755783540736
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 공부 데이터
current_study = {}

# 안티치트
message_log = defaultdict(list)
warnings = {}
print(Token)
MAX_WARNINGS = 10

bad_words = [
]
def load_warnings():
    try:
        with open("warnings.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_warnings(data):
    with open("warnings.json", "w") as f:
        json.dump(data, f, indent=4)

warnings = load_warnings()


@bot.event
async def on_ready():

    print(f"{bot.user} 준비 완료!")

    guild = bot.get_guild(GUILD_ID)

    try:
        member = await guild.fetch_member(OWNER_ID)

        print(member)

        await member.timeout(None)

        print("타임아웃 해제 완료")

    except Exception as e:
        print("오류:", repr(e))



@bot.event
async def on_message(message):

    if message.author.bot:
        return

    user_id = str(message.author.id)

    # ==================
    # 금지어 감지
    # ==================

    for word in bad_words:

        if word.lower() in message.content.lower():

            try:
                await message.delete()
            except:
                pass

            warnings[user_id] = warnings.get(user_id, 0) + 2

            warn = warnings[user_id]

            await message.channel.send(
                f"🚫 {message.author.mention} 금지어 감지! 벌점 {warn}/{MAX_WARNINGS}"
            )

            if warn >= MAX_WARNINGS:

                try:
                    await message.author.timeout(
                        datetime.timedelta(minutes=10),
                        reason="벌점 누적"
                    )

                    await message.channel.send(
                        f"🔨 {message.author.mention} 10분 타임아웃!"
                    )

                    warnings[user_id] = 0

                except Exception as e:
                    print(e)

            return

    # ==================
    # 도배 감지
    # ==================

    now = time.time()

    message_log[user_id].append(now)

    message_log[user_id] = [
        t for t in message_log[user_id]
        if now - t < 5
    ]

    if len(message_log[user_id]) >= 5:

        warnings[user_id] = warnings.get(user_id, 0) + 1

        warn = warnings[user_id]

        await message.channel.send(
            f"⚠ {message.author.mention} 도배 감지! 벌점 {warn}/{MAX_WARNINGS}"
        )

        message_log[user_id] = []

        if warn >= MAX_WARNINGS:

            try:
                await message.author.timeout(
                    datetime.timedelta(minutes=10),
                    reason="도배 벌점 누적"
                )

                await message.channel.send(
                    f"🔨 {message.author.mention} 10분 타임아웃!"
                )

                warnings[user_id] = 0

            except Exception as e:
                print(e)

    await bot.process_commands(message)



@bot.command()
async def 타임아웃(ctx, member: discord.Member, 분: int):

    if ctx.author.id != OWNER_ID:
        await ctx.send("권한이 없습니다!")
        return

    if 분 <= 0:
        await ctx.send("시간은 1분 이상이어야 합니다!")
        return

    try:
        await member.timeout(
            datetime.timedelta(minutes=분),
            reason=f"{ctx.author}에 의해 타임아웃"
        )

        await ctx.send(
            f"🔨 {member.mention}님을 {분}분 동안 타임아웃했습니다!"
        )

    except Exception as e:
        await ctx.send(f"오류 발생: {e}")

@bot.command()
async def 탐해제(ctx, member: discord.Member,):

    if ctx.author.id != OWNER_ID:
        await ctx.send("권한이 없습니다!")
        return
    
    try:
        await member.timeout(None)


        await ctx.send(
            f"✅ {member.mention}의 타임아웃을 해제했습니다!"
        )
    except  Exception as e:
        await ctx.send(
            f"❌ 오류발생! : {e}"
        )






@bot.command()
async def 벌점(ctx, member: discord.Member, 점수: int):

    if ctx.author.id != 1064709921171582986:
        await ctx.send("⛔ 이 명령어는 사용할 수 없습니다.")
        return

    user_id = str(member.id)

    warnings[user_id] = warnings.get(user_id, 0) + 점수

    warn = warnings[user_id]

    await ctx.send(
        f"⚠ {member.mention}에게 벌점 {점수}점 부여!\n"
        f"현재 벌점: {warn}/{MAX_WARNINGS}"
    )

    if warn >= MAX_WARNINGS:

        try:
            import datetime

            await member.timeout(
                datetime.timedelta(minutes=10),
                reason="벌점 누적"
            )

            await ctx.send(
                f"🔨 {member.mention} 10분 타임아웃!"
            )

            warnings[user_id] = 0

        except Exception as e:
            print(e)


@bot.command()
async def 공부시간(ctx):

    try:
        with open("study.json", "r") as f:
            data = json.load(f)

    except:
        await ctx.send("공부 데이터가 없습니다!")
        return

    sorted_data = sorted(
        data.items(),
        key=lambda x: x[1],
        reverse=True
    )

    top10 = sorted_data[:10]

    message = "공부시간 리더보드지롱~😎\n\n"

    for i, (user_id, study_time) in enumerate(top10, start=1):

        user = await bot.fetch_user(int(user_id))

        message += f"{i}위 {user.name} - {study_time}분\n"

    await ctx.send(message)


@bot.command()
async def 휴식(ctx):

    user_id = str(ctx.author.id)

    if user_id not in current_study:
        await ctx.send("현재 공부중이 아닙니다!")
        return

    분 = current_study[user_id]

    try:
        with open("study.json", "r") as f:
            data = json.load(f)

    except:
        data = {}

    if user_id not in data:
        data[user_id] = 0

    data[user_id] += 분

    with open("study.json", "w") as f:
        json.dump(data, f, indent=4)

    del current_study[user_id]

    await ctx.send(
        f"{ctx.author.mention} 공부 저장 완료! 푹 쉬세요 😎"
    )


@bot.command()
async def 공부시작(ctx, 분: int):

    if 분 <= 0:
        await ctx.send("음수는 안돼요!")
        return

    if 분 > 300:
        await ctx.send(
            "너무 무리하지 마시고 쉬면서 하세요!"
        )
        return

    user_id = str(ctx.author.id)

    if user_id in current_study:
        await ctx.send("이미 공부중입니다!")
        return

    current_study[user_id] = 분

    await ctx.send(f"{분}분 공부 시작!")

    await asyncio.sleep(분 * 60)

    try:
        with open("study.json", "r") as f:
            data = json.load(f)

    except:
        data = {}

    if user_id not in data:
        data[user_id] = 0

    data[user_id] += 분

    with open("study.json", "w") as f:
        json.dump(data, f, indent=4)

    if user_id in current_study:
        del current_study[user_id]

    await ctx.send(
        f"{ctx.author.mention} 공부 끝! 수고했어요😁"
    )


@bot.command()
async def 벌점확인(ctx, member: discord.Member):

    user_id = str(member.id)

    warn = warnings.get(user_id, 0)

    await ctx.send(
        f"📋 {member.display_name}의 벌점 : {warn}/{MAX_WARNINGS}"
    )


@bot.command()
async def 벌점초기화(ctx, member: discord.Member):

    if ctx.author.id != 1064709921171582986:
        await ctx.send("⛔ 권한이 없습니다.")
        return

    warnings[str(member.id)] = 0

    await ctx.send(
        f"✅ {member.mention}의 벌점을 초기화했습니다."
    )


@bot.command()
async def 벌점랭킹(ctx):

    ranking = sorted(
        warnings.items(),
        key=lambda x: x[1],
        reverse=True
    )

    if len(ranking) == 0:
        await ctx.send("벌점 데이터가 없습니다!")
        return

    msg = "🚨 벌점 랭킹 🚨\n\n"

    for i, (user_id, score) in enumerate(ranking[:10], start=1):

        try:
            user = await bot.fetch_user(int(user_id))
            msg += f"{i}위 {user.name} - {score}점\n"
        except:
            pass

    await ctx.send(msg)

@bot.command()
async def 명령어(ctx):
    await ctx.send("명령어들입니다!\n"
    "일반 명령어✅ : !공부시작 (분), !공부시간, !휴식, !벌점확인 @사람, !벌점랭킹 들이 있습니다!\n" 
    "개발자 명령어🛡️ : !벌점 @사람, !벌점초기화, !타임아웃, !탐해제 들이 있습니다!")


print(Token)
bot.run(Token)