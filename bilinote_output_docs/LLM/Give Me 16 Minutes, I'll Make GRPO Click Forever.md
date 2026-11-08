> 来源链接：https://www.youtube.com/watch?v=hWgJ1PpxP2Y

## 目录
- [GRPO 简介与背景](#GRPO-简介与背景)
- [Pit Runner 游戏与策略模型](#Pit-Runner-游戏与策略模型)
- [从 REINFORCE 到 PPO 的演进](#从-REINFORCE-到-PPO-的演进)
- [GRPO 核心机制：用组相对优势替代 Critic](#GRPO-核心机制用组相对优势替代-Critic)
- [GRPO 的数学目标函数](#GRPO-的数学目标函数)
- [一次真实的 GRPO 更新过程演示](#一次真实的-GRPO-更新过程演示)
- [GRPO 训练结果与模型扩展](#GRPO-训练结果与模型扩展)
- [AI 总结](#AI-总结)

## GRPO 简介与背景
[原片 @ 00:00](https://www.youtube.com/watch?v=hWgJ1PpxP2Y&t=0s)
本视频介绍深度解析 **GRPO (Group Relative Policy Optimization)**，这是驱动 **DeepSeek R1** 取得突破的强化学习算法。视频以 DeepSeek 的发布为背景，提及它被称为 AI 的“Sputnik 时刻”。
通过一个名为 **Pit Runner** 的强化学习小游戏，直观展示从零开始构建 GRPO 的全过程，拆解其背后的数学公式和代码实现。

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_000_8a0166a5-57b7-4054-bf09-00647c7f93f9.jpg)

## Pit Runner 游戏与策略模型
[原片 @ 01:07](https://www.youtube.com/watch?v=hWgJ1PpxP2Y&t=67s)
为了让复杂的概念更易懂，视频构建了一个盲盒游戏：
- **游戏规则**：机器玩家需要跨越 40 个格子到达终点旗帜。每步可以“跑”（前进 1 格）或者“跳”（抛硬币决定前进 2 格或 3 格）。如果掉落陷阱，游戏结束。
- **奖励机制**：只有到达终点或掉落陷阱时，才会给出一个最终的分数（跑过的格子数 / 39）。
- **黑盒与状态表示**：玩家不看到整个游戏地图，只能看到前方 1、2、3 格是否有陷阱（1 代表有，0 代表无），以及一个恒为 1 的偏置项。观察向量 \(s\) 包含 4 个数字。

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_001_878b7328-9c52-40c2-94d1-27879a66d5ee.jpg)

**策略网络 (Policy)**：
玩家的决策由一个极简的神经网络决定，本质上是一个 \(4 \times 2\) 的权重矩阵 \(W\)：
- 输入状态 \(s\)（4维向量）与 \(W\) 相乘，得到两个分数（RUN 和 JUMP）。
- 经过 **Softmax** 函数转换为概率。
- 数学表达：\(\pi(\cdot | s) = \text{softmax}(sW)\)。
- 初始状态所有 \(W\) 权重为 0，因此 RUN 和 JUMP 的概率各占一半（0.5）。经过训练后，\(W\) 矩阵的更新将指导玩家在看到前方有陷阱时采取跳跃。

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_002_f40fce60-7393-4f28-887d-3f2306434ba5.jpg)

一个完整的 Episode（回合）包含采样动作、移动、获取新状态的过程，直到游戏结束。系统记录下每步的 `seen`（状态）、`acts`（动作）、`path`（轨迹）以及最终的 `reward`（奖励）。

## 从 REINFORCE 到 PPO 的演进
[原片 @ 03:27](https://www.youtube.com/watch?v=hWgJ1PpxP2Y&t=207s)
GRPO 的构建建立在前人的基础上，分为三个步骤：

**1\. REINFORCE (策略梯度)**
最简单的方法：根据最终的奖励，推高轨迹中每个动作的概率。如果奖励为正，则增大所有动作概率。
**缺陷**：在本游戏中，所有奖励都是正的（至少跑了一格），即使 8 次运行中有 5 次直接掉进第一个坑，REINFORCE 仍然会提高导致掉坑的“走”动作的概率，缺乏对“坏结果”的惩罚。

**2\. PPO (Proximal Policy Optimization)**
PPO 在 REINFORCE 基础上增加了两个关键改进（视频用绿色和琥珀色标注）：
- **优势函数 (Advantage)**：不只是看绝对奖励，而是看“超出预期”的部分。引入一个 **Critic（评论家）** 模型来预测当前状态下的预期得分。优势 = 实际奖励 - 预期得分（\(A_t = R - V_\psi(s_t)\)）。如果在预期很差的关卡中获得了稍高的分数，优势依然可能为正。
- **裁剪机制 (Clip)**：为了充分利用数据，PPO 对同一批数据进行 4 次更新（4 个 epoch）。通过计算新旧策略的比率 \(r_t = \frac{\pi_\theta(a_t|s_t)}{\pi_{old}(a_t|s_t)}\) 并对其实施限制（如 \(0.8\) 到 \(1.2\) 之间），防止更新步子过大，导致策略崩溃。

**PPO 的目标函数**：
\[
 J = \sum_t \min \left( r_t A_t, \text{clip}(r_t, 0.8, 1.2) A_t \right) 
\]

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_003_cb65ff6b-0399-41d2-878e-82ab2976881c.jpg)

## GRPO 核心机制：用组相对优势替代 Critic
[原片 @ 06:00](https://www.youtube.com/watch?v=hWgJ1PpxP2Y&t=360s)
PPO 中由于 Critic 模型的存在，导致了两个严重问题：
**1\. Critic 模型极其庞大**：在 LLM 中，Critic 模型几乎和策略模型（Policy Model）一样大，带来了巨大的内存和计算负担。
**2\. Critic 很难训练**：在语言模型中，通常只有最后一个 Token 能获得奖励，Critic 要准确预测每一个步的预期得分非常困难。
更重要的是，Critic 只能看到局部的信息（如同拿着火把，只能看到前方 3 格），无法区分关卡的难度。例如，简单关卡最差的分数（0.564）甚至高于困难关卡最好的分数（0.282）。这就导致单一的“预期分数”在不同难度关卡下完全失准。

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_004_6fd0308b-a95c-451a-ad5f-76bda37eee3e.jpg)

**GRPO 的核心创新：No Critic！**
GRPO 抛弃了 Critic，采用**同一关卡游玩多次（Group）**的方法来评估难度：
针对同一道题（或者同一个关卡），采样多个回答（如 8 个）组成一个组 (Group)。用组内的平均分作为基准线，完美解决了不同关卡难度不同的问题。
每一场的优势计算公式为：
\[
 \hat{A}_i = \frac{R_i - \text{mean}(R_1, \dots, R_G)}{\text{std}(R_1, \dots, R_G)} 
\]
- \(R_i\)：这条路径的实际奖励。
- \(\text{mean}\)：组内 8 条路径的平均分。
- \(\text{std}\)：组内 8 条路径的标准差（用于归一化）。

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_005_839e7c98-441d-4655-baaf-118bbbaecd05.jpg)

即使所有 8 次都掉坑了（如困难关卡），只要其中一条路径到了第 11 格，而平均分只有 4 格，那么这路径依然会获得正的相对优势（如 +1.11），从而鼓励模型学到“至少比平均跑得远”的策略。

**副作用（Outcome Supervision）**：
因为 GRPO 是结果监督，同一个 group 里同一条轨迹的所有步骤，都共享同一个优势值。这意味着最后那一步抛硬币导致掉坑的决策，也会和前面的好决策一起被鼓励。但好处是，它免除了训练一个庞大的 Critic 模型。

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_006_46b854e6-62cf-4503-86d8-6aa6c424ff07.jpg)

## GRPO 的数学目标函数
[原片 @ 10:06](https://www.youtube.com/watch?v=hWgJ1PpxP2Y&t=606s)
DeepSeekMath 论文中给出的 GRPO 目标函数如下：
\[
 J_{GRPO}(\theta) = \frac{1}{G} \sum_{i=1}^{G} \frac{1}{|o_i|} \sum_{t=1}^{|o_i|} \min \left( \frac{\pi_\theta(o_{i,t}|q, o_{i,<t})}{\pi_{\theta_{old}}(o_{i,t}|q, o_{i,<t})} \hat{A}_{i,t}, \text{clip}\left(\frac{\pi_\theta(o_{i,t}|q, o_{i,<t})}{\pi_{\theta_{old}}(o_{i,t}|q, o_{i,<t})}, 1-\epsilon, 1+\epsilon\right) \hat{A}_{i,t} \right) - \beta D_{KL}(\pi_\theta || \pi_{ref}) 
\]
- **PPO 的比例与裁剪**：保留了 PPO 的 \(r_t\) 和 clip 机制（4个 epoch）。
- **组相对优势**：使用 \(\hat{A}_{i,t}\) 替代了 PPO 中的 Critic 预测的 \(V(s)\)。
- **KL 散度**：一个正则化项，确保模型不会偏离初始模型太远（本游戏演示中为了简化，关闭了该项）。

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_007_9ef78188-9903-45d0-a2aa-5d0a62cdcd70.jpg)

## 一次真实的 GRPO 更新过程演示
[原片 @ 10:54](https://www.youtube.com/watch?v=hWgJ1PpxP2Y&t=654s)
视频详细展示了 200 轮训练中的第 21 轮更新全过程：
**1. 生成数据**：
从种子开始，随机生成了一个包含 9 个陷阱（其中 2 个宽为 2 格）的困难关卡。模型运行 8 次，总共走了 31 步，没有一次到达终点。
**2. 计算优势**：
依照公式计算出组内均值（mean = 0.1955）和标准差（std = 0.0779）。走得最远的第 3 次和第 5 次（到达第 11 格）获得了 +1.11 的优势，而掉在最早陷阱的获得了 -1.19 的优势。
**3. 前向传播（计算概率）**：
以 Run 2 的第 2 步为例，状态 \(s = [1, 0, 0, 1]\)（说明下一格是坑）。用当前权重 \(W\) 计算出的 Logits，经过 softmax 得到 RUN 的概率为 0.152，JUMP 的概率为 0.848。
**4. 计算比率 \(r_t\) 与裁剪**：
在第一次 Pass 中，新旧策略一样，比率 \(r_t = 1\)。但由于 Run 2 的优势是负数（-1.19），其平摊到每一步的系数极小，负面作用导致“RUN”的梯度被推向负值（即减少 RUN 的概率）。
**5. 计算梯度并更新**：
经过 4 次 Pass（Epoch）的循环，权重逐步更新：
- 例如，Run 6 某个朝向陷阱的跳跃动作，超过了裁剪边界（比率跌至 0.743），因此不再更新。
- 第 4 次 Pass 后，矩阵 \(W\) 发生显著变化。比如“前方两格有坑”对应“跳跃”的权重，从 0.379 降到了 0.297（因为跳向坑里是错误的决策）。
- 更新后，模型在“前方两格有坑”时，选择跳跃的概率从原来的 0.848 降到了 0.879（注：此处视频字幕可能存在打字误差，逻辑上是为了增加跳跃概率，视频后续指出策略发生了调整），这是基于优势函数的合理变动。

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_008_9a44c10c-4649-45f4-b11b-a8a83696552a.jpg)

## GRPO 训练结果与模型扩展
[原片 @ 15:30](https://www.youtube.com/watch?v=hWgJ1PpxP2Y&t=930s)
- **策略成功率变化**：在 200 个固定测试集上，经过 200 次迭代，概率从随机盲猜的 0.295 逐步提升到了 0.713（理论最高为 0.724）。模型学会了通过抛硬币的跳跃安全度过陷阱。
- **向大模型迁移**：GRPO 的机制可无缝迁移至语言模型。本游戏中的“关卡”变为“数学题”，“动作轨迹”变为“生成的文字序列”，“游戏得分”变为“是否正确解题”，组大小从 8 直接扩展到了 DeepSeekMath 的 64。
- **DeepSeek-R1-Zero 的惊人成果**：使用该算法在 AIME 2024 数学测试中测试，模型首次尝试的准确率从 15.6% 飙升到了 71.0%。

![](./Give%20Me%2016%20Minutes,%20I'll%20Make%20GRPO%20Click%20Forever/screenshot_009_cc62fdee-815f-4d0b-b898-8f99cf1f7b17.jpg)

## AI 总结
本节视频通过生动、可视化的 **Pit Runner** 小游戏，透彻地拆解了 GRPO（Group Relative Policy Optimization）算法。核心结论如下：
GRPO 继承了 PPO 的核心机制（比率裁剪、多轮策略更新），但精准切中了 PPO 的痛点——用**组内评分对比（Group Relative Advantage）**全面替代了庞大且难以训练的 **Critic 网络**。
通过让模型在同一场景下尝试多次，利用均值和标准差进行归一化，GRPO 彻底解决了在不同难度任务中如何界定“优秀”的问题。这不仅极大降低了训练 LLM 时的显存和算力开销，还在数学推理等任务上展现了强大的自我进化能力，是驱动 DeepSeek-R1 诞生并震惊业界的底层核心算法。