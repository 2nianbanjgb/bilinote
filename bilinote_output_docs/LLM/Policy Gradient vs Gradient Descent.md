> 来源链接：https://www.youtube.com/watch?v=ukCyJY1TOAw&t=5s

## 目录

- 引言：从 PPO 到 Policy Gradient
- 第一步：问题的由来——梯度下降与黑盒函数的碰撞
- 第二步：策略梯度的核心直觉——不优化 $x$，优化生成器
- 第三步：数学推导——如何跨越黑盒的求导障碍
- 数学推导进阶：对数导数技巧与蒙特卡洛估计
- 策略必须随机：为什么 $\sigma=0$ 会导致算法崩溃
- 第四步：代码实现与逐步执行
- 策略梯度的局限性与平滑机制
- 真实场景应用：大语言模型训练与 PPO
- AI 总结

---

## 引言：从 PPO 到 Policy Gradient
[原片 @ 00:00](https://www.youtube.com/watch?v=ukCyJY1TOAw&t=0s)

在学习大语言模型（LLM）的强化学习阶段（RLHF）时，你一定听说过 PPO（Proximal Policy Optimization）。在 OpenAI 2017 年的 PPO 论文中，核心算法正是 **Policy Gradient**。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_000_fa3b211f-1c9b-4558-8c21-a508dc2fa779.jpg)

本视频分为四个步骤彻底讲透 Policy Gradient：
1. **Problem**：函数是黑盒，没有导数。
2. **Intuition**：不直接优化输入，而是优化生成输入的“生成器”。
3. **Math**：四行代数推导得出核心公式。
4. **Code**：15行代码实现，以及在真实大模型（LLM）中的应用。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_001_e03f9e1e-8e02-4fa4-8cc5-a19103908133.jpg)

---

## 第一步：问题的由来——梯度下降与黑盒函数的碰撞
[原片 @ 00:54](https://www.youtube.com/watch?v=ukCyJY1TOAw&t=54s)

通常我们要最小化一个损失函数，最常用的方法是**梯度下降法 (Gradient Descent)**。
假设目标函数为：
\[
f(x) = x^2 + 2x + 1 = (x+1)^2
\]

常规梯度下降算法：
1. 计算导数：\(f'(x) = 2x + 2\)
2. 迭代更新：\(x_{new} = x - \alpha f'(x)\)
从 \(x=3\) 开始，每步学习率 \(\alpha=0.1\)，50步后 \(x\) 到达 \(-1\)（最小值点）。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_002_550f0bce-dce9-4e7c-8504-d71a5d9e1de1.jpg)

**黑盒问题 (The Black Box Problem)**
在现实中，我们面对的往往是**黑盒函数**（如自动驾驶模拟器评分、代码测试通过率、游戏通关状态、LLM 的 Grader 打分）。
你只能输入变量 \(x\) 并获得一个返回值 \(f(x)\)，但**无法获取它的导数**（\(f'(x)\) 不可用）。
梯度下降法遇到了致命瓶颈。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_003_6a28cff6-fcf5-49be-a25d-48c795cde00f.jpg)
![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_004_9421eac2-8615-476f-b5a2-a0df8f5b974f.jpg)

---

## 第二步：策略梯度的核心直觉——不优化 \(x\)，优化生成器
[原片 @ 03:10](https://www.youtube.com/watch?v=ukCyJY1TOAw&t=190s)

既然没法求黑盒 \(f(x)\) 的导数，我们转换思路：**优化生成 \(x\) 的概率分布（采样器）。**

想象一个高尔顿板（Pegboard Game）：
- 球的落点 \(x\) 对应成本 \(f(x)\)。
- 我们无法控制单个球的轨迹。
- 但我们可以控制**漏斗的位置**（即概率分布的均值 \(\mu\)），从而改变大部分球的落点。
- 通过移动漏斗，让球更多地落在“绿色低成本”区域。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_005_451ae7a6-4e46-4da7-b01e-d2a4e1605e68.jpg)

在策略梯度中：
- 我们的“漏斗”是**策略 (Policy)**。
- 我们要优化的是策略的参数 \(\theta\)（例如正态分布的均值 \(\mu\)）。
- 目标函数从原来的 \(f(x)\) 变成了**期望成本 \(J(\mu)\)**：
  \[
J(\mu) = \mathbb{E}_{x \sim p(x|\mu)}[f(x)] = \int p(x|\mu) f(x) dx
\]

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_006_bf0b0a86-ab0f-46fa-941e-ffe808e6d6ef.jpg)

以正态分布 \(N(\mu, \sigma^2)\) 为例（设定 \(\sigma=1\)），通过抽样计算期望成本，我们得到了一条关于 \(\mu\) 的平滑曲线：
\[
J(\mu) = (\mu + 1)^2 + \sigma^2
\]
该曲线在 \(\mu=-1\) 处取得最小值。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_007_ee90b975-ae16-4107-9b03-f78481eff1fb.jpg)

---

## 第三步：数学推导——如何跨越黑盒的求导障碍
[原片 @ 07:59](https://www.youtube.com/watch?v=ukCyJY1TOAw&t=479s)

我们需要计算期望成本对参数 \(\mu\) 的导数：
\[
\frac{dJ}{d\mu} = \frac{d}{d\mu} \int p(x|\mu) f(x) dx
\]

核心目标：**只能对概率密度函数 \(p\) 求导，绝不对黑盒代价函数 \(f\) 求导。**

通过对积分离散化求导以及微积分操作，展开四步核心推导：

1.  \[
\frac{dJ}{d\mu} = \frac{d}{d\mu} \int p(x|\mu) f(x) dx
\]
2.  将导数移入积分号，由于对于固定的 \(x\)，\(f(x)\) 没有 \(\mu\) 变量，因此只对 \(p(x|\mu)\) 求导：
    \[
= \int f(x) \frac{\partial p(x|\mu)}{\partial \mu} dx
\]
    ![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_008_72dffeb4-cc5f-46c2-822a-72039c69c617.jpg) （通过将积分视为求和，证明 \(f(x)\) 是常数，其导数为 0）
3.  使用“对数导数技巧 (Log-derivative trick)”。利用 \(\frac{\partial p}{\partial \mu} = p \cdot \frac{\partial \log p}{\partial \mu}\)，将 \(p\) 重新放回积分项前：
    \[
= \int p(x|\mu) f(x) \frac{\partial \log p(x|\mu)}{\partial \mu} dx
\]
4.  利用蒙特卡洛方法 (Monte Carlo) 将积分转化为采样的平均值：
    \[
\approx \frac{1}{N} \sum_{i=1}^N f(x_i) \frac{\partial \log p(x_i|\mu)}{\partial \mu}
\]
    其中 \(x_i \sim p(x|\mu)\)。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_009_3d7512ee-3cf5-4bfd-9c7e-489861546f99.jpg) （完整四行推导）

---

## 数学推导进阶：对数导数技巧与蒙特卡洛估计
[原片 @ 13:24](https://www.youtube.com/watch?v=ukCyJY1TOAw&t=804s)

**对数导数技巧 (Log-derivative trick)**：
利用链式法则 \(\frac{\partial \log p}{\partial \mu} = \frac{1}{p}\frac{\partial p}{\partial \mu}\)，从而有 \(\frac{\partial p}{\partial \mu} = p \frac{\partial \log p}{\partial \mu}\)。这让 \(p\) 重新回到前沿，使积分再次变为可以被采样的期望形式。

**策略梯度的最终公式**：
对于正态分布，\(\frac{\partial \log p(x|\mu)}{\partial \mu} = \frac{x-\mu}{\sigma^2}\)。
当 \(\sigma=1\) 时，该导数即为 \(x-\mu\)。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_010_db4bcf30-b923-4d41-b65f-e16c3648555f.jpg)

这个导数有何物理意义？
- 如果采样点 \(x\) 大于均值 \(\mu\)，梯度为正，更新时 \(\mu \leftarrow \mu - \alpha \hat{g}\) 会让 \(\mu\) 向 \(x\) 移动（使该点更可能被抽到）。
- 如果 \(x\) 对应的 \(f(x)\) 越大（成本越高），乘上正梯度后更新幅度就越大，\(\mu\) 会大幅远离这个高成本点。
- 反之，低成本的采样点会温和地拉动 \(\mu\) 靠近它。
- 整个过程，**从未对黑盒 \(f(x)\) 求导**。

---

## 策略必须随机：为什么 \(\sigma=0\) 会导致算法崩溃
[原片 @ 16:03](https://www.youtube.com/watch?v=ukCyJY1TOAw&t=963s)

如果我们将策略中的 \(\sigma\) 设置为 0，会发生什么？
- 采样出的所有 \(x\) 都刚好等于 \(\mu\)。
- 期望成本 \(J(\mu)\) 直接塌缩为黑盒函数本身 \(J(\mu) = f(\mu)\)。
- 此时，我们需要 \(\mu\) 的导数，而这正是黑盒给不了的 \(f'(\mu)\)。
- 公式中的梯度项 \(\frac{x-\mu}{\sigma^2}\) 会发生**除以零**的报错。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_011_0206681e-e7a1-4df6-9245-1f3d7d96ad3f.jpg)
![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_012_2b67c7b5-d876-4a95-a540-d83723ac3632.jpg)

**结论：策略必须具有随机性（Stochastic）**。分布的“发散度（Spread）”是我们获得可求导信息的唯一来源。即使对于不连续的函数（如阶跃函数），只要分布够宽，采样平均也能平滑出一条可用于优化的坡度。

---

## 第四步：代码实现与逐步执行
[原片 @ 18:06](https://www.youtube.com/watch?v=ukCyJY1TOAw&t=1086s)

使用 Python 实现核心循环（共 15 行左右）：
- 采样5个 \(x\)
- 评估损失 \(f(x)\)
- 计算梯度估计 \(\hat{g} = \frac{1}{N} \sum f(x_i) \frac{x_i - \mu}{\sigma^2}\)
- 更新 \(\mu\) 和 \(\alpha\)

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_013_e0d98ea1-b902-46f8-a03f-b8a00444ca7a.jpg)

**手工推导 5 个样本（Batch Size = 5）**：
- 采样 5 个 \(x\) 值（如 3.12, 2.86, 3.64...）
- 计算对应损失值（如 17.02, 14.96...）
- 计算采样器导数 \(x_i - \mu\)
- 计算乘积 \(f(x_i) \cdot (x_i - \mu)\)，总和约为 \(+1.858\)（正值）
- 更新 \(\mu \leftarrow \mu - \alpha \cdot (+1.858)\)，\(\mu\) 从 3.0 开始下降。
- 学习率 \(\alpha\) 随着步数衰减。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_014_603a5e3c-3673-473d-bb8a-414e6c117ed1.jpg)

跑完 5000 步后，\(\mu\) 从 3.0 逐渐收敛到 -1.00155，精准逼近真实的函数最小值。
![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_015_119b7e37-17c5-44d0-86c2-b0cfd1e57224.jpg)

---

## 策略梯度的局限性与平滑机制
[原片 @ 21:12](https://www.youtube.com/watch?v=ukCyJY1TOAw&t=1272s)

Policy Gradient 能否优化任何函数？
**答：不能。** 
它优化的是“期望成本”，即黑盒函数被采样器“平滑”后的版本（Smoothing）。
- **尖锐的角 (Kink)**：会被平滑成碗状，仍能找到最低点。
- **阶跃函数 (Step)**：会被平滑成缓坡，仍能指引更新方向。
- **针孔形的极小值 (Needle)**：如果极小值区域比采样的跨度还要窄，采样将基本抓不到这个点，平滑后该极小值几乎消失，算法无法收敛到这里。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_016_f1291396-850c-4976-a33a-59b5d85dc27f.jpg) （结合图理解）
![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_017_ee289fec-9fed-4070-9c9e-519410a04f3b.jpg) （平滑图对比）

---

## 真实场景应用：大语言模型训练与 PPO
[原片 @ 23:00](https://www.youtube.com/watch?v=ukCyJY1TOAw&t=1380s)

大语言模型（LLM）的强化学习完美映射了刚才的玩具模型：
- **漏斗中心 \(\mu\)** \(\rightarrow\) LLM 的 **Weights (权重参数)**
- **高斯生成分布 \(N(\mu, \sigma^2)\)** \(\rightarrow\) 根据词表概率生成的 **Softmax 采样**
- **生成的标量 \(x\)** \(\rightarrow\) 生成的 **一段文本答案**
- **黑盒函数 \(f(x)\)** \(\rightarrow\) 外部或内部训练的 **Grader (评分器)**
- **成本 \(f(x)\)** \(\rightarrow\) 奖励得分 **Reward**（注意：优化目标从“减成本”变成了“加奖励”，符号需要翻转）

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_018_c1ea1afd-3736-4e21-aac1-a599ecc3baf1.jpg)

在 OpenAI 2017 年提出的 PPO 算法中，就是使用相同的四行公式，将 LLM 的数十亿个权重参数作为 \(\mu\) 进行更新优化。

![](./Policy%20Gradient%20vs%20Gradient%20Descent/screenshot_019_f18591ca-6bc1-4337-882a-13b0dd3cabc5.jpg)

---

## AI 总结

本视频通过极简的数学公式和直观的示例，揭示了强化学习（如 PPO 算法）中 Policy Gradient 的核心原理。当面对无法求导的黑盒函数时，策略梯度通过引入一个参数化的概率分布（Policy），将“直接求导”转化为“对采样结果的期望求导”。利用对数导数技巧和蒙特卡洛估计，我们证明了仅依靠黑盒返回的数值即可反向传播更新策略的参数（如均值）。该公式（\(\hat{g} = \frac{1}{N}\sum f(x_i)\nabla_\mu \log p(x_i|\mu)\)）正是基于 Reward 微调 LLM 等现代大模型算法的基石所在。