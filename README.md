### Resona Bot 文档

#### For PJSK Traditional Chinese Server

Resona Bot 是为PJSK繁体中文服务器设计的少功能机器人

---

## 功能列表

### 1. **绑定账号 (tw绑定)**

**命令格式：**
```
tw绑定
```

**功能描述：**
- 绑定账号


### 2. **查询个人信息 (tw个人信息 /twpjskprofile)**

**命令格式：**
```
tw个人信息
或
twpjskprofile
```

**功能描述：**
- 查询个人信息


### 3. **查询整百排名时速 (tw速 /tw线)**

**命令格式：**
```
tw速
或
tw线
```

**功能描述：**
- 查询当前整百排名（如 100 名、200 名等）的20*3时速，以及对应的分数线


### 4. **查询单榜 (wl + 角色罗马音)**

**命令格式：**
```
wl [角色罗马音]
```

**功能描述：**
- 查询指定角色的单人排行榜信息。输入角色的罗马音（如 `mfy`、`knd` 等），机器人将返回该角色的排行榜数据


### 5. **计算时速 (zs + 角色罗马音)**

**命令格式：**
```
zs [角色罗马音]
```

**功能描述：**
- 计算从第 100 名到用户当前所在位置的所需的时速


### 6. **查询他人信息 (twcf/wlcf + @xx + 角色罗马音)**

**命令格式：**
```
twcf @用户 [角色罗马音]
或
wlcf @用户 [角色罗马音]
```

**功能描述：**
- 查看其他玩家的排名和时速情况


### 7. **按位次查询 (twsk)**

**命令格式：**
```
twsk [位次]
```

**功能描述：**
- 按指定的排名位次查询相关信息。如果不输入位次，默认查询用户自己的排名信息。返回结果包含时速、分数，最大查询5个排名位次


### 8. **更新背景 (背景更新 + 图片)**

**命令格式：**
```
更新背景 [图片]
```

**功能描述：**
- 更新个人背景图片。发送带有图片的消息来更新自己的背景。支持 `.jpg` 和 `.png` 格式

**使用示例：**
```
更新背景 [图片]
```

**注意事项：**
- 图片需为（`.jpg` 或 `.png`），大小为1600*1100


