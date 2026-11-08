> 来源链接：https://www.youtube.com/watch?v=SFQWumRFT48

这是一份基于您提供的视频转录内容和截图整理的详细笔记。

目录
- 游戏设定与迷宫环境
- 迷宫代码实现与黑盒视角
- 路线分析与策略优化
- 策略的表示与 Softmax 函数
- Episode 与目标函数
- 策略梯度公式推导
- 引入折扣因子与衰减回报
- 代码实现与 Episode 1 手动推演
- 训练过程与结果可视化
- 迁移到大型语言模型（LLM）
- AI 总结

## 游戏设定与迷宫环境
[原片 @ 00:00](https://www.youtube.com/watch?v=SFQWumRFT48&t=0s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_000_800e98ef-ce2a-4a8c-926f-f1f1f63b0b3f.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_001_000167c6-0ba2-4173-8659-54be05434081.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_002_dae382e5-fabb-4e19-90d2-85abeac1d9b2.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_003_f912b821-94e3-48e2-b5c3-75d09e215f5a.jpg)
视频介绍了一个网格迷宫游戏，用于演示强化学习（Reinforcement Learning）的基础概念。
*   **基本设置**：机器人（Agent）可以在网格中执行上下左右移动。
*   **目标与奖励**：到达宝藏（Treasure）获得 10 分；掉入陷阱（Pit）扣除 5 分。其他移动不扣分也不加分。
*   **挑战（Slippery Floor）**：地板非常滑，机器人有 20% 的概率不受控制地向下方滑动一格。在陷阱上方的两个格子，一旦滑倒就会直接掉入陷阱（-5）。
*   **AI 学习效果**：一开始经常掉坑（红色十字），后来逐渐找到宝藏（绿色路径），最终在最近 100 局中赢了 96 局。
*   **背景**：这是最基础的 Policy Gradient 算法 **REINFORCE**。在 2024 年，Cohere 曾使用该算法训练语言模型，并在表现上击败了 PPO。

## 迷宫代码实现与黑盒视角
[原片 @ 01:11](https://www.youtube.com/watch?v=SFQWumRFT48&t=71s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_004_be20f3d4-ea8d-4591-ad4d-5068b69710be.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_005_761c41c4-b369-499a-8278-fd927022b487.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_006_60a6100d-f2fb-49e7-85f9-1e78dc484993.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_007_ae226508-8563-4129-8e32-d35b87959d9a.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_008_cac92695-c8d2-41f9-a21e-494fd2965e68.jpg)
游戏环境的代码逻辑由 `step` 函数负责：
1.  以 20% 的概率覆盖 Agent 的选择，强制将其向下滑动一格（`action = 2`）。
2.  执行动作，并确保 Agent 的坐标不会超出墙壁边界（`np.clip` 作用）。
3.  返回新状态、奖励值以及游戏是否结束的标志（`done`）。
*   **黑盒视角**：对于 Agent 来说，迷宫是一个黑盒。它不知道规则，只能从 `step` 函数获取两个信息：**它落到了哪个格子**以及**获得多少奖励**。

## 路线分析与策略优化
[原片 @ 02:12](https://www.youtube.com/watch?v=SFQWumRFT48&t=132s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_009_97420193-73f8-4838-a223-010534eeae18.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_010_020478ae-0739-419d-8185-0928f3975f04.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_011_ba83382d-54ce-47aa-ad4d-de948163ff0c.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_012_20b3b7a7-2256-4a9f-a487-2466a11e7b74.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_013_479b3eb3-6cd9-406b-9280-d89d52c71179.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_014_3e78d5ca-9518-4c6c-90a7-5821dcd53f50.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_015_b566746c-7a63-410a-a280-afd53772019c.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_016_3582c636-b55e-4c03-adc7-448d97fd11f3.jpg)
虽然人类能看清迷宫全局，但 Agent 只能靠试错。视频分析了两种路径：
*   **短路线（Short route）**：直接穿过陷阱上方的中间行。因为每次移动有 20% 概率滑倒掉坑，所以成功率约为 \(0.8 \times 0.8 = 64.0\%\)。
*   **长路线（Long route）**：先爬到最上面一行，再向右走。即使滑倒也只是掉到中间行，然后可以重新爬上去。成功率高达 90.7%。
*   由于 Agent 看不到迷宫结构，它必须通过机器学习算法（Policy Gradient）在交互中自己发现这条安全路线。

## 策略的表示与 Softmax 函数
[原片 @ 03:06](https://www.youtube.com/watch?v=SFQWumRFT48&t=186s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_017_bd6ca2a5-ea31-45da-9312-71f4027a21ad.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_018_c521184a-9afe-4963-b119-0bdba9b5b50d.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_019_d50768ef-dba1-400a-804c-41968e2ae3aa.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_020_3525a4a1-625a-40e6-a7be-cdadc050d453.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_021_5810c13c-999c-4899-b891-3a3e82ecfe41.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_022_494fdda6-0c3f-4362-858d-e82dc7768591.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_023_db83b821-049f-4f1b-8802-f7cf3dca53e2.jpg)
*   **策略（Policy）**：在迷宫中，我们有 12 个格子，每个格子有 4 个移动方向，共 **48 个数字**，称为 **\(\theta\)**。
*   **Softmax 函数**：由于这四个数字代表偏好但不代表概率，需要通过 Softmax 转换为概率：
    \(\pi(a|s) = \frac{e^{\theta_a^s}}{\sum_c e^{\theta_c^s}}\)
    其中 \(a\) 代表动作，\(s\) 代表状态，\(c\) 遍历所有四个方向。
*   **代码实现**：计算时先减去最大值以防止指数溢出（不改变比例），然后再除以总和保证概率和为 1。
*   **训练前后的对比**：
    *   训练前：所有数字初始化为 0，因此每个方向被选中的概率均为 0.25，表现为没有偏好。
    *   训练后：箭头长度代表概率大小，Agent 在各个格子都强烈倾向于朝着宝藏的方向移动。

## Episode 与目标函数
[原片 @ 04:18](https://www.youtube.com/watch?v=SFQWumRFT48&t=258s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_024_b07b5e96-ae83-4422-ba39-ee6519474759.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_025_f81bcd37-4f0d-4287-b886-10d449669205.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_026_72a0b257-4662-4693-9c98-5b48228233bd.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_027_ffcfeac8-ec4c-4d49-b7d2-a4f88da0c63f.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_028_10fba6f9-7d53-43c1-b6da-66a5c92095f6.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_029_7eb2ecbc-af4d-455d-9676-a03ab965d23e.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_030_7e22be2d-66a3-4b81-b660-0cb1bc7c091d.jpg)
*   **Episode（回合）**：从开始到游戏结束（或最大步数 50）的整个游玩过程。记录为轨迹 \(\tau\)。
*   **Return（回报 \(G\)）**：一个 Episode 的总得分，即所有步骤奖励的总和：
    \(G(\tau) = r_1 + r_2 + r_3 + \dots\)
    例如，第一局游戏共移动 3 次，前两次为 0，最后一次掉坑为 -5，则 \(G = 0 + 0 + (-5) = -5\)。
*   **Objective（目标函数 \(J\)）**：单局游戏充满随机性，因此要评估策略的好坏，需要看平均回报：
    \(J(\theta) = \mathbb{E}_{\tau \sim p(\tau|\theta)}[G(\tau)]\)
    目标是最大化 \(J(\theta)\)。对于未训练的 Agent，它只有 2.6% 的概率找到宝藏，因此 \(J\) 远低于 0。

## 策略梯度公式推导
[原片 @ 05:18](https://www.youtube.com/watch?v=SFQWumRFT48&t=318s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_031_3c655397-7914-49dc-9421-a2868c6d32a9.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_032_6f35369b-81d6-4d88-be73-b74bccdc8c41.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_033_796a40eb-bd2a-4e84-a8cf-bc30a203324d.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_034_17167538-ceb5-4fec-ad73-63e3234bd3fa.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_035_1fa9e7e3-00a7-4677-86e4-1c415299b3f8.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_036_3e489dc3-4b24-4c99-9da0-8c09949ba2aa.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_037_2b28e3f8-e9c9-4cd4-b21b-66cb48aaf210.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_038_1206b53b-34fe-49c3-b215-e4a0b7d5a655.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_039_f14d6c71-5e7f-4546-92a1-5638c9bda6d8.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_040_94d2b928-8c2f-47b0-93ce-4dce3ab6bd22.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_041_7e509f6c-0e9e-4faa-92cc-badb2777672e.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_042_13a38ccc-acd2-44e6-951d-028f1f3bdefd.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_043_91d9adda-0d9a-44f7-b0c3-788cc0269332.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_044_1851f4b5-af90-419f-bb5e-f621a321f4bd.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_045_9ff32423-85f3-4d94-afdf-b4c52cc77b1d.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_046_65121f10-2dcb-4f2e-8011-ba18153b110e.jpg)
算法的核心是求策略梯度，更新公式为：\(\theta \leftarrow \theta + \alpha \hat{g}\)。
*   **轨迹概率**：\(p(\tau|\theta)\) 可以拆解为策略带来的概率和环境带来的概率。
*   **对数技巧**：将乘积取对数变为求和。\(\log p(\tau|\theta) = \sum_t \log \pi(a_t|s_t) + \sum_t \log P(s_{t+1}|s_t, a_t)\)。
*   **环境梯度为 0**：环境（迷宫）转移概率 \(P\) 与参数 \(\theta\) 无关，求导后为 0。这就是“教练看录像带”的比喻：复盘时只关注球员（Agent）自己的决定，不怪天气（环境）。
*   **Softmax 的导数**：推导结果极其简洁，等于 **One-hot 向量减去概率向量**。
    \(\nabla_\theta \log \pi(a|s) = 1_{[a]} - \pi(\cdot|s)\)
    例如，在某个格子选择了“向右”，概率为 0.25，则“向右”对应的梯度为 \(1 - 0.25 = 0.75\)，其他三个方向为 \(0 - 0.25 = -0.25\)。
*   因此，完整梯度估计公式为：
    \(\hat{g} = \sum_t G_t \nabla_\theta \log \pi(a_t|s_t)\)

## 引入折扣因子与衰减回报
[原片 @ 06:48](https://www.youtube.com/watch?v=SFQWumRFT48&t=408s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_047_d4fbf8c0-dcb1-400f-942b-8fd50a612419.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_048_3b255855-9d76-45d6-86ce-36e03fd31d77.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_049_929da2ad-fb21-439b-95c4-9c96abd7d68e.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_050_aa59d497-f7b1-4539-b371-207c9076603d.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_051_34546b8c-ca55-46d3-8473-c675fe7af574.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_052_e131ff17-6ca8-48a5-afc7-ff2e1c1f51c7.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_053_6c45f255-5d1a-42ea-b195-90147ce3c829.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_054_7b9d864c-1b61-419d-8aba-641b11f7bec7.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_055_e460f5c0-f889-4efb-8c61-ee165b6dffcc.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_056_79d18e22-639b-49d7-8358-1516a784cd18.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_057_c52f8a82-7e74-44fb-857d-3d23fa0e7b61.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_058_d9850428-eb0e-4c2f-87bf-b14647110639.jpg)
如果直接使用整局的回报 \(G_t\)，所有步骤会得到相同的分数（比如赢了都是 +10），这并不合理。越接近宝藏的步骤，贡献应该越大。
*   **引入折扣因子（Discount factor）\(\gamma\)**：通常设为 0.9。
*   **逐步衰减**：某一步的回报 \(G_t = r_{t+1} + \gamma G_{t+1}\)。距离宝藏每前进一步，其功劳就乘以 0.9。
*   **分数表**：例如一局 9 步获胜的游戏，最后一步得 10 分，倒数第二步 \(10 \times 0.9 = 9\) 分，第 1 步可能只有 \(0.9^8 \times 10 \approx 4.30\) 分。
*   **算法核心总结**：通过逆序计算每一步的折扣回报，然后将该返回值作为权重，放大或缩小该步的选择概率。

## 代码实现与 Episode 1 手动推演
[原片 @ 07:54](https://www.youtube.com/watch?v=SFQWumRFT48&t=474s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_059_bc8b5c2a-fbc7-4e10-bc24-08f466121f1e.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_060_56dbe99d-6882-4084-a0fa-7039bf83b3a7.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_061_203eaf4f-d590-48f3-ac41-ab0852c7e45c.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_062_3462a199-1612-4362-84b5-8e6eae9304ca.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_063_ad8582ff-e562-421e-8407-c50c649cadc9.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_064_d7f07a10-5015-4cf6-b7a9-db85741d35a6.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_065_c2527bc9-f2f6-4aac-8529-cd37ca60eabf.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_066_929c6d3e-1673-46af-9ef0-b11e3cd4cea1.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_067_bfbb3ef6-f76d-419e-bfc9-b24c05cb982b.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_068_122faed5-ba8e-4db5-ba3c-aaa595ae1111.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_069_9f394834-2099-4e75-b761-93e297a42581.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_070_dfe7788b-4c24-4ff7-a1e7-ebd4b60e6960.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_071_48d7c0e1-9eb0-44bd-a8ed-774e3dd8ddde.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_072_02eb5ac7-e5b3-41fc-9856-d79670cf4a9d.jpg)
REINFORCE 的代码非常短（约 20 行 Python），分为四个部分：
1.  **采样一局游戏**：Agent 根据概率选择动作，记录下状态、动作和奖励。
2.  **逆序计算得分**：从最后一步开始，计算折扣回报（例如 -5、-4.50、-4.05）。
3.  **计算梯度**：用回报乘以 (One-hot - 概率分布)，得到梯度。
4.  **更新参数**：\(\theta \leftarrow \theta + \alpha \hat{g}\)（学习率 \(\alpha\) 为 0.01）。

**Episode 1 手动推演**：
*   **过程**：向上（Up） -> 向右（Right） -> 向右（Right，但滑倒掉坑）。
*   **逆序得分**：掉坑那步 -5，之前是 -4.50，再之前是 -4.05。
*   **参数更新**：在滑倒前的那个格子，因为选择了向右且游戏失败，其向右的概率被削弱（从 0.25 降到 0.241），其他三个方向概率略微增加。

## 训练过程与结果可视化
[原片 @ 09:18](https://www.youtube.com/watch?v=SFQWumRFT48&t=558s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_073_5e5cfa20-4b13-4759-90af-e9f66d21230a.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_074_7c788e29-ad25-499d-82ed-96e8ecf820d6.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_075_166eb4d3-fc91-402d-a6ae-d04969608cce.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_076_9d207101-b1d2-480e-a438-c50c8db05f87.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_077_d69675a6-95e4-49bd-943f-81d6959178d2.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_078_15e525a7-2ab8-495a-9a11-b96a34ed37e4.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_079_0b5b8f5b-9517-47e1-95f7-05644a7b1454.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_080_af67210b-5471-419e-a269-69c0cc9a3691.jpg)
*   **初期**：Agent 频繁掉坑（画面中满是红叉路径），连续 100 局成功率为 0%。
*   **第 98 回合**：首次出现绿线（成功找到宝藏）。
*   **最终**：经过 5000 回合训练后，Agent 的策略演化为“先去顶部走安全路线”，成功率稳定在 88%-90% 左右，接近理论极限 90.7%。
*   **神奇的涌现**：人类从未告诉 Agent “地板是滑的”或“顶部路线安全”，它完全是通过稀疏的奖励（Returns）自我学习到了这一策略。相比于直接走捷径（短路线成功率仅 64%），算法在探索中发现了最优解。

## 迁移到大型语言模型（LLM）
[原片 @ 10:12](https://www.youtube.com/watch?v=SFQWumRFT48&t=612s)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_081_4f6c98ff-7471-485c-8a3d-4570695f4946.jpg)
![](./Give%20Me%2010%20Minutes,%20I'll%20Make%20REINFORCE%20Click%20Forever/screenshot_082_3d92aa06-5b55-4f80-997b-2f7b0c91b8a6.jpg)
将 REINFORCE 从迷宫迁移到语言模型，只需替换三个概念：
1.  **表格（Table \(\theta\)）\(\rightarrow\) 模型权重（Model's weights）**。
2.  **移动（Action in cell）\(\rightarrow\) 下一个词（Next word / Token）**。
3.  **迷宫（Maze & Reward）\(\rightarrow\) 打分程序（Program that scores the answer）**（例如 RLHF 中的 Reward Model）。
整个训练循环的数学逻辑完全一致。

## AI 总结
本视频深入浅出地讲解了强化学习中最基础的策略梯度算法 **REINFORCE**。视频首先通过一个“地板打滑的迷宫”引入问题，形象地说明了为何需要策略梯度（环境不可控，只能优化策略本身）。接着详细推导了算法的数学原理：通过最大化期望回报，利用对数技巧消除环境转移概率，并推导出极其优美的 Softmax 导数公式（One-hot 减概率）。视频进一步引入折扣因子（\(\gamma\)）来合理分配不同时间步的功劳。最后，通过约 20 行 Python 代码，完整展示了模型从随机乱撞到自主发现“安全长路线”的优化过程，并指出只需替换三个核心概念即可将该算法无缝扩展应用到大型语言模型（LLM）的强化学习对齐中。