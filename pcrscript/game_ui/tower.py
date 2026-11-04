"""CN tower pages after the special-quests entrance change (960x540)."""
from dataclasses import dataclass
import re

import cv2 as cv
import numpy as np

from .avatars import face_crop, feature
from .screen import EventUIError, normalized


def confident(screen, pattern, roi, *, exact=True):
    items = [i for i in screen.all(pattern, roi) if i.score >= .95
             and (not exact or re.fullmatch(pattern, normalized(i.text)))]
    return max(items, key=lambda i: i.score) if items else None


def busy(screen):
    return bool(screen.find('正在进行数据连接|加载中|连接中'))


def title(screen):
    return bool(confident(screen,'点击屏幕开始游戏',(260,450,710,535))
                and confident(screen,'主菜单',(0,460,200,540)))


def home(screen):
    return bool(not busy(screen)
                and not screen.find('确认|取消|关闭', (250,100,710,525), exact=True)
                and confident(screen, '露娜之塔', (45, 0, 230, 65))
                and confident(screen, '剧情故事', (600, 0, 720, 70))
                and confident(screen, '通关队伍', (775, 80, 925, 125)))


def floor_number(screen):
    if not home(screen):
        return None
    item = confident(screen, r'\d+层', (310, 75, 480, 125))
    if item:return int(re.search(r'\d+', normalized(item.text))[0])
    maximum=getattr(screen,'tower_max_floor',None)
    return maximum if type(maximum) is int and maximum>0 and top_floor(screen) else None


def top_floor(screen):
    tab=confident(screen,'塔顶',(310,75,415,125))
    return bool(home(screen) and tab and screen.blue_button(tab)
                and confident(screen,'塔顶',(55,100,255,460)))


def selected_cleared(screen):
    floor = floor_number(screen)
    if floor is None:
        return False
    row = confident(screen, '塔顶' if top_floor(screen) else str(floor)+r'[阶层]', (55, 100, 255, 460))
    return bool(row and confident(screen, '通关', (55, row.center[1]+8, 255, row.center[1]+65)))


def recovery_ready(screen):
    return bool(home(screen) and confident(screen,'角色全回复',(315,405,455,455))
                and screen.find('1天仅能全回复角色1次',(440,405,710,455))
                and not screen.find('还剩.*使用',(440,405,710,455)))


def recovery_confirmation(screen):
    return bool(confident(screen,'角色全回复',(300,125,670,165))
                and screen.find('回复所有角色的生命值',(300,190,700,250))
                and screen.find('技能值也将被重置',(300,280,700,320))
                and screen.find('支援角色不是重置的对象',(300,310,700,340))
                and not screen.find('购买|消耗|宝石|玛那',(240,165,720,345)))


def recovery_receipt(screen):
    return bool(confident(screen,'角色全回复',(300,125,670,165))
                and screen.find('所有角色的生命值已回复',(300,235,700,285)))


def target_signature(screen):
    """Floor plus visible enemy HP state; animations outside bars are excluded."""
    floor = floor_number(screen)
    if floor is None:
        raise EventUIError('露娜塔目标楼层未知')
    lengths = []
    # The five bars have ~126px spacing. A 123px stride drifts into the
    # animated scenery to their left; sample only each bar's inner fill.
    for left, right in ((317,408),(443,534),(568,659),(693,785),(819,910)):
        bars = screen.image[293:297, left:right].astype(np.int16)
        green = (bars[:, :, 1] > bars[:, :, 2]+20) & (bars[:, :, 1] > bars[:, :, 0]+20)
        lengths.append(int(np.count_nonzero(green.sum(axis=0) >= 2)))
    return dict(floor=floor, hp=lengths)


def shadow_bars(screen):
    """Read unobscured orange enemy bars, excluding the party and boss HUD.

    Require both long white borders and an orange interior. Damage numbers
    and UB flashes commonly hide bars; missing bars are never counted dead.
    """
    image=screen.image[110:357]
    pixels=image.astype(np.int16)
    white=((pixels.min(2)>175)&(pixels.max(2)-pixels.min(2)<65)).astype(np.uint8)
    lines=cv.morphologyEx(white,cv.MORPH_OPEN,np.ones((1,49),np.uint8))
    contours,_=cv.findContours(lines,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)
    boxes=[cv.boundingRect(c) for c in contours
           if 53<=cv.boundingRect(c)[2]<=70 and cv.boundingRect(c)[3]<=3]
    bars=[]
    for x,y,w,h in boxes:
        for xx,yy,ww,hh in boxes:
            if not (6<=yy-y<=8 and abs(xx-x)<=3 and abs(ww-w)<=4):continue
            inside=image[y+2:yy-1,x:x+w]
            hsv=cv.cvtColor(inside,cv.COLOR_BGR2HSV)
            orange=(hsv[:,:,0]<28)&(hsv[:,:,1]>95)&(hsv[:,:,2]>110)
            # A continuous left-aligned fill distinguishes HP from text/effects.
            filled=orange.sum(0)>=max(1,len(inside)-1)
            indices=np.flatnonzero(filled)
            if not len(indices) or indices[0]>4:continue
            length=int(indices[-1])+1
            if filled[:length].mean()<.9:continue
            bars.append(dict(x=x,y=y+110,fill=length/w))
    return bars if len(bars)<=4 else []


def recommendations(screen, floor):
    return bool(not busy(screen) and (confident(screen, str(floor)+'层通关队伍一览', (200, 10, 750, 70))
        or floor==getattr(screen,'tower_max_floor',None)
        and confident(screen,'塔顶通关队伍一览',(200,10,750,70))))


@dataclass
class Recommendation:
    button: object
    mode: str
    portraits: list
    multi_party: bool = False


def same_face(first, second):
    a, b = feature(first), feature(second)
    ac, bc = a-a.mean(), b-b.mean()
    correlation = float(ac @ bc)/max(float(np.linalg.norm(ac)*np.linalg.norm(bc)), 1e-6)
    return float(a @ b) >= .92 and correlation >= .90


def same_faces(first, second):
    return len(first) == len(second) == 5 and all(same_face(a,b) for a,b in zip(first,second))


def matches_formation(screen, portraits, avatars=None):
    # Rounded source thumbnails and formation cards have different borders.
    # Preserve both identity thresholds and allow two physical pixels of border
    # alignment; never accept a shared frame colour as character identity.
    if len(portraits)!=5:return False
    matched=[any(same_face(face, face_crop(screen.image,
        (48+109*i+dx, 379+dy, 95, 95))) for dx in (-2,-1,0,1,2) for dy in (-2,-1,0,1,2))
        for i,face in enumerate(portraits)]
    if all(matched):return True
    if avatars is None:return False
    # Star upgrades can use a different illustration of the same unit. Both
    # ends must independently resolve to the same canonical avatar identity.
    source=avatars.query(portraits)
    current=avatars.query(formation_faces(screen))
    return all(ok or (a and b and not str(a).startswith('unit:') and normalized(a)==normalized(b))
               for ok,a,b in zip(matched,source,current))


def formation_faces(screen):
    return [face_crop(screen.image,(48+109*i,379,95,95)).copy() for i in range(5)]


def recommendation_rows(screen, *, grouped=False):
    rows = []
    for button in screen.all('^使用$', (740, 95, 815, 435)):
        y = int(button.center[1])-43
        if button.score < .95 or not 90 <= y <= 355:
            continue
        mode = confident(screen, '立即发动|自动', (170, y-12, 250, y+26))
        multi_party=False
        if not mode or not confident(screen, '胜利', (170, y+25, 250, y+62)):
            if not grouped:continue
            headers=screen.all('^玩家等级$',(45,75,165,430))
            parent=max((h.center[1] for h in headers if h.center[1]<=button.center[1]+5),default=None)
            if parent is None:continue
            end=min((h.center[1]-10 for h in headers if h.center[1]>parent),default=435)
            mode=confident(screen,'立即发动|自动',(170,parent-20,250,parent+25))
            if not mode or not confident(screen,'胜利',(170,parent,250,end)):
                continue
            multi_party=True
        # The row must be completely visible, including all five cards.
        portraits = [face_crop(screen.image, (266+81*i, y, 68, 68)) for i in range(5)]
        rows.append(Recommendation(button, normalized(mode.text), portraits,multi_party))
    return rows


def use_confirmation(screen):
    return bool(confident(screen, '队伍编组使用确认', (280, 120, 690, 175))
                and confident(screen, '确认使用这个队伍编组吗[？?]', (300, 168, 680, 205)))


def preview_complete(screen):
    slots = preview_slots(screen)
    return slots is not None and all(slots)


def preview_faces(screen):
    return [face_crop(screen.image,(284+81*i,213,68,68)).copy() for i in range(5)]


def preview_ready(screen):
    cancel = confident(screen, '取消', (260,340,410,410))
    return bool(use_confirmation(screen) and not busy(screen) and cancel
                and abs(cancel.center[1]-373) <= 3
                and float(np.mean(screen.image[175:200,275:685])) > 220)


def preview_slots(screen):
    if not preview_ready(screen):
        return None
    # Empty placeholders are neutral grey; do not treat the warning text alone
    # as a missing member: it is also shown for a fully available team.
    slots = []
    for x in (284, 365, 446, 527, 608):
        patch = cv.cvtColor(screen.image[224:268, x+8:x+58], cv.COLOR_BGR2HSV)
        slots.append(float(np.mean((patch[:, :, 1] > 60) & (patch[:, :, 2] > 80))) >= .15)
    return tuple(slots)


def formation(screen):
    return bool(not busy(screen) and confident(screen, '队伍编组', (300, 0, 650, 70))
                and not use_confirmation(screen))


def simulation_formation(screen):
    return bool(formation(screen) and confident(screen, '模拟战开始', (780, 420, 930, 490))
                and screen.find('设定为模拟战', (590, 480, 930, 525)))


def party_vitals(screen):
    values = []
    for x in (96,205,314,423,532):
        hp = screen.image[479:489, x-42:x+42].astype(np.int16)
        tp = screen.image[494:504, x-42:x+42].astype(np.int16)
        green = (hp[:, :, 1] > hp[:, :, 2]+25) & (hp[:, :, 1] > hp[:, :, 0]+25)
        blue = (tp[:, :, 0] > tp[:, :, 2]+30) & (tp[:, :, 1] > tp[:, :, 2]+30)
        values.append((int(np.count_nonzero(green.sum(axis=0) >= 3)),
                       int(np.count_nonzero(blue.sum(axis=0) >= 3))))
    return values


def reduced_star_badge(screen,index):
    left=48+109*index
    patch=cv.cvtColor(screen.image[448:475,left:left+26],cv.COLOR_BGR2HSV)
    return bool(np.mean((patch[:,:,0]>90)&(patch[:,:,0]<130)
                        &(patch[:,:,1]>110)&(patch[:,:,2]>150))>.15)


def battle_result(screen):
    if screen.find('菜单', (840, 0, 960, 65), exact=True):
        return None
    if confident(screen,'LOSE|DEFEAT|战斗失败',(200,0,760,140)):
        return 'failed'
    if confident(screen, 'WIN[!！]?|战斗胜利', (230, 30, 740, 160)):
        return 'win'
    if confident(screen, 'LOSE|DEFEAT|战斗失败|TIMEUP|时间到', (200, 0, 760, 360)):
        return 'failed'
    return None


def navigation_exit(screen):
    if battle_result(screen)=='failed':
        return confident(screen,'前往露娜之塔',(600,390,950,535))
    if confident(screen, '角色详情', (300,0,650,70)):
        return confident(screen, '确认', (320,450,650,515))
    if use_confirmation(screen):
        return confident(screen, '取消', (260, 340, 410, 410))
    if screen.find(r'(?:\d+层|塔顶)通关队伍一览', (200, 10, 750, 70)):
        return confident(screen, '关闭', (375, 445, 590, 515))
    if formation(screen) and (screen.find('今天的编组角色数') or simulation_formation(screen)):
        return confident(screen, '取消', (640, 425, 780, 490))
    return None
