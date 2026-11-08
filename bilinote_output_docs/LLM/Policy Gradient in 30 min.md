> 来源链接：https://www.youtube.com/watch?v=26j1Cn8AECs

## 目录

- [核心问题：黑盒奖励无法反向传播](#核心问题黑盒奖励无法反向传播)
- [将问题映射到大型语言模型 (LLMs)](#将问题映射到大型语言模型-llms)
- [策略梯度定理 (Policy Gradient Theorem)](#策略梯度定理-policy-gradient-theorem)
- [对数导数技巧 (Log-Derivative Trick)](#对数导数技巧-log-derivative-trick)
- [REINFORCE 算法](#reinforce-算法)
- [将 REINFORCE 应用于 LLM](#将-reinforce-应用于-llm)
- [信用分配问题与高方差](#信用分配问题与高方差)
- [Actor-Critic 架构：引入优势函数](#actor-critic-架构引入优势函数)
- [PPO (Proximal Policy Optimization)](#ppo-proximal-policy-optimization)
- [总结与 RLHF](#总结与-rlhf)
- [AI 总结](#ai-总结)

---

## 核心问题：黑盒奖励无法反向传播
[原片 @ 00:00](https://www.youtube.com/watch?v=26j1Cn8AECs&t=0s)

视频的核心在于解决**抽象目标（Abstract Goals）**的训练问题。传统的有监督微调（Simple Fine-tuning）在明确的数据集上易如反掌，但面对“变得更乐于助人”或“写出更安全的回复”等目标时，直接写损失函数（Loss Function）是不可能的。我们只能给模型一个“评分”或“奖励”（Reward），但**这个奖励信号通常是一个“黑盒”（Black Box）**。

![](./Policy%20Gradient%20in%2030%20min/screenshot_000_0a1cdb64-7ba9-4362-8667-bc1897e47346.jpg)

> ![](./Policy%20Gradient%20in%2030%20min/screenshot_001_131db1bc-92b8-43b7-b6ca-a81ff42e4b21.jpg) 视频开篇指出，接下来的30分钟将详细拆解驱动 ChatGPT 对齐的**核心算法——策略梯度（Policy Gradients）**。

![](./Policy%20Gradient%20in%2030%20min/screenshot_002_fe025834-f482-48eb-ae8b-2346f360ffe9.jpg) 对比了简单微调与抽象目标：训练模型在数据集上很容易，但如何为“变得更有帮助”或“写出更安全的回复”等目标进行训练？

![](./Policy%20Gradient%20in%2030%20min/screenshot_003_ebcb0f41-0dc1-4b36-8e5e-ba38e61fecac.jpg) 介绍了强化学习中的黑盒环境（Human / AI Judge）。Agent 输出动作，环境返回一个单一的**奖励数值（Reward）**。

![](./Policy%20Gradient%20in%2030%20min/screenshot_004_83671b4e-e1bb-4b36-8509-75e1803a837f.jpg) 关键问题：**你无法通过人类的意见进行反向传播（Backpropagate）**。标准的梯度下降在这里是完全无用的。

## 将问题映射到大型语言模型 (LLMs)
[原片 @ 04:49](https://www.youtube.com/watch?v=26j1Cn8AECs&t=289s)

我们可以将简单的优化问题完美映射到 LLM 的训练中：

*   **输入 x** -> 对应 LLM 的海量参数 $\theta$。
*   **奖励函数 $R(x)$** -> 对应一个评估生成文本的**奖励模型（Reward Model）**，记作 $R(y)$。
*   **寻找最优 x** -> 寻找最优参数 $\theta$，以生成高奖励文本。

![](./Policy%20Gradient%20in%2030%20min/screenshot_005_f235ee4a-fb9d-4164-b64f-a1e7116d7bcc.jpg) 流程图展示了LLM参数 $\theta$ 生成文本 $y$，文本进入奖励模型 $R$，模型返回一个单一的分数（如 $0.9$ 表示有帮助，$0.1$ 表示无帮助）。

![](./Policy%20Gradient%20in%2030%20min/screenshot_006_45ff6a5c-0ad2-47d1-a83f-d1e79af42119.jpg) 再次强调核心矛盾：**你无法通过文本生成和人类判断来反向传播奖励分数。**梯度路径在人类评估（黑盒）这里彻底中断。如何更新模型参数成为了中心问题。

## 策略梯度定理 (Policy Gradient Theorem)
[原片 @ 06:06](https://www.youtube.com/watch?v=26j1Cn8AECs&t=366s)

这是解决上述问题的数学基石。策略梯度允许我们在奖励函数完全未知的情况下，直接对策略进行优化。公式为：
$$
\nabla_\theta J(\theta) = E_{\tau \sim \pi_\theta} \left[ \left( \sum_{t=0}^T \nabla_\theta \log \pi_\theta(a_t|s_t) \right) \left( \sum_{t=0}^T r(s_t, a_t) \right) \right]
$$

为了真正理解它，我们从最原始的**朴素方法 (Naive Approach)** 开始推导，这会走向死胡同：
我们希望最大化期望奖励：$J(\theta) = E_{\tau \sim \pi_\theta}[R(\tau)] = \int \pi_\theta(\tau) R(\tau) d\tau$。

![](./Policy%20Gradient%20in%2030%20min/screenshot_007_c1386155-8b25-425e-86fc-c7598b8adc69.jpg) 目标是最大化期望奖励 $J(\theta)$，表达形式是对所有可能轨迹 $\tau$ 的积分。

![](./Policy%20Gradient%20in%2030%20min/screenshot_008_6c008012-470f-48f4-bc4e-bf279189f135.jpg) 第一步：取目标函数的梯度；第二步：交换梯度与积分，并且由于奖励 $R(\tau)$ 不依赖于参数 $\theta$，将其提取出来，得到 $\int R(\tau) \nabla_\theta \pi_\theta(\tau) d\tau$。

**为什么这是死胡同？**
因为要从样本中估算积分，公式必须满足**期望（Expectation）**的形式，即 $\int p(x)f(x)dx$。在这个公式中，Distribution 部分变成了 $\nabla_\theta \pi_\theta(\tau)$，而不是我们熟知的 $\pi_\theta(\tau)$。这意味着我们不知道如何从“策略梯度的分布”中进行采样，**算法卡住了**。

## 对数导数技巧 (Log-Derivative Trick)
[原片 @ 08:39](https://www.youtube.com/watch?v=26j1Cn8AECs&t=519s)

拯救这个公式的英雄是微积分中的一个简单而优美的恒等式。
计算 $\log f(x)$ 的导数，有：
$$
\nabla_\theta \log f(x) = \frac{\nabla_\theta f(x)}{f(x)}
$$
重新排列后得到：
$$
\nabla_\theta f(x) = f(x) \nabla_\theta \log f(x)
$$

![](./Policy%20Gradient%20in%2030%20min/screenshot_009_1da8b4ec-a10e-4d8a-a077-13761f73a43a.jpg) 利用对数导数技巧，推导出 $\nabla_\theta J(\theta) = \int R(\tau) (\pi_\theta(\tau) \nabla_\theta \log \pi_\theta(\tau)) d\tau$。

将其代入之前的死胡同公式，奇迹发生了：
$$
\nabla_\theta J(\theta) = \int \pi_\theta(\tau) [R(\tau) \nabla_\theta \log \pi_\theta(\tau)] d\tau
$$
这个积分现在完美地变成了一个**期望（Expectation）**：
$$
\nabla_\theta J(\theta) = E_{\tau \sim \pi_\theta} [R(\tau) \nabla_\theta \log \pi_\theta(\tau)]
$$
现在，概率分布是我们的策略 $\pi_\theta(\tau)$，我们**知道如何从中采样**，而函数 $f(x)$ 就是括号里的部分。不可处理的积分被转化为了可以通过采样估算的期望。

## REINFORCE 算法
[原片 @ 10:36](https://www.youtube.com/watch?v=26j1Cn8AECs&t=636s)

这是策略梯度定理最简单、最直观的实现。

![](./Policy%20Gradient%20in%2030%20min/screenshot_010_a669486e-8da8-49cb-8841-f75f8bcb2a1e.jpg) REINFORCE 算法步骤：
1\. 初始化策略网络 $\pi_\theta$。
2\. 循环：
    *   **Rollout**：使用当前策略生成完整轨迹 $\tau$。
    *   **Reward**：计算该轨迹的总奖励 $R(\tau)$（从黑盒获取）。
    *   **Update**：计算得分（梯度）并乘以奖励：
        $\theta \leftarrow \theta + \alpha \cdot R(\tau) \cdot \nabla_\theta \log \pi_\theta(\tau)$

**核心直觉：**
*   **高正向奖励** $\rightarrow$ 加大幅度提升该动作的概率（Make action more likely）。
*   **低或负向奖励** $\rightarrow$ 采取步骤降低该动作的概率（Make action less likely）。

![](./Policy%20Gradient%20in%2030%20min/screenshot_011_3fd8e63d-3004-468e-aecd-2d29259fd944.jpg) 在 1D 优化问题上演示 REINFORCE：
策略：正态分布 $N(\mu, \sigma)$，研究参数 $\theta = \mu$；动作：采样 $x$；奖励函数：$R(x) = -(x-2)^2 + 10$（黑盒）；得分：$\frac{x-\mu}{\sigma^2}$。
![](./Policy%20Gradient%20in%2030%20min/screenshot_012_b8686e60-781c-4bf6-a23f-070f63ac8bda.jpg) 举例说明，如果采样到接近峰值 $x = 1.89$，奖励为 $9.99$，得分（Score）为 $3.89$。更新幅度（Score $\times$ Reward）高达 $38.82$，将均值 $\mu$ 从 $-2.0$ 大幅推向接近峰值的位置。

## 将 REINFORCE 应用于 LLM
[原片 @ 14:30](https://www.youtube.com/watch?v=26j1Cn8AECs&t=870s)

为了将强化学习（RL）翻译成 LLM 的语言，我们需要一张 **罗塞塔石碑（Rosetta Stone）**：

*   **Policy $\pi_\theta$** -> **LLM 本身**。它定义了下一个 token 的概率分布。
*   **State $s_t$** -> **Prompt + 到目前为止生成的 Tokens**。即 LLM 当前的上下文。
*   **Action $a_t$** -> **下一个 Token**（从词表中采样）。
*   **Trajectory $\tau$** -> **完整的回复**（由所有生成的 token 组成）。
*   **Reward $R(\tau)$** -> **单一分数**（通常来自外部的奖励模型）。

![](./Policy%20Gradient%20in%2030%20min/screenshot_013_997821aa-c25d-4896-bcfd-21a5e3cf93c6.jpg) 关键项 $\nabla_\theta \log \pi_\theta(a_t|s_t)$，在 LLM 中其实仅仅是所选 token 的**对数概率梯度**（Log-probability gradient），这是任何 Transformer 模型的标准输出。

**写俳句（Haiku）实例：**
![](./Policy%20Gradient%20in%2030%20min/screenshot_014_d964ae46-075a-4f11-939f-ff21bf2e90ea.jpg) 步骤 1：Prompt（初始状态 $s_0$）为 "Write a haiku about robots."
![](./Policy%20Gradient%20in%2030%20min/screenshot_015_929a6315-c90d-47fb-94bd-e07c12b47c79.jpg) 步骤 2：Rollout。LLM 根据 $s_0$ 采样出 token $a_0 =$ "Metal"，更新状态 $s_1$，接着生成 $a_1 =$ "gears"... 直到生成完整轨迹 $\tau$。
![](./Policy%20Gradient%20in%2030%20min/screenshot_016_8d8f341f-7302-46ab-95b4-8343538d4dfd.jpg) 步骤 3：奖励计算。将生成的完整回复送给奖励模型（黑盒），得到 $R = 0.9$。
![](./Policy%20Gradient%20in%2030%20min/screenshot_017_4c09065a-792a-4798-91d9-8099201118cf.jpg) 步骤 4：更新。使用奖励 $0.9$ 去更新每个 token 的对数概率梯度。**整个序列的最终梯度是所有 token 信号的加和**。

## 信用分配问题与高方差
[原片 @ 17:42](https://www.youtube.com/watch?v=26j1Cn8AECs&t=1062s)

尽管 REINFORCE 可以工作，但它极其低效，存在经典的**信用分配（Credit Assignment）**问题。就像给一个小组作业付了一个最终成绩，有人干了所有活，有人啥也没干，却得了同样的分数。

![](./Policy%20Gradient%20in%2030%20min/screenshot_018_b2a27e21-f5f3-4e3b-9062-4e2cb6b27d75.jpg) 单个奖励 $R=0.9$ 是给几十个不同决策的。例如 "Metal gears softly turn" 可能很精彩，但结尾 "I am now awake" 很普通。REINFORCE **将两者同等对待，都奖励 $+0.9$**。
![](./Policy%20Gradient%20in%2030%20min/screenshot_019_0f52f507-fc10-4137-ad11-ee0e2ee2b988.jpg) 反之，如果最终奖励很低（$0.2$），精彩的部分也会被同样惩罚。

这种“将单一奖励抹平（Smearing）到整个序列”的方式，导致**梯度噪声极大、方差极高（High-Variance）**，学习缓慢且极不稳定。REINFORCE 是一种蛮力工具，我们需要更外科手术式的方法。

## Actor-Critic 架构：引入优势函数
[原片 @ 19:12](https://www.youtube.com/watch?v=26j1Cn8AECs&t=1152s)

![](./Policy%20Gradient%20in%2030%20min/screenshot_020_d7d57003-c9c9-4863-b56c-c28824cd201b.jpg) 根本问题在于我们问错了问题。不要问“最终结果好吗？”，而要问：**“这个特定的动作比我在此时预期的更好还是更差？”**

**直觉示例：**
*   打游戏得到 80 分。如果平均水平是 30分，那是极好的；如果平均水平是 95分，那简直是灾难。
*   原始得分不如**优势（Advantage）**包含的信息量大。

**引入基线（Baseline）：**
![](./Policy%20Gradient%20in%2030%20min/screenshot_021_6a8c89ba-2f38-4a88-b7ee-c98ad0ccc6ce.jpg) 不在用原始奖励 $R(\tau)$ 缩放梯度，而是用 **$R(\tau) - b$**，其中 $b$ 是基线。只要 $b$ 不依赖于动作 $a_t$，数学上就是完全合理的。这通过让算法只关注“真正极好或真正极差”的结果，大幅降低了方差。

![](./Policy%20Gradient%20in%2030%20min/screenshot_022_02eba2f2-6498-4944-b8d7-b305fcc4c8dc.jpg) 最好的基线是**价值函数（Value Function）$V(s_t)$**，即在当前状态 $s_t$ 下按照策略 $\pi_\theta$ 行动的**预期总奖励**。

![](./Policy%20Gradient%20in%2030%20min/screenshot_023_7bbd10c6-7539-4195-8ebe-a2316cc433fd.jpg) 由此定义**优势函数（Advantage Function）**：
$$
A(s_t, a_t) = R_t - V(s_t)
$$
（优势 = 实际收到的奖励 - 从当前状态预期的奖励）

![](./Policy%20Gradient%20in%2030%20min/screenshot_024_6ec05535-9a33-48c0-80e6-e35cbeef353b.jpg) 
*   如果 $A > 0$：正向惊喜（结果比预期好），增加该动作的概率。
*   如果 $A < 0$：负向惊喜（结果比预期差），降低该动作的概率。

![](./Policy%20Gradient%20in%2030%20min/screenshot_025_29dbe898-b311-4f69-88d2-f1cbf0418025.jpg) 最终的最稳定策略梯度更新公式：
$$
\nabla_\theta J(\theta) = E_{\tau \sim \pi_\theta} \left[ \sum_{t=0}^T \nabla_\theta \log \pi_\theta(a_t|s_t) A(s_t, a_t) \right]
$$
我们不再强化原始分数，而是**强化正向或负向的“惊喜”**，这是一个巨大的进步！

**Actor-Critic 架构：**
![](./Policy%20Gradient%20in%2030%20min/screenshot_026_3a7efae9-cbbf-4bad-9fb5-bf06120e8fc8.jpg) 如何获得 $V(s_t)$？我们不知道真实的价值函数，所以用另一个神经网络来**学习它**。这就引出了著名的 Actor-Critic 架构：
*   **Actor（演员）**：即策略网络（LLM），负责看状态 $s_t$ 并决定动作 $a_t$。使用带优势信号的策略梯度进行学习。
*   **Critic（评论家）**：一个独立的神经网络，负责看状态 $s_t$ 并估计其价值 $V(s_t)$。通过最小化均方误差（MSE Loss）来学习，即尽量匹配实际看到的奖励。
![](./Policy%20Gradient%20in%2030%20min/screenshot_027_f8eefa83-fdb3-4cbb-8f85-8ef22fd693c1.jpg) 在实践中，LLM 的 Actor 和 Critic 不是完全独立的。Critic 只是接在 Transformer 尾部的一个微小的 **价值头（Value Head）**，极大提高了效率。

![](./Policy%20Gradient%20in%2030%20min/screenshot_028_a250232d-f03c-4eb2-83ef-e7d52c55e81c.jpg) 俳句实例：生成最后一个词 "awake" 时，Critic 预测 $V(s_t) = 0.85$，而实际环境奖励 $R=0.9$。优势 $A = 0.9 - 0.85 = +0.05$。我们给予的不再是巨大的 $+0.9$ 噪声信号，而是精确的 $+0.05$ 正向惊喜，这是一个温和的“轻推”（Gentle nudge）。

## PPO (Proximal Policy Optimization)
[原片 @ 25:29](https://www.youtube.com/watch?v=26j1Cn8AECs&t=1529s)

Actor-Critic 解决了方差问题，但带来了更危险的**不稳定性（Instability）**。如果模型遇到一个具有极高优势的数据批次，它会采取极其巨大的更新步伐，可能瞬间摧毁之前的策略，导致**灾难性崩溃（Catastrophic Collapse）**。
对于 LLM，一旦发现能触发高奖励的短语，它可能会疯狂追逐该信号，**抛弃语法、抛弃连贯性（Reward Hacking）**。我们需要一个**安全束带（Safety Harness）**，让模型在当前的“信任区域（Trust Region）”内进行提升。

![](./Policy%20Gradient%20in%2030%20min/screenshot_029_7a8b047b-24c1-4518-8b09-e1bd1edbaef7.jpg) PPO 要回答的核心问题：**如何迈出最大可能的改进步伐，同时避免导致性能灾难性下降？**
![](./Policy%20Gradient%20in%2030%20min/screenshot_030_ceb97423-5a0f-4535-b638-b0e66ac48986.jpg) 以前的算法使用极其复杂的数学。PPO 的天才之处在于一个简单的技巧：**裁剪代理目标函数（Clipped Surrogate Objective）**。

**1. 概率比率（Probability Ratio）：**
$$
r_t(\theta) = \frac{\pi_\theta(a_t|s_t)}{\pi_{\theta_{old}}(a_t|s_t)}
$$
（新策略下的概率 / 旧策略下的概率）。$>1$ 表示动作更容易发生，$<1$ 表示更难发生。

**2. PPO 裁剪目标：**
$$
L^{CLIP}(\theta) = E_t \left[ \min(r_t(\theta) A_t, \text{clip}(r_t(\theta), 1-\epsilon, 1+\epsilon) A_t) \right]
$$

![](./Policy%20Gradient%20in%2030%20min/screenshot_031_2febaa73-3c8c-4797-8dce-fcc62a300966.jpg) **情况 1：优势 $A_t$ 为正**。目标函数变为 $\min(r_t A_t, (1+\epsilon)A_t)$。这创造了一个**天花板（Ceiling）**。一旦比率超过 $1+\epsilon$，收益不再增加，模型失去过度贪心的动力。
![](./Policy%20Gradient%20in%2030%20min/screenshot_032_f91c1f8d-167a-4b7e-bc44-df317345710e.jpg) **情况 2：优势 $A_t$ 为负**。目标函数变为 $\min(r_t A_t, (1-\epsilon)A_t)$。这创造了一个**地板（Floor）**。一旦比率跌破 $1-\epsilon$，惩罚不再增加，防止模型反应过度。

**3. KL 散度惩罚（KL-Divergence Penalty）：**
![](./Policy%20Gradient%20in%2030%20min/screenshot_033_44c9e0c5-3eb1-4853-b208-c16f497a3e3c.jpg) 对于 LLM，还需要最后一道安全带，即在损失函数中增加一个惩罚项：
$$
\text{Final Loss} = L^{CLIP} - \beta \cdot KL(\pi_{\theta_{old}} || \pi_\theta)
$$
这个 $KL$ 衡量新策略与原始策略（通常是 SFT 模型）的偏离程度，$\beta$ 控制惩罚力度。这确保了模型为了追逐奖励，**不会遗忘它在初始训练中获得的语法、知识和风格**。

![](./Policy%20Gradient%20in%2030%20min/screenshot_034_2859dbef-fc30-4e49-ae48-d8f3aef83377.jpg) 结合了 Actor-Critic 的稳定更新和 PPO 裁剪信任区域的安全性，PPO 提供了对齐大规模 LLM 所需的鲁棒算法。

## 总结与 RLHF
[原片 @ 29:42](https://www.youtube.com/watch?v=26j1Cn8AECs&t=1782s)

整个视频可以总结为四个核心步骤：
1.  **黑盒问题**：不能使用标准的梯度下降来优化人类意见这种黑盒奖励，因为有死胡同（无法反向传播）。
2.  **REINFORCE**：对数导数技巧打破了这堵墙。但由于高方差，信号极其嘈杂。
3.  **Actor-Critic**：引入基线（Baseline），切断噪声，带来稳定的稳定性。
4.  **PPO**：PPO 的裁剪目标创造了信任区域，防止模型在更新中摧毁自己。

![](./Policy%20Gradient%20in%2030%20min/screenshot_035_eb0a4dbd-57de-4ae5-835f-160ee87c1914.jpg) 在科技界常听到的 **RLHF（基于人类反馈的强化学习）**，实质上运转的正是这套机器：
1.  收集人类偏好数据，训练出一个**奖励模型**（即我们的黑盒 $R$）。
2.  将奖励模型放入 **PPO 循环**中，更新基础 LLM（即我们的 Actor $\pi_\theta$）。
3.  在这个过程中，至关重要的 **KL 惩罚**起着安全带的作用，确保模型不会忘记其核心知识。

虽然规模庞大，但推动最先进 AI 模型对齐的核心算法原理，正是上述内容。

## AI 总结

这个视频系统性地推导了现代大型语言模型（LLM）对齐的核心算法——**策略梯度（Policy Gradient）**及其演进。内容从“无法对黑盒奖励（如人类偏好）进行反向传播”这一根本痛点出发，形象地展示了**策略梯度定理**如何利用**对数导数技巧（Log-Derivative Trick）**，将无法处理的积分转化为可通过采样估计的期望，从而推导出最基础的 **REINFORCE 算法**。

随后，视频深入探讨了强化学习与 LLM 的映射关系（如 Policy = LLM、Action = 生成 token 等），指出 REINFORCE 存在严重的**信用分配问题（Credit Assignment）**和高方差。为解决此问题，自然演进到了 **Actor-Critic 架构**，引入**价值函数（Value Function）**和**优势函数（Advantage）**，将奖励平滑转化为“正向/负向惊喜”。

最后，针对 Actor-Critic 可能导致策略崩溃的风险，视频详细解析了目前 LLM 对齐的工业标准 **PPO（Proximal Policy Optimization）**。通过**概率比率（Probability Ratio）**的 Clip 机制和 **KL 散度惩罚**，PPO 在确保模型稳定提升奖励的同时，维持了“信任区域”，防止了模型因追逐奖励而破坏原有的语言能力，最终构成完整且落地的 **RLHF（人类反馈强化学习）**技术栈。