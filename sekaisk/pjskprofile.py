import time
import ujson as json
import os
import io
import requests
from .api_client import ApiClient
from nonebot.log import logger
from PIL import Image, ImageFont, ImageDraw, ImageFilter

#基于Unibot修改 https://github.com/watagashi-uni/Unibot by watagashi_uni
class userprofile(object):

    def __init__(self):
        self.name = ''
        self.rank = 0
        self.userid = ''
        self.twitterId = ''
        self.word = ''
        self.userDecks = [0, 0, 0, 0, 0]
        self.special_training = [False, False, False, False, False]
        self.full_perfect = [0, 0, 0, 0, 0, 0]
        self.full_combo = [0, 0, 0, 0, 0, 0]
        self.clear = [0, 0, 0, 0, 0, 0]
        self.mvpCount = 0
        self.superStarCount = 0
        self.userProfileHonors = {}
        self.userHonorMissions = []
        self.characterRank = {}
        self.characterId = 0
        self.highScore = 0
        self.masterscore = {}
        self.expertscore = {}
        self.appendscore = {}
        self.musicResult = {}
        for i in range(25, 38):
            self.masterscore[i] = [0, 0, 0, 0]
        for i in range(21, 32):
            self.expertscore[i] = [0, 0, 0, 0]
        for i in range(23, 39):
            self.appendscore[i] = [0, 0, 0, 0]

    def getprofile(self, userid , data=None, is_force_update=False):
        client = ApiClient(userid)
   
        if data is None:
            data = client.call_infoapi(f'/user/{userid}/profile',is_force_update=is_force_update)
 
            # if data:
            #     logger.debug(f"success get infodata")
        self.twitterId = data.get('userProfile', {}).get('twitterId', "")
        self.userid = userid
        self.word = data.get('userProfile', {}).get('word', "")

        try:
            self.characterId = data['userChallengeLiveSoloResult']['characterId']
            self.highScore = data['userChallengeLiveSoloResult']['highScore']
        except:
            pass

        self.characterRank = data.get('userCharacters')
        self.userProfileHonors = data.get('userProfileHonors')
        self.userHonorMissions = data.get('userHonorMissions', [])
        self.name = data['user']['name']
        self.rank = data['user']['rank']
        count_data = data['userMusicDifficultyClearCount']
        self.full_perfect = [count_data[i].get('allPerfect', 'no data') if i < len(count_data) else 0 for i in range(6)]
        self.full_combo = [count_data[i]['fullCombo'] if i < len(count_data) else 0 for i in range(6)]
        self.clear = [count_data[i]['liveClear'] if i < len(count_data) else 0 for i in range(6)]
        self.mvpCount = data['userMultiLiveTopScoreCount']['mvp']
        self.superStarCount = data['userMultiLiveTopScoreCount']['superStar']
       
        for i in range(0, 5):
            self.userDecks[i] = data['userDeck'][f'member{i + 1}']
    
            for userCards in data['userCards']:
                if userCards['cardId'] != self.userDecks[i]:
                    continue
                if userCards['defaultImage'] == "special_training":
                    self.special_training[i] = True


def pjskprofile(userid, private=None, is_force_update=False, group_id=None):
    profile = userprofile()
    profile.getprofile(userid, is_force_update=is_force_update)
    if private == 0:
       id = userid
    else:
        id = "Private"
    img = Image.open('pics/pjskprofile_new.png')
    # if img:
    #   logger.debug("success open progfile img")

    with open('./twmasterdata/cards.json', 'r', encoding='utf-8') as f:
        cards = json.load(f)
    # if cards:
    #   logger.debug("success open progfile cards")
    try:
        assetbundleName = ''
        for i in cards:
            if i['id'] == profile.userDecks[0]:
                assetbundleName = i['assetbundleName']
            # logger.debug(f"{profile.special_training}")
        if profile.special_training[0]:
            cardimg = Image.open('./data/assets/sekai/assetbundle/resources'
                                 f'/startapp/thumbnail/chara/{assetbundleName}_after_training.png')
        else:
            cardimg = Image.open('./data/assets/sekai/assetbundle/resources'
                                 f'/startapp/thumbnail/chara/{assetbundleName}_normal.png')
        cardimg = cardimg.resize((151, 151))
        r, g, b, mask = cardimg.split()
        img.paste(cardimg, (118, 51), mask)
    except FileNotFoundError:
        pass

    draw = ImageDraw.Draw(img)
    font_style = ImageFont.truetype("./data/HarmonyOS_Sans_SC_Medium.ttf", 45)
    draw.text((295, 45), profile.name, fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("./data/FOT-RodinNTLGPro-DB.ttf", 20)
    draw.text((298, 116), 'id:' + str(id), fill=(0, 0, 0), font=font_style)
    font_style = ImageFont.truetype("./data/FOT-RodinNTLGPro-DB.ttf", 34)
    draw.text((415, 157), str(profile.rank), fill=(255, 255, 255), font=font_style)
    font_style = ImageFont.truetype("./data/FOT-RodinNTLGPro-DB.ttf", 22)
    draw.text((182, 318), str(profile.twitterId), fill=(0, 0, 0), font=font_style)

    font_style = ImageFont.truetype("./data/HarmonyOS_Sans_SC_Medium.ttf", 24)
    bbox = font_style.getbbox(profile.word)
    size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
    if size[0] > 480:
        draw.text((132, 388), profile.word[:int(len(profile.word) * (460 / size[0]))], fill=(0, 0, 0), font=font_style)
        draw.text((132, 424), profile.word[int(len(profile.word) * (460 / size[0])):], fill=(0, 0, 0), font=font_style)
    else:
        draw.text((132, 388), profile.word, fill=(0, 0, 0), font=font_style)

    for i in range(0, 5):
        try:
            assetbundleName = ''
            for j in cards:
                if j['id'] == profile.userDecks[i]:
                    assetbundleName = j['assetbundleName']
            # logger.debug(f"使用的卡组为：{profile.special_training}")
            if profile.special_training[i]:
                cardimg = Image.open('./data/assets/sekai/assetbundle/resources'
                                     f'/startapp/thumbnail/chara/{assetbundleName}_after_training.png')
            else:
                cardimg = Image.open('./data/assets/sekai/assetbundle/resources'
                                     f'/startapp/thumbnail/chara/{assetbundleName}_normal.png')
            # cardimg = cardimg.resize((151, 151))
            r, g, b, mask = cardimg.split()
            img.paste(cardimg, (111 + 128 * i, 488), mask)
        except FileNotFoundError:
            pass

    font_style = ImageFont.truetype("./data/FOT-RodinNTLGPro-DB.ttf", 24)
    for i in range(0, 5):
        bbox = font_style.getbbox(str(profile.clear[i]))
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_coordinate = (int(167 + 105 * i - text_width / 2), int(732 - text_height / 2))
        draw.text(text_coordinate, str(profile.clear[i]), fill=(0, 0, 0), font=font_style)

        bbox = font_style.getbbox(str(profile.full_combo[i]))
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_coordinate = (int(167 + 105 * i - text_width / 2), int(732 + 133 - text_height / 2))
        draw.text(text_coordinate, str(profile.full_combo[i]), fill=(0, 0, 0), font=font_style)

        bbox = font_style.getbbox(str(profile.full_perfect[i]))
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_coordinate = (int(167 + 105 * i - text_width / 2), int(732 + 2 * 133 - text_height / 2))
        draw.text(text_coordinate, str(profile.full_perfect[i]), fill=(0, 0, 0), font=font_style)

    bbox = font_style.getbbox(str(profile.clear[5]))
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_coordinate = (int(707 - text_width / 2), int(732 - text_height / 2))
    draw.text(text_coordinate, str(profile.clear[5]), fill=(0, 0, 0), font=font_style)

    bbox = font_style.getbbox(str(profile.full_combo[5]))
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_coordinate = (int(707 - text_width / 2), int(732 + 133 - text_height / 2))
    draw.text(text_coordinate, str(profile.full_combo[5]), fill=(0, 0, 0), font=font_style)

    bbox = font_style.getbbox(str(profile.full_perfect[5]))
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_coordinate = (int(707 - text_width / 2), int(732 + 2 * 133 - text_height / 2))
    draw.text(text_coordinate, str(profile.full_perfect[5]), fill=(0, 0, 0), font=font_style)

    character = 0
    font_style = ImageFont.truetype("./data/FOT-RodinNTLGPro-DB.ttf", 29)
    for i in range(0, 5):
        for j in range(0, 4):
            character += 1
            characterRank = 0
            for charas in profile.characterRank:
                if charas['characterId'] == character:
                    characterRank = charas['characterRank']
                    break
            bbox = font_style.getbbox(str(characterRank))
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_coordinate = (int(916 + 184 * j - text_width / 2), int(688 + 87.5 * i - text_height / 2))
            draw.text(text_coordinate, str(characterRank), fill=(0, 0, 0), font=font_style)
    for i in range(0, 2):
        for j in range(0, 4):
            character += 1
            characterRank = 0
            for charas in profile.characterRank:
                if charas['characterId'] == character:
                    characterRank = charas['characterRank']
                    break
            bbox = font_style.getbbox(str(characterRank))
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_coordinate = (int(916 + 184 * j - text_width / 2), int(512 + 88 * i - text_height / 2))
            draw.text(text_coordinate, str(characterRank), fill=(0, 0, 0), font=font_style)
            if character == 26:
                break

    draw.text((952, 141), f'{profile.mvpCount}回', fill=(0, 0, 0), font=font_style)
    draw.text((1259, 141), f'{profile.superStarCount}回', fill=(0, 0, 0), font=font_style)
    try:
        chara = Image.open(f'chara/chr_ts_{profile.characterId}.png')
        chara = chara.resize((70, 70))
        r, g, b, mask = chara.split()
        img.paste(chara, (952, 293), mask)
        draw.text((1032, 315), str(profile.highScore), fill=(0, 0, 0), font=font_style)
    except:
        pass
    for i in profile.userProfileHonors:
        if i['seq'] == 1:
            try:
                honorpic = generatehonor(i, True, profile.userHonorMissions)
                honorpic = honorpic.resize((266, 56))
                r, g, b, mask = honorpic.split()
                img.paste(honorpic, (104, 228), mask)
            except:
                pass

    for i in profile.userProfileHonors:
        if i['seq'] == 2:
            try:
                honorpic = generatehonor(i, False, profile.userHonorMissions)
                honorpic = honorpic.resize((126, 56))
                r, g, b, mask = honorpic.split()
                img.paste(honorpic, (375, 228), mask)
            except:
                pass

    for i in profile.userProfileHonors:
        if i['seq'] == 3:
            try:
                honorpic = generatehonor(i, False, profile.userHonorMissions)
                honorpic = honorpic.resize((126, 56))
                r, g, b, mask = honorpic.split()
                img.paste(honorpic, (508, 228), mask)
            except:
                pass

    image_path = f"data/piccache/{userid}profile.png"
    # logger.debug(f"Saving image to {image_path}")
    if not os.path.exists(os.path.dirname(image_path)):
        os.makedirs(os.path.dirname(image_path))

    img.save(image_path)
    img = Image.open(image_path)
    # logger.debug("success generate image")
    return  image_path


def generatehonor(honor, ismain=True, userHonorMissions=None):
    star = False
    backgroundAssetbundleName = ''
    frameName = ''
    assetbundleName = ''
    groupId = 0
    honorRarity = 0
    honorType = ''
    honor['profileHonorType'] = honor.get('profileHonorType', 'normal')

    is_live_master = False
    masterdatadir = 'twmasterdata'


    if honor['profileHonorType'] == 'normal':
        # 普通牌子
        with open(f'{masterdatadir}/honors.json', 'r', encoding='utf-8') as f:
            honors = json.load(f)
            # if honors:
            #     logger.info("honors load success")
        with open(f'{masterdatadir}/honorGroups.json', 'r', encoding='utf-8') as f:
            honorGroups = json.load(f)
            # if honors:
            #     logger.info("honorgroup load success")
        for i in honors:
            if i['id'] == honor['honorId']:
                try:
                    assetbundleName = i['assetbundleName']
                    honorRarity = i['honorRarity']
                    try:
                        level2 = i['levels'][1]['level']
                        star = True
                    except IndexError:
                        pass

                    for j in honorGroups:
                        if j['id'] == i['groupId']:
                            try:
                                backgroundAssetbundleName = j['backgroundAssetbundleName']
                            except KeyError:
                                backgroundAssetbundleName = ''
                            
                            try:
                                frameName = j['frameName']
                            except KeyError:
                                pass
                            honorType = j['honorType']
                            break
                    filename = 'honor'
                    mainname = 'rank_main.png'
                    subname = 'rank_sub.png'
                except KeyError:
                    honorMissionType = i['honorMissionType']
                    for level in i['levels']:
                        if honor['honorLevel'] == level['level']:
                            assetbundleName = level['assetbundleName']
                            honorRarity = level['honorRarity']
                    filename = 'honor'
                    mainname = 'scroll.png'
                    subname = 'scroll.png'
                    is_live_master = True
        if honorType == 'rank_match':
            filename = 'rank_live/honor'
            mainname = 'main.png'
            subname = 'sub.png'

        if ismain:

            if honorRarity == 'low':
                path = 'pics/frame_degree_m_1.png'
            elif honorRarity == 'middle':
                path = 'pics/frame_degree_m_2.png'
            elif honorRarity == 'high':
                path = 'pics/frame_degree_m_3.png'
            else:
                path = 'pics/frame_degree_m_4.png'

            # 检查带 frameName 的路径是否存在
            full_path = 'data/assets/sekai/assetbundle/resources/startapp/honor_frame/' + frameName + path[4:]
            # logger.debug(full_path, os.path.exists(full_path))
            if os.path.exists(full_path):
                frame = Image.open(full_path)
            else:
                frame = Image.open(path)  # 如果文件不存在，只打开默认图片
            if backgroundAssetbundleName == '':
                rankpic = None
                try:
                    pic = gethonorasset(path='data/assets/sekai/assetbundle/resources'
                                 f'/startapp/{filename}/{assetbundleName}/degree_main.png')
                except FileNotFoundError:
                    pass
                # logger.debug(f"rankpic:{pic}")
                try:
                    rankpic = gethonorasset(path='data/assets/sekai/assetbundle/resources'
                                         f'/startapp/{filename}/{assetbundleName}/{mainname}')
                    logger.debug(f"rankpic:{rankpic}")
                except FileNotFoundError:
                    pass
                r, g, b, mask = frame.split()
                if honorRarity == 'low':
                    pic.paste(frame, (8, 0), mask)
                else:
                    pic.paste(frame, (0, 0), mask)
                if rankpic is not None:
                    r, g, b, mask = rankpic.split()
                    if is_live_master:
                        pic.paste(rankpic, (218, 3), mask)
                        for i in userHonorMissions:
                            if honorMissionType == i['honorMissionType']:
                                progress = i['progress']
                        draw = ImageDraw.Draw(pic)
                        font_style = ImageFont.truetype("data/HarmonyOS_Sans_SC_Medium.ttf", 20)
                        bbox = font_style.getbbox(str(progress))
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        text_coordinate = (int(270 - text_width / 2), int(58 - text_height / 2))
                        draw.text(text_coordinate, str(progress), fill=(255, 255, 255), font=font_style)

                        star_count = (progress // 10) % 10 + 1
                        stars_pos = [
                             (223, 68), (216, 56), (208, 42), (216, 27), (223, 13),
                             (295, 68), (304, 56), (311, 42), (303, 27), (295, 13)
                        ]

                        with_star = Image.open('pics/live_master_honor_star_1.png')
                        with_star_alpha = with_star.split()[3]
                        without_star = Image.open('pics/live_master_honor_star_2.png')
                        without_star_alpha = without_star.split()[3]

                        for i in range(10):
                            if star_count <= i:
                                star_pic, star_alpha = without_star, without_star_alpha
                            else:
                                star_pic, star_alpha = with_star, with_star_alpha
                            pic.paste(star_pic, (stars_pos[i][0], stars_pos[i][1] - 8), star_alpha)
                    else:
                        pic.paste(rankpic, (190, 0), mask)
            else:
                pic = gethonorasset(path='data/assets/sekai/assetbundle/resources'
                                 f'/startapp/{filename}/{backgroundAssetbundleName}/degree_main.png')
                rankpic = gethonorasset(path='data/assets/sekai/assetbundle/resources'
                                     f'/startapp/{filename}/{assetbundleName}/{mainname}')
                r, g, b, mask = frame.split()
                if honorRarity == 'low':
                    pic.paste(frame, (8, 0), mask)
                else:
                    pic.paste(frame, (0, 0), mask)
                r, g, b, mask = rankpic.split()
                if rankpic.width == 380:
                    pic.paste(rankpic, (0, 0), mask)
                else:
                    pic.paste(rankpic, (190, 0), mask)
            if honorType == 'character' or honorType == 'achievement':
                honorlevel = honor['honorLevel']
                if star is True:
                    if honorlevel > 10:
                        honorlevel = honorlevel - 10
                    if honorlevel < 5:
                        for i in range(0, honorlevel):
                            lv = Image.open('pics/icon_degreeLv.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
                    else:
                        for i in range(0, 5):
                            lv = Image.open('pics/icon_degreeLv.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
                        for i in range(0, honorlevel - 5):
                            lv = Image.open('pics/icon_degreeLv6.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
        else:
            # 小图         
            if honorRarity == 'low':
                path = 'pics/frame_degree_s_1.png'
            elif honorRarity == 'middle':
                path = 'pics/frame_degree_s_2.png'
            elif honorRarity == 'high':
                path = 'pics/frame_degree_s_3.png'
            else:
                path = 'pics/frame_degree_s_4.png'

            # 检查带 frameName 的路径是否存在
            full_path = 'data/assets/sekai/assetbundle/resources/startapp/honor_frame/' + frameName + path[4:]
            if os.path.exists(full_path):
                frame = Image.open(full_path)
            else:
                frame = Image.open(path)  # 如果文件不存在，只打开默认图片
            if backgroundAssetbundleName == '':
                rankpic = None
                pic = gethonorasset(path='data/assets/sekai/assetbundle/resources'
                                 f'/startapp/{filename}/{assetbundleName}/degree_sub.png')
                try:
                    rankpic = gethonorasset(path='data/assets/sekai/assetbundle/resources'
                                         f'/startapp/{filename}/{assetbundleName}/{subname}')
                except FileNotFoundError:
                    pass
                r, g, b, mask = frame.split()
                if honorRarity == 'low':
                    pic.paste(frame, (8, 0), mask)
                else:
                    pic.paste(frame, (0, 0), mask)
                if rankpic is not None:
                    r, g, b, mask = rankpic.split()
                    if is_live_master:
                        pic.paste(rankpic, (40, 3), mask)
                        for i in userHonorMissions:
                           if honorMissionType == i['honorMissionType']:
                              progress = i['progress']
                        draw = ImageDraw.Draw(pic)
                        font_style = ImageFont.truetype("data/HarmonyOS_Sans_SC_Medium.ttf", 20)
                        bbox = font_style.getbbox(str(progress))
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        text_coordinate = (int(90 - text_width / 2), int(58 - text_height / 2))
                        draw.text(text_coordinate, str(progress), fill=(255, 255, 255), font=font_style)
                    else:
                        pic.paste(rankpic, (34, 42), mask)
            else:
                pic = gethonorasset(path='./data/assets/sekai/assetbundle/resources'
                                 f'/startapp/{filename}/{backgroundAssetbundleName}/degree_sub.png')
                rankpic = gethonorasset(path='./data/assets/sekai/assetbundle/resources'
                                     f'/startapp/{filename}/{assetbundleName}/{subname}')
                r, g, b, mask = frame.split()
                if honorRarity == 'low':
                    pic.paste(frame, (8, 0), mask)
                else:
                    pic.paste(frame, (0, 0), mask)
                r, g, b, mask = rankpic.split()
                print(rankpic.height)
                if rankpic.height == 80:
                    pic.paste(rankpic, (0, 0), mask)
                else:
                    pic.paste(rankpic, (34, 42), mask)
            if honorType == 'character' or honorType == 'achievement':
                if star is True:
                    honorlevel = honor['honorLevel']
                    if honorlevel > 10:
                        honorlevel = honorlevel - 10
                    if honorlevel < 5:
                        for i in range(0, honorlevel):
                            lv = Image.open('pics/icon_degreeLv.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
                    else:
                        for i in range(0, 5):
                            lv = Image.open('pics/icon_degreeLv.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
                        for i in range(0, honorlevel - 5):
                            lv = Image.open('pics/icon_degreeLv6.png')
                            r, g, b, mask = lv.split()
                            pic.paste(lv, (54 + 16 * i, 63), mask)
    elif honor['profileHonorType'] == 'bonds':
        # cp牌子
        with open(f'{masterdatadir}/bondsHonors.json', 'r', encoding='utf-8') as f:
            bondsHonors = json.load(f)
            for i in bondsHonors:
                if i['id'] == honor['honorId']:
                    gameCharacterUnitId1 = i['gameCharacterUnitId1']
                    gameCharacterUnitId2 = i['gameCharacterUnitId2']
                    honorRarity = i['honorRarity']
                    break
        if ismain:
            # 大图
            if honor['bondsHonorViewType'] == 'reverse':
                pic = bondsbackground(gameCharacterUnitId2, gameCharacterUnitId1)
            else:
                pic = bondsbackground(gameCharacterUnitId1, gameCharacterUnitId2)
            chara1 = Image.open(f'chara/chr_sd_{str(gameCharacterUnitId1).zfill(2)}_01/chr_sd_'
                                f'{str(gameCharacterUnitId1).zfill(2)}_01.png')
            chara2 = Image.open(f'chara/chr_sd_{str(gameCharacterUnitId2).zfill(2)}_01/chr_sd_'
                                f'{str(gameCharacterUnitId2).zfill(2)}_01.png')
            if honor['bondsHonorViewType'] == 'reverse':
                chara1, chara2 = chara2, chara1
            r, g, b, mask = chara1.split()
            pic.paste(chara1, (0, -40), mask)
            r, g, b, mask = chara2.split()
            pic.paste(chara2, (220, -40), mask)
            maskimg = Image.open('pics/mask_degree_main.png')
            r, g, b, mask = maskimg.split()
            pic.putalpha(mask)
            if honorRarity == 'low':
                frame = Image.open('pics/frame_degree_m_1.png')
            elif honorRarity == 'middle':
                frame = Image.open('pics/frame_degree_m_2.png')
            elif honorRarity == 'middle':
                frame = Image.open('pics/frame_degree_m_3.png')
            else:
                frame = Image.open('pics/frame_degree_m_4.png')
            r, g, b, mask = frame.split()
            if honorRarity == 'low':
                pic.paste(frame, (8, 0), mask)
            else:
                pic.paste(frame, (0, 0), mask)
            wordbundlename = f"honorname_{str(gameCharacterUnitId1).zfill(2)}" \
                             f"{str(gameCharacterUnitId2).zfill(2)}_{str(honor['bondsHonorWordId']%100).zfill(2)}_01"
            word = Image.open('./data/assets/sekai/assetbundle/resources/startapp'
                                 f'/bonds_honor/word/{wordbundlename}.png')
            r, g, b, mask = word.split()
            pic.paste(word, (int(190-(word.size[0]/2)), int(40-(word.size[1]/2))), mask)
            if honor['honorLevel'] < 5:
                for i in range(0, honor['honorLevel']):
                    lv = Image.open('pics/icon_degreeLv.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
            else:
                for i in range(0, 5):
                    lv = Image.open('pics/icon_degreeLv.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
                for i in range(0, honor['honorLevel'] - 5):
                    lv = Image.open('pics/icon_degreeLv6.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
        else:
            # 小图
            if honor['bondsHonorViewType'] == 'reverse':
                pic = bondsbackground(gameCharacterUnitId2, gameCharacterUnitId1, False)
            else:
                pic = bondsbackground(gameCharacterUnitId1, gameCharacterUnitId2, False)
            chara1 = Image.open(f'chara/chr_sd_{str(gameCharacterUnitId1).zfill(2)}_01/chr_sd_'
                                f'{str(gameCharacterUnitId1).zfill(2)}_01.png')
            chara2 = Image.open(f'chara/chr_sd_{str(gameCharacterUnitId2).zfill(2)}_01/chr_sd_'
                                f'{str(gameCharacterUnitId2).zfill(2)}_01.png')
            if honor['bondsHonorViewType'] == 'reverse':
                chara1, chara2 = chara2, chara1
            chara1 = chara1.resize((120, 102))
            r, g, b, mask = chara1.split()
            pic.paste(chara1, (-5, -20), mask)
            chara2 = chara2.resize((120, 102))
            r, g, b, mask = chara2.split()
            pic.paste(chara2, (60, -20), mask)
            maskimg = Image.open('pics/mask_degree_sub.png')
            r, g, b, mask = maskimg.split()
            pic.putalpha(mask)
            if honorRarity == 'low':
                frame = Image.open('pics/frame_degree_s_1.png')
            elif honorRarity == 'middle':
                frame = Image.open('pics/frame_degree_s_2.png')
            elif honorRarity == 'middle':
                frame = Image.open('pics/frame_degree_s_3.png')
            else:
                frame = Image.open('pics/frame_degree_s_4.png')
            r, g, b, mask = frame.split()
            if honorRarity == 'low':
                pic.paste(frame, (8, 0), mask)
            else:
                pic.paste(frame, (0, 0), mask)
            if honor['honorLevel'] < 5:
                for i in range(0, honor['honorLevel']):
                    lv = Image.open('pics/icon_degreeLv.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
            else:
                for i in range(0, 5):
                    lv = Image.open('pics/icon_degreeLv.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
                for i in range(0, honor['honorLevel'] - 5):
                    lv = Image.open('pics/icon_degreeLv6.png')
                    r, g, b, mask = lv.split()
                    pic.paste(lv, (54 + 16 * i, 63), mask)
    return pic

def gethonorasset(server = 'jp', path=None):
    if server == 'jp':
        return Image.open(path)
    if 'bonds_honor' in path:  # 没解出来 之后再改
        return Image.open(path)
    else:
        path = path.replace('startapp/honor', f'startapp/{server}honor').replace('startapp/honor', f'startapp/{server}honor')
        if os.path.exists(path):
            return Image.open(path)
        else:
            dirs = os.path.abspath(os.path.join(path, ".."))
            foldername = dirs[dirs.find(f'{server}honor') + len(f'{server}honor') + 1:]
            filename = path[path.find(foldername) + len(foldername) + 1:]
            try:
                if server == 'tw':
                    print(f'download from https://storage.sekai.best/sekai-tc-assets/honor/{foldername}_rip/{filename}')
                    resp = requests.get(f"https://storage.sekai.best/sekai-tc-assets/honor/{foldername}_rip/{filename}", timeout=4)
            except:
                return Image.open(path.replace('{server}honor', 'honor'))
            if resp.status_code == 200:  # 下载到了
                pic = Image.open(io.BytesIO(resp.content))
                if not os.path.exists(dirs):
                    os.makedirs(dirs)
                pic.save(path)
                return pic
            else:
                return Image.open(path)

def bondsbackground(chara1, chara2, ismain=True):
    if ismain:
        pic1 = Image.open(f'bonds/{str(chara1)}.png')
        pic2 = Image.open(f'bonds/{str(chara2)}.png')
        pic2 = pic2.crop((190, 0, 380, 80))
        pic1.paste(pic2, (190, 0))
    else:
        pic1 = Image.open(f'bonds/{str(chara1)}_sub.png')
        pic2 = Image.open(f'bonds/{str(chara2)}_sub.png')
        pic2 = pic2.crop((90, 0, 380, 80))
        pic1.paste(pic2, (90, 0))
    return pic1
