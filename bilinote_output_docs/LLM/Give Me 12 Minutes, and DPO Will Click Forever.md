> 来源链接：https://www.youtube.com/watch?v=y2aBgSgbsIk

## 目录
- [引言与目标](#引言与目标)
- [核心问题与偏好数据](#核心问题与偏好数据)
- [传统解法：RLHF](#传统解法-rlhf)
  - [阶段一：训练奖励模型](#阶段一训练奖励模型)
  - [阶段二：强化学习微调策略](#阶段二强化学习微调策略)
- [RLHF 的痛点](#rlhf-的痛点)
- [DPO 的核心思想](#dpo-的核心思想)
  - [朴素的自奖励模型](#朴素的自奖励模型)
  - [隐式奖励推导](#隐式奖励推导)
  - [DPO 损失函数](#dpo-损失函数)
- [DPO 的实现与结果](#dpo-的实现与结果)
  - [梯度更新逻辑](#梯度更新逻辑)
  - [代码实现与实验对比](#代码实现与实验对比)
- [模型扩展与局限性](#模型扩展与局限性)
- [AI 总结](#ai-总结)

## 引言与目标
[原片 @ 00:00](https://www.youtube.com/watch?v=y2aBgSgbsIk&t=0s)
- 视频用 12 分钟深入解析 DPO（Direct Preference Optimization，直接偏好优化）。
- 目标：理解整个推导过程，了解为什么偏好训练以前需要奖励模型和强化学习循环，而 DPO 如何用一个损失函数取代它们，并在代码中逐步运行。

## 核心问题与偏好数据
[原片 @ 00:38](https://www.youtube.com/watch?v=y2aBgSgbsIk&t=38s)
- **示例问题**：如何用 Python 反转一个列表（`How do I reverse a list in Python?`）。
- **四种回复**：正确的（right）、闲聊的（chatty）、错误的（wrong）、拒绝回答的（refuse）。
- **初始概率**：目前 chatbot 选择“正确”回复的概率是 0.20。
- **训练目标**：通过偏好训练将该概率提升至 0.911。
- **迷你模型**：一个仅有 4 个参数的模型（对应四种回复），通过 softmax 转化为概率。
- **参考模型（Reference Model, \(\pi_{ref}\)）**：带有偏好训练前初始参数的冻洁模型（在真实流程中，通常是 SFT 模型）。
- **偏好数据**：收集用户偏好对，即问题 \(x\)、偏好的回复 \(y_w\) 和被拒绝的回复 \(y_l\)。假设收集了 1000 对。

## 传统解法：RLHF
[原片 @ 02:05](https://www.youtube.com/watch?v=y2aBgSgbsIk&t=125s)
- RLHF（Reinforcement Learning from Human Feedback）通常分为两个高成本阶段。
- **阶段一：训练奖励模型（Reward Model）**
  - 将偏好数据转化为分数。类似于 Elo 积分：每回合赢家加分，输家扣分。
  - 使用 **Bradley-Terry 模型**，用户偏好胜者的概率为：
    \[
P(y_w > y_l) = \sigma(r(y_w) - r(y_l))
\]
    其中 \(\sigma\) 是 sigmoid 函数。
  - **损失函数**：最大似然估计，取负对数：
    \[
\mathcal{L}_{RM} = -\mathbb{E}_{(x, y_w, y_l) \sim D} \left[ \log \sigma(r(y_w) - r(y_l)) \right]
\]
  - 在示例中，损失从 0.693 降到 0.478。经过拟合，获胜回复（right）的分数最高。

- **阶段二：强化学习微调（RL Loop）**
  - 目标是最大化奖励减去 KL 散度惩罚：
    \[
\max_{\pi_\theta} \mathbb{E}_{y \sim \pi_\theta(y|x)} \left[ r(y) \right] - \beta \text{KL}(\pi_\theta(y|x) || \pi_{ref}(y|x))
\]
  - 第一项奖励高分，第二项惩罚偏离参考模型，\(\beta\) 控制权衡。
  - 在示例中，如果全押“正确”回复，奖励为 2.0，惩罚为 0.80，净值 1.20；最佳权衡是概率 0.911，净值 1.24。
  - RLHF 需要用 PPO 等算法进行采样探索，比如采样 48,000 个回复，最终达到目标。

## RLHF 的痛点
[原片 @ 04:47](https://www.youtube.com/watch?v=y2aBgSgbsIk&t=287s)
- 复杂度高：涉及多个模型（策略模型、参考模型、奖励模型、价值模型）。
- 计算成本巨大：需要在训练循环中不断采样生成新回复来打分。
- 论文指出：RLHF 比监督学习复杂得多，而 Meta 的 Llama 3 论文甚至发现 DPO 消耗更少计算资源且表现更好。

## DPO 的核心思想
[原片 @ 05:50](https://www.youtube.com/watch?v=y2aBgSgbsIk&t=350s)
- **目标**：通过直接在存储的偏好对（静态 pairs）上计算一个损失函数，得到与 RLHF 相同的模型，无需奖励模型，也无需采样。
- **核心点子**：让 chatbot 自己成为奖励模型。

### 朴素的自奖励模型
- **朴素方法及其缺陷**：用模型自身的对数概率 \(\log \pi_\theta(y)\) 作为奖励，直接套用 Bradley-Terry 损失。结果虽然拟合了偏好数据（损失降至 0.478），但“正确”回复的概率仅达到 0.75，未达到 RLHF 的 0.911。原因是没有引入 KL 惩罚来约束模型偏离参考模型的程度。

### 隐式奖励推导
[原片 @ 07:24](https://www.youtube.com/watch?v=y2aBgSgbsIk&t=444s)
- 此时推导开始：从 RLHF 的目标函数中找到最优策略的闭式解。
- 已知 RLHF 目标的最优 chatbot 形式为：
  \[
\pi^*(y) \propto \pi_{ref}(y) e^{r(y)/\beta}
\]
- 反向解出奖励 \(r(y)\)：
  \[
r(y) = \beta \log \frac{\pi_\theta(y)}{\pi_{ref}(y)} + C
\]
  其中 \(C\) 是常数，在计算胜负差时会抵消。
- **结论**：chatbot 的隐式奖励（Implicit Reward）由它与参考模型的对数概率比值决定。

### DPO 损失函数
[原片 @ 08:18](https://www.youtube.com/watch?v=y2aBgSgbsIk&t=498s)
- 将隐式奖励代入 Bradley-Terry 模型，得到 DPO 损失：
  \[
\mathcal{L}_{DPO}(\theta) = -\mathbb{E}_{(x, y_w, y_l) \sim D} \left[ \log \sigma \left( \beta \log \frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \beta \log \frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)} \right) \right]
\]
- 优化 DPO 损失同样能推高胜者压低败者，且无需采样。

![](./Give%20Me%2012%20Minutes,%20and%20DPO%20Will%20Click%20Forever/screenshot_000_207891ea-e5e8-4b66-a966-ed496ad0dcc3.jpg)

## DPO 的实现与结果
[原片 @ 08:45](https://www.youtube.com/watch?v=y2aBgSgbsIk&t=525s)
- **梯度更新逻辑**：
  - 需要计算损失对参数 \(\theta\) 的梯度。
  - 链式法则给出三部分：损失随间隔（Margin）的变化量（\(-\sigma(-M)\)）、间隔随参数的变化量（\(\beta \times (\text{winner direction} - \text{loser direction})\)）。
  - 组合后，每个偏好对都以权重 \(\sigma(-M)\) 推高胜者、压低败者。如果模型还是排错，权重很大；排对了，权重变小。

- **代码实现过程**：
  - 初始化参数 \(\theta\) 复制自参考模型，此时所有 margin 为 0，权重为 0.5。
  - 先跑一步：更新后，“right”概率从 0.20 升至 0.236。
  - 跑 300 步：损失降至 0.478，与 RLHF 的奖励模型损失一致。

- **结果对比**：
  - RLHF 采样了 48,000 个回复；DPO 采样 0 个。
  - 两者最终让“right”回复的概率达到 **0.911**。
  - 论文标题一语道破：“Your language model is secretly a reward model”。DPO 中原本虚幻的隐式奖励，对齐后与 RLHF 拟合出的真实奖励极其接近。

![](./Give%20Me%2012%20Minutes,%20and%20DPO%20Will%20Click%20Forever/screenshot_001_e05b1cc4-a80f-4b34-9fb8-2c60c056ef0c.jpg)

## 模型扩展与局限性
[原片 @ 10:55](https://www.youtube.com/watch?v=y2aBgSgbsIk&t=655s)
- **规模扩展**：在真实 LLM 中，4 个数字变成数十亿权重，回复的概率变成所有 token 概率的对数之和：
  \[
\log \pi_\theta(\text{reply}) = \sum_j \log \pi_\theta(\text{token}_j \mid \text{question}, \text{previous tokens})
\]
- **局限性**：DPO 只能从静态存储的预先收集好的 pairs 中学习（Offline）；而 RLHF 能不断给新生成的回复打分（Online）。何时更优因任务而异。

![](./Give%20Me%2012%20Minutes,%20and%20DPO%20Will%20Click%20Forever/screenshot_002_aebe9e23-9130-4b8c-a129-1e7905eee5a2.jpg)
![](./Give%20Me%2012%20Minutes,%20and%20DPO%20Will%20Click%20Forever/screenshot_003_cf2eb7e5-2893-48aa-bdda-e3595781903b.jpg)

## AI 总结
本视频通过一个简化的 4 答案示例，讲述了从 RLHF 中繁杂的“奖励模型+RL 采样”到 DPO“单损失函数训练”的演进。核心在于数学推导表明，使用 **DPO 损失**——即模型与参考模型的对数概率差（隐式奖励）代入 Bradley-Terry 模型——仅需计算静态数据对，就能绕过奖励模型和强化学习过程，直接以梯度下降方式更新模型。实验中，DPO 无需任何采样，最终效果与需要 48,000 次采样的 RLHF 完全一致，展现出极其高效的特性。