## 介绍

基于Open cv 模板匹配的脚本，模板图基于960x540的设备。对于其他分辨率识别效果不一定好(可能不能正常完成操作)

## 已有能力
- [x] 支持使用win32api对模拟器进行截图（只支持雷电模拟器）
- [x] 自动实名认证（只支持雷电模拟器）
- [x] 第一章推图及跳过相应出现的引导
- [x] 自动关闭战斗动画
- [x] 自动领取任务奖励
- [x] 多设备登录及切换账号

## 其他

* ADB默认不支持中文输入，中文输入使用的是雷电模拟器的接口。所以如果要使用实名认证功能，需要使用雷电模拟器并传入雷电模拟器的安装目录。**并且由于使用Windows应用程序的命令，会触发防火墙。可以关闭后使用，或者手点下允许。**
* win32api带来的提升还是很高的，使用win32api截图时间平均在0.003秒左右，而使用adb截图耗时浮动在1-2秒。