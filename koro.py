import discord
import os
import asyncio
import datetime
import glob
import random
import sqlite3
import requests
import aiohttp
from pprint import pprint
from discord.ext import commands
import datetime
import matplotlib.pyplot as plt
from discord.ext import tasks



TOKEN = os.getenv('TOKEN')
#prefix="."
intents=discord.Intents.all()
client=discord.Client(intents = intents)
tree = discord.app_commands.CommandTree(client)

#レベルDB
conn=sqlite3.connect("level.db", check_same_thread=False)
c=conn.cursor()

channel_sent=""

class HogeButton(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HugaButton("PUSH"))

class HugaButton(discord.ui.Button):
    def __init__(self,txt:str):
        super().__init__(label=txt,style=discord.ButtonStyle.green)

    async def callback(self, interaction: discord.Interaction):
        #memberロールの付与(本番用)
        await interaction.user.add_roles(interaction.guild.get_role(11111111111111111))
        await interaction.channel.delete()
        #c.execute("UPDATE level SET new_comer='' WHERE userid=?",(interaction.user.id,))
        #new_comer_chを消す
        c.execute("UPDATE level SET new_comer=? WHERE userid=?",('',interaction.user.id))
        conn.commit()
        

@client.event
async def on_ready():
    global channel_sent
    #Hogewarts
    channel_sent = client.get_channel(222222222222222222)
    print("起動")
    await client.change_presence(activity=discord.Game("X")) #～をプレイ中
    await tree.sync()
    dbsend.start() #定期実行するメソッドの後ろに.start()をつける


@tasks.loop(minutes=30)
async def dbsend():
    global channel_sent
    await channel_sent.send(file=discord.File("./level.db"))

@client.event
async def on_member_join(member):
    #print("test")
    if member.bot:
        return
    
    guild = member.guild
    month_join = '-'.join(str(datetime.datetime.now()).split()[0].split('-')[:2])
    if conn is None:
        c.execute("INSERT INTO statistics VALUES(?, ?, ?)",(member.id,member.name,month_join))
        conn.commit()
    #権限の編集
    permission = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
            member: discord.PermissionOverwrite(read_messages=True),
    }
    
    #チャンネルを作成するカテゴリのIDを取得する(本番用)
    category = guild.get_channel(333333333333333333333)
    
    #カテゴリ内に指定した名前でチャンネルを作成する
    ch = await category.create_text_channel(name=member.name + "ようこそ",overwrites=permission)
    #DBの中身にjoin_chを挿入する
    c.execute("UPDATE level SET new_comer=? WHERE userid=?",(str(ch.id),member.id))
    conn.commit()
    
    await ch.send("下のボタンを押してください。", view=HogeButton())

@client.event
async def on_member_remove(member):       
    if member.bot:
        return
    guild = member.guild
    
    
    #本番用
    channel = await guild.fetch_channel(4444444444444444444444)
    await channel.send(member.name + "が" + "抜けました")
    
    
    #認証チャンネルをそのままにした状態で即抜けした人のチャンネルを削除
    #try:
    c.execute("SELECT new_comer from level WHERE userid=?", (member.id,))
    #print(c.fetchone()[0])
    data = c.fetchone()[0]
    try:
        await guild.get_channel(int(data)).delete()
    except Exception as e:
        print(e)
        pass

    c.execute("DELETE FROM level WHERE userid=?", (member.id,))
    conn.commit()


@tree.command(
    name="statistics",
    description="メンバー流入状況を可視化"
)
async def statistics(interaction:discord.Interaction):
    c.execute('SELECT date_join,count(date_join) FROM level WHERE date_join <> "" GROUP BY date_join HAVING count(date_join)>=1')
    data_c=list(c.fetchall())
    #print(data_c)
    data_date = []
    data_member = []
    for data in data_c:
        data_date.append(data[0])
        data_member.append(data[1])

    figure, ax = plt.subplots() #グラフの定義
    ax.plot(data_date,data_member)
    plt.title("Member_Flow")
    plt.xlabel("Date")
    plt.ylabel("Number Of Member")
    figure.savefig('./test.jpg')

    embed = discord.Embed(title="メンバーの流入状況") # まずは普通にEmbedを定義
    fname="test.jpg " # アップロードするときのファイル名 自由に決めて良いですが、拡張子を忘れないように
    file = discord.File(fp="./test.jpg",filename=fname,spoiler=False) # ローカル画像からFileオブジェクトを作成
    embed.set_image(url=f"attachment://{fname}") # embedに画像を埋め込むときのURLはattachment://ファイル名
    await interaction.response.send_message(file=file, embed=embed,ephemeral=True) # ファイルとembedを両方添えて送信する
    
client.run(TOKEN) #ボットのトークン
