# VPet 换形象改造方案

> 目标：把 VPet 自带的「萝莉斯」形象替换成自己的宠物形象，用于闭源商用。
> 编写日期：2026-10-03
> 依据：VPet 官方 `Secondary Development Support Documentation.md` + 源码实测 + 实际素材统计

---

## 一、先解决商用合规问题（最重要）

这是整个改造的前提，必须先理清。

| 对象 | 授权情况 | 能否闭源商用 |
|---|---|---|
| **VPet 代码** | Apache License 2.0 | 可以。只需保留版权声明与 NOTICE 文件，附带专利授权 |
| **自带动画素材** | 版权归「虚拟主播模拟器制作组」 | **不能直接用**。商用需弹窗告知来源、页面标注来源、禁止出售动画文件盈利、并邮件联系作者 |
| **内置图片 / Zip 图库** | 同上，且 Zip 图库明确禁止商用 | 不能直接用 |

**关键结论**：官方文档明确写道——

> 本动画声明仅限于桌宠自带的动画，**若有画师/开发者画自己的动画适配给桌宠，并不遵循本声明**

**所以商用路线就是：全部素材自制。** 一旦用自制素材，就完全绕开这套附加条款，只剩 Apache-2.0 约束。这和「换宠物形象」的目标天然一致。

**注意**：如果后续想用 Live2D 做形象，需额外确认 Live2D Cubism SDK 的商用分级授权（发行商事业规模超阈值要付费，Cubism Editor 免费版也有营收门槛）。

---

## 二、素材规格

| 项 | 规格 |
|---|---|
| 格式 | PNG，透明背景 |
| 尺寸 | **1000 × 1000 像素**（实测官方 6181 张素材全部统一此规格） |
| 帧时长 | 写在**文件名末位**，单位毫秒。如 `125` 表示每帧 125ms |
| 帧序号 | 三位数字，从 `000` 开始递增 |

---

## 三、目录结构与命名规范

### 3.1 整体位置

```
VPet-Simulator.Windows/mod/0000_core/
├── info.lps              MOD 信息配置
├── pet/
│   ├── vup.lps           动画配置（交互坐标等，必改）
│   └── vup/              动画素材根目录
│       ├── Default/      动画类型
│       ├── Sleep/
│       ├── WORK/
│       └── ...
├── food/                 食物、饮料、药品
├── image/                物品图标
├── lang/                 多语言文本
├── text/                 说话台词
├── theme/                主题与字体
└── photo/                图鉴
```

### 3.2 动画素材的两种组织方式

**方式 A：状态 / 变体分层**（如 `Default`、`Eat`、`Think`）

```
Default/
├── Happy/
│   ├── 1/            变体编号
│   │   └── 循环A_000_125.png
│   ├── 2/
│   └── 3/
├── Nomal/
├── PoorCondition/
└── Ill/
```

**方式 B：段 + 状态合并命名**（如 `Sleep`、`Touch_Head`）

```
Sleep/
├── A_Happy/           A 段 + Happy 状态
├── A_Nomal/
├── A_PoorCondition/
├── B_Happy/
├── B_Nomal/
├── B_PoorCondition/
├── B_ill/
├── C_Happy/
├── C_Nomal/
└── C_PoorCondition/
```

**注意**：**状态是由目录名识别的**（`Happy` / `Nomal` / `PoorCondition` / `Ill`），不写在文件名里。

### 3.3 文件名规范

```
{动画名称}_{帧序号}_{帧时长}.png
```

官方实际使用的例子：

```
躺下_000_125.png          中文名 + 000 帧 + 125ms
睡觉循环_000_125.png
happysleep_001_125.png    英文名也可
_000_125.png              名称可留空
时间轴 1_000_125.png      名称可含空格
```

**解析器的容错特性**（重要，能省很多事）：

- 状态 / 动画类型 / 动画名称三者**顺序不限**
- `_` 和 `/` 可以互相替换
- 会自动过滤纯数字段和 `~` 开头的标记
- 解析优先级：**配置文件 > 路径关键词 > 默认值**
- 大小写不敏感

所以**最省事的做法是照抄官方目录结构和命名，只替换 PNG 内容**，不用去猜解析规则。

---

## 四、必须提供的动画（优先级）

### 4.1 硬性必须的 7 个

缺了系统跑不起来或表现异常：

| 类型 | 含义 | 结构要求 |
|---|---|---|
| `Raised_Dynamic` | 被提起（动态） | Single |
| `Raised_Static` | 被提起（静态） | ABC 三段 |
| `Default` | 呼吸 / 待机（核心） | Single |
| `Sleep` | 睡觉 | ABC 三段 |
| `Say` | 说话 | ABC 三段 |
| `StartUP` | 开机 | Single |
| `Work` | 工作 | ABC 三段 |

### 4.2 ABC 三段式说明

```
A_Start  入场 / 准备    → 播放一次
B_Loop   主体 / 持续    → 循环播放（次数可变）
C_End    退场 / 结束    → 播放一次
```

以摸头为例：A 段是手接近头部，B 段是持续摸头，C 段是手离开。这种设计让循环次数可以动态控制，动画依然完整。

### 4.3 最小可用集建议

如果不想一次做完 25 类、6181 帧，**建议按此顺序推进**：

1. **第一批（能跑起来）**：`Default`（130 帧）+ `StartUP` + `Shutdown`
2. **第二批（能交互）**：`Raise`（被提起）、`Touch_Head`、`Touch_Body`、`Pinch`
3. **第三批（有养成感）**：`Sleep`、`Say`、`IDEL`、`MOVE`
4. **第四批（完整）**：`WORK`（2214 帧，工作量最大，可后置或精简）

---

## 五、交互坐标配置（vup.lps）

**这是换形象时最容易漏掉、也最容易出问题的地方。**

### 5.1 文件格式

`.lps` 是 VPet 自定义格式，**不是 JSON**：

```
键#值:|
嵌套写法：键:|子键#子值:|
```

### 5.2 必须调整的字段

文件：`mod/0000_core/pet/vup.lps`

```
pet#vup:|                                    宠物标识
intor#虚拟主播模拟器默认人物形象:|              介绍文本
path#vup:|                                   素材路径
petname#萝莉斯:|                              宠物名字
tag#all,vup,girl:|                           标签

touchhead:|px#159:|py#16:|sw#189:|sh#178:|   摸头判定区
touchbody:|px#166:|py#206:|sw#163:|sh#136:|  摸身体判定区
pinch:|px#149:|py#128:|sw#56:|sh#59:|        捏的判定区

touchraised:|happy_px#0:|happy_py#50:|happy_sw#500:|happy_sh#200:|   被提起时
             nomal_px#0:|...:|poorcondition_px#0:|...:|ill_px#0:|...:|

raisepoint:|happy_x#290:|happy_y#128:|nomal_x#290:|nomal_y#128:|      抓取锚点
            poorcondition_x#290:|poorcondition_y#128:|ill_x#225:|ill_y#115:|
```

**`px / py` 是相对位置，`sw / sh` 是宽高**。因为不同形象的头部、身体位置完全不同，**换形象后这些数值必须重新测量**，否则点击摸头、拖拽提起的判定区域会全部错位。

注意 `raisepoint` 和 `touchraised` 要**按 4 种状态分别配置**（`happy_` / `nomal_` / `poorcondition_` / `ill_` 前缀）。

### 5.3 怎么测

在游戏里打开开发控制台（`winConsole`），或直接按新形象的实际像素位置估算：以 1000×1000 画布左上角为原点，量出头部区域左上角坐标和宽高。

---

## 六、完整改造步骤

### 步骤 1：备份原始 MOD

```bash
cd VPet-Simulator.Windows/mod
cp -r 0000_core 0001_mypet
```

建议新建一个独立 MOD 目录而不是直接改 `0000_core`，便于对照和回退。

### 步骤 2：修改 info.lps

改成自己的 MOD 标识：

```
vupmod#MyPet:|
author#你的名字:|
gamever#11000:|
ver#11000:|
intro#你的桌宠介绍:|
itemid#2:|
lang#zh-Hans:|介绍#介绍:|MyPet#我的宠物:|
```

**注意 `itemid` 必须与 `0000_core` 不同**，否则会冲突。

### 步骤 3：替换动画素材

按第三节的目录结构和命名规范，把自制 PNG 放进去。

**最省事的做法**：先照抄官方目录树（`cp -r`），再逐个目录替换 PNG 文件，保持文件名格式不变。

### 步骤 4：调整 vup.lps 坐标

按第五节的字段，重新测量并填入新形象的判定区坐标。

### 步骤 5：处理其他配置

| 文件 | 作用 | 是否必改 |
|---|---|---|
| `food/*.lps` | 食物 / 饮料 / 药品定义 | 可保留 |
| `text/*.lps` | 说话台词 | 建议改成自己的文案 |
| `lang/zh-Hans/*.lps` | 界面文本 | 可保留 |
| `theme/default.lps` | 主题配色 | 可选 |
| `image/*` | 物品图标 | 可保留 |

### 步骤 6：在游戏里加载

启动 VPet → 设置 → MOD 管理，确认新 MOD 被识别。也可以通过创意工坊机制导入。

---

## 七、构建与调试

### 7.1 环境要求

| 项 | 要求 | 当前状态 |
|---|---|---|
| .NET SDK | **10.0**（主程序目标框架为 `net10.0-windows7.0`） | 未安装，需 `winget install Microsoft.DotNet.SDK.10` |
| .NET 运行时 | 10.0（已装 10.0.11） | 已满足 |
| Visual Studio | 可选，命令行 `dotnet build` 亦可 | 未安装 |

### 7.2 构建命令

```bash
cd VPet
dotnet build VPet.sln -c Debug -p:Platform=x64
```

或用 Visual Studio 打开 `VPet.sln`，平台选 **x64**，启动项目选 **`VPet-Simulator.Windows`**。

### 7.3 关键坑：mklink.bat

**首次构建后启动会报错「缺少模组 Core，无法启动桌宠」——这是正常的。**

需要**以管理员身份**运行 `VPet-Simulator.Windows/mklink.bat`，它会把 `mod` 目录链接到编译输出位置：

```
bin\x64\Debug\net10.0-windows7.0\mod
```

脚本里还有 4 个指向**仓库外**的配套项目链接（`VPet.ModMaker`、`VPet.Plugin.Demo` 系列等），**报错是正常的，脚本自己也有提示，可以忽略**。

### 7.4 配套仓库（按需）

| 仓库 | 用途 |
|---|---|
| `LorisYounger/VPet.ModMaker` | MOD 制作器（图片帧生成） |
| `LorisYounger/VPet.Plugin.Demo` | 插件开发示例（含时钟、EdgeTTS、ChatGPT 插件） |

---

## 八、附录：完整动画类型清单

实测 25 个动画类型、共 6181 帧：

| 类型 | 帧数 | 子结构 | 说明 |
|---|---|---|---|
| `BDay` | 53 | A, B, C | 生日 |
| `Default` | 130 | Happy, Ill, Nomal, PoorCondition | 呼吸 / 待机（核心必须） |
| `Drink` | 103 | Happy, Ill, Nomal, PoorCondition, front_lay | 喝 |
| `Eat` | 114 | Happy, Ill, Nomal, PoorCondition | 吃 |
| `Gift` | 157 | Happy, Ill, Nomal, PoorCondition | 礼物 |
| `IDEL` | 849 | Boring, Bubbles, Meow, Squat, Tennis, amusement_B, aside, happy_like520, meowlook, yawning | 空闲随机动画 |
| `LevelUP` | 82 | Happy, Nomal, PoorCondition | 升级 |
| `MOVE` | 534 | climb.left/right、crawl.left/right、fall.left/right、walk.left/right（±faster/slow） | 移动（所有会动的） |
| `Music` | 354 | A, B, C, Single | 音乐 |
| `Pinch` | 91 | Happy, Nomal, PoorCondition | 捏 |
| `Raise` | 192 | Raised_Dynamic, Raised_Static | 被提起（必须） |
| `Say` | 124 | Self, Serious, Shining, Shy | 说话（必须） |
| `Shutdown` | 170 | 2, Happy_1, Ill, Nomal_1, Nomal_2, PoorCondition | 关机 |
| `SideHide_Left_Main` | 74 | Happy, Nomal, PoorCondition | 左侧隐藏（主体） |
| `SideHide_Left_Rise` | 47 | Happy, Nomal, PoorCondition | 左侧隐藏（探出） |
| `SideHide_Right_Main` | 86 | Happy, Nomal, PoorCondition | 右侧隐藏（主体） |
| `SideHide_Right_Rise` | 47 | Happy, Nomal, PoorCondition | 右侧隐藏（探出） |
| `Sleep` | 57 | A/B/C × Happy/Nomal/PoorCondition/ill | 睡觉（必须） |
| `StartUP` | 120 | Happy, Happy_1, Happy_newyear, Ill, Nomal, Nomal_newyear, PoorCondition | 开机（必须） |
| `State` | 116 | StateONE, StateTWO | 待机模式切换 |
| `Switch` | 160 | Down, Hunger, Thirsty, Up | 状态切换 |
| `Think` | 138 | Happy, Nomal, PoorCondition | 思考 |
| `Touch_Body` | 118 | A/B/C × Happy/ill, Happy_Turn | 摸身体 |
| `Touch_Head` | 51 | A/B/C × Nomal/ill, Happy | 摸头 |
| `WORK` | 2214 | Calligraphy, FixMenu, GrilledSausage, PlayONE, PlayWater, RemoveObject, RopeSkipping, Study, StudyPaint, StudyTWO, WorkClean, WorkONE, WorkTWO | 工作（13 种，工作量最大） |

---

## 九、交互机制备忘（改造时需注意）

- **拖动宠物 = 长按后拖动**：`Main.xaml.cs` 中按下左键后起线程 `Thread.Sleep(PressLength)`，若仍未松开则判定为长按，触发 `DisplayRaised()` 进入被提起状态并注册 `MouseMove`；移动鼠标时按 `GraphConfig.RaisePoint[当前状态]` 计算偏移，调用 `Controller.MoveWindows(x, y)` 移动窗口。
- **`PressLength` 默认 300 毫秒**（配置键 `gameconfig.presslength`）。即按住超过 0.3 秒才进入拖拽，快速点击则触发互动。
- 相关设置项：`AllowMove`（允许自动移动）、`SmartMove` + `SmartMoveInterval`（松手后自动走位）、`MoveArea`（限制活动矩形区域）。

---

## 十、风险提示

1. **素材版权**：必须完全自制，或取得画师明确授权。不要使用任何动漫 IP 同人素材。
2. **分发动画文件禁止收费**：即使自制，也不要单独售卖动画文件。
3. **`itemid` 冲突**：新建 MOD 时必须与 `0000_core` 不同。
4. **Steam 版与源码版差异**：Steam 版为打包发布，源码仓库的素材版本可能滞后。改造前确认两者素材是否一致。
5. **工作量预估**：完整替换 25 类动画需要 6000+ 帧美术素材，建议先做最小可用集验证流程，再逐步补全。
