> 来源链接：https://www.youtube.com/watch?v=Dy5KiEXlSUs

## 目录

- [CartPole 游戏机制](#cartpole-游戏机制)
- [PPO 算法背景](#ppo-算法背景)
- [CartPole 状态与物理模拟](#cartpole-状态与物理模拟)
- [从 REINFORCE 到 PPO 的三个改进](#从-reinforce-到-ppo-的三个改进)
- [PPO 核心组件详解](#ppo-核心组件详解)
- [策略网络与游戏过程](#策略网络与游戏过程)
- [折扣回报计算](#折扣回报计算)
- [PPO 第一项：Advantage（优势函数）](#ppo-第一项advantage优势函数)
- [预测模型（Linear Regression）](#预测模型linear-regression)
- [PPO 第二项：Importance Ratio（重要性比率）](#ppo-第二项importance-ratio重要性比率)
- [PPO 第三项：Clipped Surrogate Objective（裁剪）](#ppo-第三项clipped-surrogate-objective裁剪)
- [PPO 代码实现 - 单次更新](#ppo-代码实现---单次更新)
- [最终训练结果与 GPT 扩展](#最终训练结果与-gpt-扩展)
- [AI 总结](#ai-总结)

---

## CartPole 游戏机制
[原片 @ 00:00](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=0s)

本视频以 CartPole（倒立摆）游戏为例，详细拆解了 PPO（Proximal Policy Optimization）算法的全部工程与数学细节，目标是利用约 20 行 Python 代码实现并通过 19 分钟的学习让读者彻底理解 PPO 的运行原理。

在 CartPole 中，智能体（Agent）通过向左或向右推动小车来保持杆子直立。
- 动作空间：向左推（Push left）或向右推（Push right）。
- 奖励机制：每保持一步杆子直立，获得 1 分（\(+1\)）。
- 结束条件：杆子倾斜超过 \(12^\circ\)，或小车偏离轨道范围（左右各 2.4 米），或达到 500 步上限（此上限用于训练时的停止条件）。

视频首先展示了 PPO 训练过程中的 7 个片段（同时播放）：
最开始游戏只能坚持 8 步就失败；随着训练进行，能坚持 100 步、几百步，但最终依然会失败；而完成训练的策略（Finished policy）能坚持超过 500 步，不再倒下。PPO 算法正是将 GPT-3 转化为 ChatGPT 的强化学习核心算法。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_000_dc4fa795-acf1-4882-ac58-95f6e1366ab0.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_001_bda74852-d3aa-43e8-b1c9-75cc48dc61ba.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_002_b8370d23-c158-4f41-99a7-64fe8e2da34e.jpg)

## PPO 算法背景
[原片 @ 00:38](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=38s)

PPO 算法出自 OpenAI 在 2017 年发表的论文《Proximal Policy Optimization Algorithms》。这个算法将复杂的强化学习问题浓缩成一个核心公式，本视频将从零开始构建公式中的每一个部分，并用代码实现它。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_003_c0742930-9485-41f2-b05c-99326ca2134e.jpg)

## CartPole 状态与物理模拟
[原片 @ 01:17](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=77s)

CartPole 的虚拟世界由 4 个数字表示：
1. \(x\)：小车在轨道上的位置
2. \(\dot{x}\)：小车的速度
3. \(\theta\)：杆子的倾斜角度
4. \(\dot{\theta}\)：杆子倾斜的角速度

在代码中，`step` 函数负责执行物理模拟：
- 第一，对小车施加向左或向右的 10 牛顿力。
- 第二，运行 1/50 秒（0.02秒）的物理模拟。
- 第三，返回 1 点奖励并判断游戏是否结束。

**核心物理原理**：重力会将杆子拉下，而智能体施加的推力是唯一能将其拉回的力量。每一步，智能体接收 4 个状态数、1 个奖励和是否结束的信号，然后必须选择向左推还是向右推。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_004_44567df4-c408-41de-a230-1520c2f5a308.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_005_80678c64-4fcc-4d2b-a3a5-eea35fc3f357.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_006_399cccf6-9282-4ad5-9fba-e57550e05a6d.jpg)

游戏代码中物理方程的核心思想是：
\[
 \ddot{\theta} = \frac{g \sin\theta - \cos\theta \frac{F + m_p l \dot{\theta}^2 \sin\theta}{m_c + m_p}}{l \left( \frac{4}{3} - \frac{m_p \cos^2\theta}{m_c + m_p} \right)} 
\]
其中 \(F\) 是推力，\(m_c\) 是小车质量，\(m_p\) 是杆子质量，\(l\) 是杆子长度。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_007_e89e1870-9a09-42cf-96f1-8171bbf039ee.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_008_3ddbb5de-f2d9-4217-9ddb-fa8cf946f216.jpg)

## 从 REINFORCE 到 PPO 的三个改进
[原片 @ 02:36](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=156s)

PPO 建立在一个较早的强化学习算法 REINFORCE 之上。REINFORCE 的核心思想是：玩一局游戏，通过计算动作后所有点的总和来为每个动作打分，然后根据得分改变动作的概率。

REINFORCE 的核心公式为：
\[
 G_t = r_{t+1} + \gamma G_{t+1} 
\]
\[
 \hat{g} = \sum_t G_t \nabla_\theta \log \pi(a_t | s_t) 
\]
\[
 \theta \leftarrow \theta + \alpha \hat{g} 
\]

PPO 在 REINFORCE 的基础上增加了 **三个关键修改**，使训练更加稳定：
1.  **计算优势（Advantage）**：比较当前动作的得分与通常状态下得分的差异，减少方差。
2.  **复用经验（Importance Ratio）**：通过重要性权重，多次利用同一批数据（Epochs），提高数据效率。
3.  **梯度裁剪（Clip）**：限制策略更新的幅度，防止单批次数据导致策略过度学习。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_009_5dbead4f-b8cc-40e2-83fe-a888959a6b58.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_010_5f74c9b8-b766-4c91-981d-f81e7a08ad0b.jpg)

## PPO 核心组件详解
[原片 @ 03:10](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=190s)

### 优势（Advantage）
在更新策略时，如果某次测试得分是 90 分，但平均分只有 85 分，那么 90 分是好成绩；如果平均分是 95 分，则 90 分是差成绩。通过比较动作的得分与当前状态下的平均分，我们可以判断动作的相对好坏。公式为 \(A_t = G_t - V(s_t)\)。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_011_ab845ae4-22d2-4507-a92f-c9aa61640824.jpg)

### 重要性比率（Importance Ratio）
为了避免浪费游戏数据，我们可以多次使用同一批游戏数据进行训练（称为 Epochs）。就像复习练习题，多轮复习能加深记忆。由于多次更新会导致策略改变，旧动作在当前策略下的概率发生变化。
这时引入重要性比率：\(r_t(\theta) = \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{old}}(a_t|s_t)}\)。
如果策略已经不再倾向于某个动作（已改正的错误），该比率就会降低，从而减少该动作对更新的影响。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_012_220dc944-7154-4ee1-9ba7-194351a89a6b.jpg)

### 裁剪（Clip）
如果无限次地使用同一批数据进行训练（例如 40 个 Epoch），策略会在旧的知识上过度自信（过拟合），导致在新状态下表现不佳。引入裁剪（Clip），限制重要性比率的变化范围（如 \(1 \pm \epsilon\)，通常 \(\epsilon=0.2\)）。
一旦比率超过 \(1.2\)（奖励上限）或低于 \(0.8\)（惩罚下限），梯度就会被截断为零，防止策略过度更新。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_013_ef86ee07-7a11-46e7-b998-f2c9e64280bc.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_014_e65a9b87-8ccd-4286-8ad3-bb2f24f2dbde.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_015_d0b1360f-3ade-4ed0-b3e9-ecd169dc8a42.jpg)

## 策略网络与游戏过程
[原片 @ 04:12](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=252s)

PPO 使用的最简单的策略网络是一个单层神经网络（即一个矩阵），输入 4 个状态数字，输出 2 个动作的得分。
初始时所有权重为 0，此时策略输出向左和向右的概率各为 \(0.5\)（通过 Softmax 函数获得）。

游戏过程（Episode）：
在一局游戏中，智能体根据概率选择动作，环境返回新的状态和奖励，直到杆子倒下或达到 500 步。我们需要记录这三个信息：
1.  每一步的状态 \(S\)
2.  选择的动作 \(A\)
3.  收到的奖励 \(R\)

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_016_05c58646-f47c-4c1a-92ab-c1708e842d52.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_017_00596d5f-93a2-4fc1-8c0b-7705f102bf23.jpg)

## 折扣回报计算
[原片 @ 05:48](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=348s)

为了计算每个动作的得分，我们使用折扣回报（Discounted Return）：
\[
 G_t = r_{t+1} + \gamma G_{t+1} 
\]
其中折扣因子 \(\gamma = 0.99\)。这意味着未来的奖励具有递减的价值，距离当前动作越远的奖励，对当前决策的影响越小。例如，一局 113 步的游戏，第一步的得分为 67.88，最后一步的得分仅为 1。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_018_67964d2a-9db0-400b-8894-68aff2a1aad2.jpg)

## PPO 第一项：Advantage（优势函数）
[原片 @ 06:06](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=366s)

在 REINFORCE 中，优势就是动作的绝对得分。但这存在问题：有时候动作虽然导致游戏结束，但因为它是在杆子即将倒下时做出的，得分依然为正（因为前面积累了很多分）。

我们需要一个**相对的评价**：减去该状态下的预期得分（基线）。公式为：
\[
 A_t = G_t - V(s_t) 
\]
- \(G_t\)：实际获得的得分。
- \(V(s_t)\)：模型预测的在当前状态下通常能获得的分数。

这样，如果动作导致游戏失败（实际得分低于预期），优势值就为负，即使绝对得分为正。通过这种方式，PPO 能真正区分动作的好坏。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_019_074d0d3a-e629-498c-a168-1104de5d5024.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_020_e40b780e-982f-4c7b-9283-6886282aa419.jpg)

## 预测模型（Linear Regression）
[原片 @ 09:24](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=564s)

预测模型 \(V(s)\) 可以是一个简单的线性回归模型。不需要神经网络，任何能预测分数的模型都可以。

模型公式：
\[
 V(s) = v_1|x| + v_2|\dot{x}| + v_3|\theta| + v_4|\dot{\theta}| + v_5 
\]
其中 \(v_i\) 是权重。我们需要学习这些参数。游戏稳定时，预期得分大约为 57；接近边缘时，预期得分大约为 36。
在代码中，这通过矩阵运算实现，通过梯度下降来更新权重，使预测值更接近实际得分。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_021_a8aa7d04-310f-4f70-8135-0b566473f8ca.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_022_6c306bf5-a4b0-4302-aa87-a4977daae717.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_023_e747bfc5-30ed-4cb6-ad77-9f765f784d86.jpg)

## PPO 第二项：Importance Ratio（重要性比率）
[原片 @ 12:01](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=721s)

为了解决数据复用的问题，PPO 引入了 **Epochs**（多轮训练）。例如，每批数据可以在策略更新时使用 4 次。

但更新后的策略已经不同于生成数据时的旧策略，因此需要引入重要性比率（Importance Ratio）：
\[
 r_t(\theta) = \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{old}}(a_t|s_t)} 
\]
如果当前策略对某个动作的概率远低于旧策略（说明策略已经发生了改变，不再倾向于这个动作），该比率就会降低。
计算公式为：
\[
 \text{权重} = r_t \times A_t 
\]
在第一个 Epoch 之前，所有比率均为 1。每次 Epoch 更新后，比率会发生变化。例如，某个动作的概率从 \(0.167\) 下降到 \(0.091\)，则比率为 \(0.546\)，其优势值也会相应缩小。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_024_6f7b1c0c-2c5c-4a34-80df-ef283d3332d5.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_025_1d90cbe0-313e-4f7f-9d7e-aaba1e112495.jpg)

## PPO 第三项：Clipped Surrogate Objective（裁剪）
[原片 @ 14:12](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=852s)

如果依赖于旧的游戏数据（Old Map）更新太多次，策略可能会对新情况反应过度。就好像用旧的股市新闻过度交易一样，过度自信会导致灾难性的失败。
因此，PPO 强制限定了更新的幅度。使用代理目标函数（Surrogate Objective）：
\[
 L^{CLIP}(\theta) = \hat{E}_t \left[ \min \left( r_t(\theta)\hat{A}_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon)\hat{A}_t \right) \right] 
\]
其中 \(\epsilon = 0.2\)。
- 如果某个动作表现比预期好（\(\hat{A}_t > 0\)），当比率超过 \(1.2\) 时，目标值不再增加（平顶）。
- 如果动作表现比预期差（\(\hat{A}_t < 0\)），当比率低于 \(0.8\) 时，目标值不再下降（平底）。

**关键理解**：如果一个动作被截断（Clipped），它在这次 Epoch 中不会产生梯度（梯度为 0）。换句话说，这个动作对更新没有任何贡献，从而保证了单次更新对策略的改变是有限的。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_026_c928d979-6394-45f8-b76c-28a7b1f250f7.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_027_ca96d501-4780-45f9-8f53-edf50f21f010.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_028_5272efe9-06f0-4587-8905-9660d3e8a70f.jpg)

## PPO 代码实现 - 单次更新
[原片 @ 16:36](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=996s)

实现整个 PPO 更新循环的四大部分代码如下：
1.  **玩 5 局游戏**并记录每一步的 \(S, A, G\)。
2.  **计算优势函数**。输入 \(S\)，计算预测值 \(V(s)\)，并计算 \(A = G - V\)。
3.  **在相同数据上训练 4 个 Epoch**。计算策略概率，获取重要性比率 \(r_t\)，应用裁剪（Clip），计算梯度并更新权重。
4.  **训练预测器**。用实际得分 \(G\) 更新线性回归权重 \(v\)，使其预测更准确。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_029_5228d459-9c2f-4ca2-b4c8-3ea036fc1f1e.jpg)

通过执行代码展开查看单次更新的细节：
- 玩 5 局游戏（分别 113, 172, 194, 108, 173 步），最后几局因杆子倒下而结束。
- 计算奖励（最后一步步长很小）。
- 计算优势（例如第 1 步的前几步优势为正，最后的几步优势为负，且负值较大）。
- 使用 4 个 Epoch 更新权重。在更新过程中，某些动作的比率会超出范围，从而被截断（梯度置为零），导致部分权重不再更新。
- 用实际得分重新拟合预测器的权重。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_030_f5b22b91-831a-4b82-934e-8f21e5aa6603.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_031_55cdb6a8-8c62-41e2-be23-dab582912e31.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_032_1498ccec-e6d9-432e-9e06-3384b683b701.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_033_9316143b-6889-47da-a8eb-d5d1ba6af37d.jpg)

## 最终训练结果与 GPT 扩展
[原片 @ 18:30](https://www.youtube.com/watch?v=Dy5KiEXlSUs&t=1110s)

执行完整的 400 次更新（2000 局游戏）：
- 训练初期，游戏很快就失败（甚至游戏刚开始就结束）。
- 后期逐渐稳定，到第 2000 局游戏时，智能体平均能坚持 473 步（超过了 500 步中的大部分时间），大幅超越了随机推车（平均 22 步）的基线。
- 通过 Tensorboard 曲线可以看到，策略更新后性能保持稳定，持续处于高分水平。

**从 CartPole 到 GPT（ChatGPT）的三个替换**：
1.  我们的 8 个权重参数扩展为语言模型的数十亿个参数。
2.  控制推车向左/向右的动作替换为预测下一个词。
3.  环境和物理规则（CartPole）替换为一个评估模型（Reward Model），用于对语言模型的生成答案进行打分。

![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_034_7468ce0b-8a5a-4b1b-9998-68822b3063a9.jpg)
![](./Give%20Me%2019%20Minutes,%20I'll%20Make%20PPO%20Click%20Forever/screenshot_035_9c94eded-7bc3-402d-a932-548c3d168169.jpg)

## AI 总结

PPO 是强化学习历史上最具影响力的算法之一，它的核心贡献是让策略优化过程**稳定**且**高效**。本视频通过从头实现一个 CartPole 智能体，清晰地拆解了 PPO 的三大核心模块：

1. **Advantage（优势函数）**：用实际得分减去预测基线，让模型能分辨出“相对的好”与“绝对的坏”。
2. **Importance Ratio（重要性比率 / Epochs）**：用数学方法评估当前策略与旧策略的差异，从而允许模型对旧数据进行多次学习，显着提升了数据利用率。
3. **Clipping（裁剪）**：通过限制比率的更新范围，防止模型在有限的旧数据上过度拟合。当动作的概率变化超过 20% 阈值时，截断梯度，从而极大地提升了训练的容错能力。

视频后半段展示了该算法从代码到实现的全过程：通过简单的线性回归模型预测奖励，并在每一轮迭代中执行“预测-比较-更新”的闭环。最后，视频指出，将这一套机制中的“动作/状态”替换为“词汇/上下文”，并将环境替换为“评分模型”，就是我们从 GPT-3 走向 ChatGPT 所应用的核心思路。