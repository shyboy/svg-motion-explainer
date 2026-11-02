# SVG Motion Explainer

> 让 AI 读懂你的文章，再为“真正需要动起来”的段落生成可以直接插进微信公众号的 SVG 动效图。

这是一个给 Claude（以及其他支持 `SKILL.md` 规范的 Agent）使用的 **Skill**。它不是动画模板库，而是一套“先想清楚再动手”的工作方法：从原文中找出顺序、流向、并行、状态变化、因果这类**文字很难一眼说清**的关系，用最少的运动把它们讲明白，并输出无 JavaScript、无外部依赖、可以 inline 插入公众号的 SVG + SMIL 动画。

---

## 它解决什么问题

公众号里的动效图通常有两种做法：

| 做法 | 问题 |
|---|---|
| 录屏转 GIF | 体积大、画质糊、文字无法缩放，还会被压缩 |
| 套用现成 SVG 模板、换文字 | 动效和内容关系不大，看起来“在动”，但没讲清楚任何事 |

SVG Motion Explainer 的思路是：**把运动当作解释变量，而不是装饰**。如果把动画去掉，读者什么也没少理解，那这张图就不该动。

## 能做什么 / 不做什么

**适合：**

- 为文章、报告、教程、产品介绍里的某一段生成解释性动效图
- 判断一篇文章里哪些段落值得做动效、哪些用静态图就够了
- 把步骤、路由、并行任务、前后对比、因果链、界面操作等关系做成动画
- 校验已有 SVG 的 SMIL 时间轴是否写对

**不适合：**

- 纯装饰插画、海报
- 视频 / GIF 剪辑
- 只是把固定模板里的文字换一换

## 快速开始

### 1. 安装

**Claude Code / 本地 Agent**

```bash
git clone https://github.com/shyboy/svg-motion-explainer.git ~/.claude/skills/svg-motion-explainer
```

或者放到项目目录的 `.claude/skills/svg-motion-explainer/` 下，只在该项目中生效。

**Claude 应用（网页 / 桌面端）**

把整个仓库打包成 zip（压缩包根目录里要能直接看到 `SKILL.md`），在设置中的 Skills 区域上传即可。入口位置以你当前使用的版本为准。

### 2. 使用

安装后不需要特殊命令，直接用自然语言描述需求，Agent 会在合适的时候自动加载这个 Skill：

```text
这是我公众号文章的草稿，帮我找出 2～3 个最值得做动效的段落，
并为每一段生成一张可以插入公众号的 SVG 动效图。
```

```text
下面这段讲的是「请求先到 Router，再分给多个 Worker 并行执行，结果汇总回来」，
帮我做一张动效图，宽 750。
```

```text
帮我检查这个 SVG 的 SMIL 动画有没有写错：path/to/figure.svg
```

### 3. 插入公众号

1. 在浏览器里打开生成的 `.svg`（或包含它的 HTML 预览页），确认动画正常。
2. 以 **inline SVG 代码**的方式插入正文（例如通过支持插入 HTML / SVG 代码的公众号编辑器，或从渲染好的网页中整段复制粘贴）。**不要**把 `.svg` 当作普通图片上传——那样动画会丢失。
3. 保存草稿，**用手机微信预览**。不同客户端版本的表现可能有差异，桌面浏览器正常不等于手机上一定正常。

## 工作流程

Skill 会引导 Agent 按下面的顺序工作，而不是一上来就写代码：

```text
读原文 → 判断是否值得动 → 写“解释契约” → 选叙事模式 → 分镜(3–7 拍) → 写 SVG → 校验 → 交付
```

1. **确立解释目标**：作者在说什么？读者最可能卡在哪？看完图应该多理解了什么？
2. **判断是否值得动**：只有顺序、方向、状态、时序/并发、因果、视线引导这几类变化，才值得用运动表达。
3. **写解释契约**：

   ```text
   Source passage:          原文段落
   Reader question:         读者的疑问
   Single takeaway:         这张图唯一要传达的结论
   Motion-worthy relationship: 值得用运动表达的关系
   Literal depiction or analogy: 是如实描绘还是类比
   Static fallback state:   不支持动画时显示什么
   ```

4. **选择叙事模式**：步骤 → 分步揭示；路由 → 令牌在节点间移动；并行 → 同时开始、各自完成；对比 → 两侧做同样的操作；状态变化 → 保持对象身份的前后过渡……详见 [`references/narrative-patterns.md`](references/narrative-patterns.md)。
5. **分镜**：3–7 个节拍，循环一般 4–8 秒。公众号里的 SMIL 通常在页面加载时就开始播放，而不是滚动到图片时才开始，所以循环要短。
6. **实现**：`viewBox` 宽 750，高度按内容定；`<title>` + `<desc>` 写结论；`animate` 管透明度，`animateTransform` 管位移和缩放；用嵌套 `<g>` 保住静态定位。
7. **校验**：运行校验脚本，再在浏览器里逐帧检查初始、过程、完成、复位四种状态。
8. **交付**：SVG 文件 + 为什么选这种动法 + 循环时长 + 插入方式 + 尚未验证的兼容性风险。

## 仓库结构

```text
svg-motion-explainer/
├── SKILL.md                         # Skill 主说明：触发条件、工作流、质量标准
├── references/
│   ├── narrative-patterns.md        # 内容关系 → 叙事模式 的对照表与分镜方法
│   └── smil-wechat.md               # 面向公众号的保守 SMIL 写法与兼容性规则
├── scripts/
│   └── validate_svg.py              # SVG / SMIL 静态校验脚本
└── assets/
    └── parallel-tasks-example.svg   # 一个完整示例：三项任务并行开工、各自交付
```

## 校验脚本

```bash
python scripts/validate_svg.py path/to/figure.svg
```

只依赖 Python 标准库。会检查：

- XML 能否正确解析、根元素是否为 `<svg>`
- 是否缺少 `viewBox`、`<title>`、`<desc>`
- 是否使用了 `<script>`、`<foreignObject>`、`on*` 事件属性
- 是否引用了外部资源、是否用了 CSS 动画
- `dur` 是否合法；`begin` 是否依赖 click / hover / scroll 等事件
- `values` 与 `keyTimes` 数量是否一致；`keyTimes` 是否从 0 开始、到 1 结束且单调递增
- `calcMode="spline"` 时 `keySplines` 段数与取值范围是否正确
- 重复的 `id`

退出码 `0` 表示没有错误（警告不影响退出码）。脚本无法判断视觉效果，也无法保证在所有微信客户端中的表现。

## 写 SMIL 时最容易踩的坑

- **`keyTimes` 是比例，不是秒**：`dur="6s"` 时，第 1.8 秒对应 `0.3`。
- **`values`、`keyTimes` 数量必须一致**；`keySplines` 要比它们少一段。
- **`animateTransform` 会覆盖元素自身的 `transform`**：静态定位放外层 `<g>`，动画放内层 `<g>`。
- **先写好静态兜底**：元素的初始属性就是不支持动画时读者看到的画面，别让它是一张空白图。
- **SVG 文字不会自动换行**：用多个 `<text>` / `<tspan>` 手动断行，并在最窄的屏幕宽度下检查。
- **别把 SVG 当图片上传**：要 inline 插入才能保留动画。

## 示例

[`assets/parallel-tasks-example.svg`](assets/parallel-tasks-example.svg)：一句话需求被拆成海报、文案、清单三条并行任务，同时开工、各自在不同时间完成交付。它展示了时序、嵌套变换和 8 点加载器的写法，**只是一个参考，不是默认模板**。

## 兼容性说明

- 输出遵循保守策略：不用 JavaScript、`foreignObject`、外部字体与样式表、复杂滤镜，`animateMotion` 和路径变形需要单独测试。
- 如果需要背景纹理等位图，建议先上传到公众号素材库，再在 SVG 中引用公众号图床地址；校验脚本会对外部资源给出警告，提醒你确认这一点。
- 微信客户端的行为可能随版本变化。最终发布前请务必在目标手机客户端中预览草稿。

## 贡献

欢迎提交 Issue 和 PR，尤其是：

- 新的叙事模式与反例
- 在不同微信客户端版本上的兼容性测试结果
- 校验脚本的新检查项
