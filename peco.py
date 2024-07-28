import discord
import sqlite3
import asyncio
import datetime
import random
from discord import ui
from discord.ui import View
import emoji
import os


#本番用
TOKEN = os.getenv('TOKEN')


before_time = 0
#本番用
conn=sqlite3.connect("./level.db", check_same_thread=False)


c=conn.cursor()
data=c.fetchone()

message_before = ""
message_cnt = 0


intents=discord.Intents.all()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

#prefix="?"
#intents=discord.Intents.all()
#bot=commands.Bot(command_prefix=prefix,intents=intents)

c.execute("CREATE TABLE IF NOT EXISTS level(userid int primary key,username,level,exp,before_word,after_word,cnt,new_comer,black_list,date_join)")

#ロールnameからロールidの検索
async def search_role(lst_role,role_name):
    for role in lst_role:
        if role.name == role_name:
            return role.id
        
#Limitedロールの付与
async def limited_role_adds(member,role_id):
    #limitedロール
    role_limited = member.guild.get_role(role_id)
    #memberロール
    role_rev = member.guild.get_role(111111111111111)
    try:
        await member.remove_roles(role_rev)
    except Exception as e:
        print(e)
        pass
    
    await member.add_roles(role_limited)
    
#お祝いメッセージ送信
def congrats(name,role_name):
    return name + "さん" + "@" + role_name + "の獲得おめでとうございます"

#ロール付与
async def role_adds(member,role_id):
    role = member.guild.get_role(role_id)
    if member.get_role(role_id) == role:
        return None
    else:
        await member.add_roles(role)
        return member

#level判定してロール付与する処理
async def check_level(member,val,lst_role):
    mem = None
    role_name = ""

    #joinロール付与
    if val >= 5:
        role_name = "join"
        role_id = await search_role(lst_role,role_name)
        #await message.channel.send(str(member) + str(role_id))
        mem = await role_adds(member,role_id)
        
    #friendlyロール付与
    if val >= 15:
        role_name = "friendly"
        role_id = await search_role(lst_role,role_name)
        mem = await role_adds(member,role_id)

    #talkativeロール付与
    if val >= 25:
        role_name = "talkative"
        role_id = await search_role(lst_role,role_name)
        mem = await role_adds(member,role_id)
        
        
    return (mem,role_name)

#@bot.event
@client.event
async def on_ready():
    print("起動")
    await client.change_presence(activity=discord.Game(name="XXXXXX"))
    await tree.sync()


#@bot.listen("on_message")
@client.event
async def on_message(message):
    global all_emojis
    url = ""

    if message.author.bot:
        return

    c.execute("SELECT * FROM level WHERE userid=?", (message.author.id,))
    
    data=c.fetchone()


    if data is None:
        try:
            month_join = '-'.join(str(datetime.datetime.now()).split()[0].split('-')[:2])
            c.execute("INSERT INTO level VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",(message.author.id,message.author.name, 1, 0, "", "", 0,"", 0, month_join))
            conn.commit()
        except:
            pass

        return
    if message.content == "":
        return
    
    #levelUP通知をするチャンネル
    botRoom = client.get_channel(44444444444444444)
        
    #投稿したものが画像かどうかの判定
    try:
        url = message.attachments[0].url
    except:
        pass
        

    c.execute("UPDATE level set before_word=? WHERE userid =?", (message.content, message.author.id,))
    conn.commit()

    c.execute("SELECT before_word FROM level WHERE userid =?", (message.author.id,))
    before_msg = c.fetchone()[0]

    c.execute("SELECT after_word FROM level WHERE userid =?", (message.author.id,))
    after_msg = c.fetchone()[0]

    if after_msg == None:
        after_msg = ""
    
    
    if ((("https://discord.gg" in message.content))):
        await message.delete()
    
    if (message.content != "/bump") and (url == ""):
        if (message.mention_everyone and (message.content.count("@everyone") >= 2 or (message.content.count("@here") >= 2))):
            #メッセージの削除
            await message.delete()
            #発言の制限を実施する
            await message.channel.send("あなたは荒らし")
            #発言をさせないようにロールを付与する(@Limited)
            await limited_role_adds(message.author,6666666666666666666)
            #カウントを初期化
            c.execute("UPDATE level set cnt=0 WHERE userid =?", (message.author.id,))
            conn.commit()
        
        if before_msg == after_msg:
            c.execute("UPDATE level set cnt=cnt+1 WHERE userid =?", (message.author.id,))
            conn.commit()
            c.execute("SELECT cnt FROM level WHERE userid =?", (message.author.id,))
            cnt = c.fetchone()[0]

            if cnt >= 3:
                try:
                    #発言の制限を実施する
                    await message.channel.send("あなたは荒らし")
                except:
                    pass
                #発言をさせないようにロールを付与する(@Limited)
                await limited_role_adds(message.author,6666666666666666666)
                #カウントを初期化     
                c.execute("UPDATE level set cnt=0 WHERE userid =?",(message.author.id,))
                conn.commit()

        elif before_msg != after_msg:
            c.execute("UPDATE level set cnt=0 WHERE userid =?", (message.author.id,))
            conn.commit()
    

    #before_msg = message.content
    after_msg = before_msg

    #after_wordの格納
    c.execute("UPDATE level set after_word=? WHERE userid =?", (after_msg, message.author.id))
    conn.commit()

    #ブラックリストに含まれる場合は除外
    if data[8] == 1:
        return

    try:
        c.execute("UPDATE level set exp=? WHERE userid=?",(data[3]+1.5, message.author.id))
        conn.commit()
    except:
        pass
    c.execute("SELECT * FROM level WHERE userid=?", (message.author.id,))
    data=c.fetchone()
    if data[3] >= data[2]*5:
        c.execute("UPDATE level set level=?,exp=? WHERE userid=?",(data[2]+1,0,message.author.id))
        conn.commit()
        await botRoom.send(message.author.name + "さん!" + str(data[2]+1) + "レベルに" + "アップしました")
        
        guild = message.guild
        lst_role = guild.roles
        member = await guild.fetch_member(message.author.id)
        
        mem = await check_level(member,data[2]+1,lst_role)
        
        if mem[0] is None:
            pass
        else:
            await botRoom.send(congrats(message.author.name,mem[1]))


@tree.command(
    name="islolate",
    description="特定のメンバーを隔離します(ユーザIDで制限)"
)
@discord.app_commands.describe(
    userid="@ユーザ"
)
async def isolate(mem:discord.Interaction,userid:str):
    #await mem.response.send_message(f"Hello, {user}!")


    #memberロールの取得
    mem_role = discord.utils.get(mem.guild.roles, name="member")
    
    #Limitedロールの取得
    lmt_role = discord.utils.get(mem.guild.roles, name="Limited")


    #memberロールのはく奪
    try:
        mem1 = mem.guild.get_member(int(userid))
        await mem1.remove_roles(mem_role)
    except Exception as e:
        print(e)
        await mem.response.send_message(content="そのようなユーザはいませんよ",ephemeral = True)
        return


    #Limitedロールの付与
    try:
        await mem1.add_roles(lmt_role)
    except Exception as e:
        print(e)
        await mem.response.send_message(content="システム上で不具合が起こっています",ephemeral = True)
        return


    #memberをVCから切断する処理↓
    try:
        await mem1.move_to(None)
        await mem.response.send_message(content="隔離措置を施しました！",ephemeral = True)
    except Exception as e:
        print(e)
        await mem.response.send_message(content="隔離措置を施しました！",ephemeral = True)
        return

@tree.command(
    name="backup",
    description="サーバのバックアップを取ります"
)
@discord.app_commands.default_permissions(
    administrator = True
)
async def backup(interaction:discord.Interaction):
    global gldid
    gldid=0
    gldid=interaction.guild.id
    select = HugaListServ()
    view = View(timeout=180)
    view.add_item(select)
    await interaction.response.send_message("バックアップ先のサーバを選んでください",view=view,ephemeral=True)

class HugaListServ(discord.ui.Select):
    def __init__(self):
        global options
        global gldid
        options={}
        optionobj=[]
        for gld in client.guilds:
            if gld.id == gldid:
                pass
            else:
                #セレクトメニューに使うオブジェクト
                optionobj.append(discord.SelectOption(label=gld.name))
                options[gld.name]=gld
        
        #選択先のサーバがない場合は終了
        if len(options)==0:
            return
        
        super().__init__(min_values=1, max_values=1, options=optionobj)

    async def callback(self, interaction: discord.Interaction):
        global options
        bckgld=interaction.guild
        await interaction.response.send_message(content="バックアップ中...",ephemeral=True)


        #ロール作成
        for gld in list(options.values()):
            try:
                if gld.name == self.values[0]:
                    for role in reversed(bckgld.roles):
                        await gld.create_role(name=role.name,permissions=role.permissions,colour=role.colour,hoist=True,mentionable=True)
            except Exception as e:
                print(e)
                return
            
        await interaction.followup.send("バックアップ中...",ephemeral=True)

        #チャンネル作成
        for gld in list(options.values()):
            try:
                if gld.name == self.values[0]:
                    #チャンネルの全カテゴリ取得とバックアップ先サーバにカテゴリ作成
                    categories={}
                    for cate in bckgld.categories:
                        await gld.create_category(cate.name)
                    
                    for cate in gld.categories:
                        categories[cate.name]=cate.id

                    #print("bckgld.channels:",bckgld.channels)
                    #print("bckgld.len:",len(bckgld.channels))
                    
                    for cate in bckgld.categories:
                        try:
                            if cate.name in list(categories.keys()):
                                for chnl in cate.channels:
                                    gldcate = gld.get_channel(categories[chnl.category.name])
                                    if str(chnl.type) == "text":
                                        #print(chnl.name)
                                        await gldcate.create_text_channel(name=chnl.name,overwrites=chnl.overwrites,topic=chnl.topic)
                                    if str(chnl.type) == "voice":
                                        #print(chnl.name)
                                        await gldcate.create_voice_channel(name=chnl.name,overwrites=chnl.overwrites)
                                    if str(chnl.type) == "stage_voice":
                                        #print(chnl.name)
                                        await gldcate.create_stage_channel(name=chnl.name,overwrites=chnl.overwrites)


                        except Exception as e:
                            pass
                            print(e)

            except Exception as e:
                print(e)
                return

        await interaction.followup.send("バックアップ完了しました",ephemeral=True)
        return


#@bot.command()
@tree.command(
    name="level",#コマンド名
    description="あなたのレベルを確認出来ますよ"#コマンドの説明
)
async def level(interaction: discord.Interaction):
    user=interaction.user
    c.execute("SELECT * FROM level WHERE userid=?", (user.id,))
    data=c.fetchone()
    if data is None:
        await interaction.response.send_message("まだないので、経験値稼いでくださいね",ephemeral=True)

    embed = discord.Embed(title=f"{user}のランク",description = f"Lv.{data[2]}")
    embed.add_field(name="次のレベルまで",value=str(int(data[2]*5) - data[3]) + "経験値ですよ")
    await interaction.response.send_message(embed=embed,ephemeral=True)


#blacklist登録
#@bot.command()
@tree.command(
    name="blacklist",#コマンド名
    description="ブラックリスト登録(管理者のみ)"#コマンドの説明
)
@discord.app_commands.describe(
    userid="blacklistの後ろにユーザIDを指定ください" # 引数名=説明
)
@discord.app_commands.default_permissions(
    administrator=True
)
async def blacklist(interaction: discord.Interaction,userid: str):
    if interaction.user.guild_permissions.administrator:
        try:
            c.execute("SELECT * FROM level WHERE userid=?", (int(userid),))
            data=c.fetchone()
        except:
            await interaction.response.send_message("ユーザIDは数値です",ephemeral=True)
            return

        if data is None:
            await interaction.response.send_message("そのユーザIDを持つ人はいませんね....",ephemeral=True)
            return
        
        if data[8] == 1:
            await interaction.response.send_message("その人は既にブラックリストに登録されてますね",ephemeral=True)
            return
        else:
            try:
                c.execute("UPDATE level set black_list=? WHERE userid=?",(1,int(userid)))
                conn.commit()
                await interaction.response.send_message("ブラックリストに登録しました",ephemeral=True)
            except:
                await interaction.response.send_message("間違いがあります",ephemeral=True)

    else:
        await interaction.response.send_message("この操作は管理人のみが行えます",ephemeral=True)
        
#blacklist解除
#@bot.command()
@tree.command(
    name="unlock",#コマンド名
    description="ブラックリスト解除(管理者のみ)"#コマンドの説明
)
@discord.app_commands.describe(
    userid="unlockの後ろにユーザIDを指定ください" # 引数名=説明
)
@discord.app_commands.default_permissions(
    administrator=True
)
async def unlock(interaction: discord.Interaction,userid: str):
    if interaction.user.guild_permissions.administrator:
        try:
            c.execute("SELECT * FROM level WHERE userid=?", (int(userid),))
            data=c.fetchone()
        except:
            await interaction.response.send_message("ユーザIDは数値ですよ",ephemeral=True)
            return

        if data is None:
            await interaction.response.send_message("そのユーザIDを持つ人はいませんね....",ephemeral=True)
            return
        
        if data[8] == 0:
            await interaction.response.send_message("その人は元からホワイトです",ephemeral=True)
            return

        else:
            try:
                c.execute("UPDATE level set black_list=? WHERE userid=?",(0,int(userid)))
                conn.commit()
                await interaction.response.send_message("ブラックリストから削除しました",ephemeral=True)
            except:
                await interaction.response.send_message("間違いがあります",ephemeral=True)

    else:
        await interaction.response.send_message("この操作は管理人のみが行えます",ephemeral=True)
        
#@client.command()
@tree.command(
    name="board",#コマンド名
    description="上位20名のレベルを閲覧する"#コマンドの説明
)
async def board(interaction: discord.Interaction):
    #user=ctx.author
    c.execute("SELECT username,level,exp FROM level ORDER BY level DESC,exp DESC LIMIT 20")
    
    embed = discord.Embed(title="メンバーのLv(上位20人のみ表示)",color=0x00ff00,description="名前(name),Level,exp")
    #テスト用
    #embed = discord.Embed(title="メンバーのLv",color=0x00ff00,description=c.fetchall())

    for i in c.fetchall():
        s = str(list(i)[0]) + ',' + str(list(i)[1]) + ',' + str(list(i)[2])
        embed.add_field(name='-------------------------',value = s, inline=False)
 
    await interaction.response.send_message(embed=embed,ephemeral=True)



#管理者権限を持ったユーザのみレベルの変更が出来る
#@client.command()
@tree.command(
    name="change_level",#コマンド名
    description="レベルの変更(管理者のみ)"#コマンドの説明
)
@discord.app_commands.describe(
    userid="useridを入力してください" # 引数名=説明
)
@discord.app_commands.describe(
    level="レベルを設定ください" # 引数名=説明
)
@discord.app_commands.default_permissions(
    administrator=True
)
async def change_level(interaction: discord.Interaction,userid: str,level: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("管理人以外は操作できませんよ",ephemeral=True)
        return
    try:
        id = int(userid)
        c.execute("SELECT * FROM level WHERE userid=?", (id,))
        data=c.fetchone()
    except:
        await interaction.response.send_message("ユーザIDは数値です",ephemeral=True)
        return

    if data is None:
        await interaction.response.send_message("そのユーザIDを持つ人はいませんね....",ephemeral=True)
        return

    try:
        level = int(level)
    except:
        await interaction.response.send_message("レベルは数値ですよ",ephemeral=True)
        return

    if level >= 1:
        await interaction.response.send_message("レベルを" + str(level) + "に設定しました",ephemeral=True)
        lst_role = interaction.guild.roles
        roles = []
        c.execute("UPDATE level set level=?,exp=? WHERE userid=?",(level,0,id))
        conn.commit()
        #idからmember型のメンバーを取得し，check_levelメソッドを呼ぶ
        member = await interaction.guild.fetch_member(id)
        #mem:member, name:ロールの名前．レベルに相応のロールを付与する
        mem,name = await check_level(member,level,lst_role)

        if name == "":
            name = "member"

        for role in member.roles:
           roles.append(role.name)

        #レベルよりも高位のロールをつけている場合はロールをはく奪する
        try:
            for role in roles[roles.index(name) + 1:]:
                role_id = await search_role(lst_role,role)
                role_rev = member.guild.get_role(role_id)
                await member.remove_roles(role_rev)
        except Exception as e:
            #print(e)
            pass

    elif level < 1:
        await interaction.response.send_message("レベルは1以上ですよ",ephemeral=True)


client.run(TOKEN)
#bot.run(TOKEN) #ボットのトークン
