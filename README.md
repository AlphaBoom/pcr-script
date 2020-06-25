## 介绍
> 自用脚本：主要根据当前小号(农场号)的进度添加功能

基于Open cv 模板匹配的脚本，模板图基于960x540的设备。对于其他分辨率识别效果不一定好(可能不能正常完成操作)。

## 已有能力

- [x] 增加申请加入工会功能
- [x] 自动强化前五个角色
- [x] 第三章支持到1图
- [x] 第二章推图支持、剧情跳过支持
- [x] 增加分账号配置任务
- [x] 增加扫荡图功能
- [x] 增加购买1/10/20次mana功能
- [x] 支持使用win32api对模拟器进行截图（只支持雷电模拟器）
- [x] 自动实名认证（只支持雷电模拟器）
- [x] 第一章推图及跳过相应出现的引导
- [x] 自动关闭战斗动画
- [x] 自动领取任务奖励
- [x] 多设备登录及切换账号

## 配置信息

配置默认的账号及需要做哪些任务等信息，需要在工程目录下创建`config.yml`的文件，具体可参考根目录下`sample.yml`文件

```yaml
Accounts: #存账号信息
  -
    account: account1
    password: password1
  -
    account: account2
    password: password2
IDS: #用于实名认证的信息
  -
    id: 身份证号
    name: 张三
Extra:
  guildname: &guidename 行会名称
  dnpath: 'N:\dnplayer2'
Task: #配置执行任务,配置任务名称，如果需要传入参数在下面增加参数，可以根据不同的账号序号配置任务。
      #账号会执行小于等于并且离它最近的序号的任务列表
  1: #配置账号大于等于1的进行以下操作
    -
      - get_quest_reward #领取任务奖励
    -
      - tohomepage #回到首页
    -
      - buy_mana #购买mana
      - 20 #买20次
    -
      - saodang
      - 1 #第一章
      - 9 #level 9
      - 60 #扫荡60次
    -
      - tohomepage
    -
      - get_quest_reward
      
  5: #配置账号大于等于5的进行以下操作
    -
      - get_quest_reward #领取任务奖励
    -
      - tohomepage #回到首页
    - 
      - join_guild
      - *guidename
    -
      - saodang
      - 1 #第一章
      - 9 #level 9
      - 60 #扫荡60次
    -
      - tohomepage
    -
      - get_quest_reward
```

## 其他

* ADB默认不支持中文输入，中文输入使用的是雷电模拟器的接口。所以如果要使用实名认证功能，需要使用雷电模拟器并传入雷电模拟器的安装目录。**并且由于使用Windows应用程序的命令，会触发防火墙。可以关闭后使用，或者手点下允许。**
* win32api带来的提升还是很高的，使用win32api截图时间平均在0.003秒左右，而使用adb截图耗时浮动在1-2秒。由于win32api的方式需要获取模拟器的窗口信息，这个需要根据模拟器来适配。