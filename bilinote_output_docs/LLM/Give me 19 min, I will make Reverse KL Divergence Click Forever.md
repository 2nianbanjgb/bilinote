> 来源链接：https://www.youtube.com/watch?v=mMQRr9TDJQ4

## 目录
- 视频背景与核心概念 [原片 @ 00:00](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=0s)
- 核心示例：“水在___沸腾” [原片 @ 00:36](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=36s)
- 大语言模型背景与蒸馏问题 [原片 @ 01:42](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=102s)
- KL散度的数学定义 [原片 @ 04:03](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=243s)
- 直觉理解与模式覆盖/模式寻找 [原片 @ 06:48](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=408s)
- 寻找最优解与图表分析 [原片 @ 08:18](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=498s)
- 梯度推导与代码实现 [原片 @ 10:09](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=609s)
- 实际应用与不同论文的取舍 [原片 @ 14:28](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=868s)
- 进阶解决方案：GKD 与广义 JSD [原片 @ 15:46](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=946s)
- 最佳实践与总结 [原片 @ 17:36](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=1056s)

## 视频背景与核心概念
[原片 @ 00:00](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=0s)

本视频探讨了大型语言模型（LLM）蒸馏中的 **Reverse KL Divergence（反向 KL 散度）**，并基于 Thinking Machines 在 2025 年 10 月发布的关于 Policy Distillation（策略蒸馏）的文章展开。

*   **核心流程**：较小的 Student 模型生成自己的文本（称为 Rollouts），较大的 Teacher 模型为每个 token 打分。
*   **核心算法**：学习算法可以浓缩为一行公式——**Per-token reverse KL divergence（逐 token 反向 KL 散度）**。
*   **为什么选择反向 KL**：文章给出了两个关键原因——**Unhackable（不可被欺骗的）** 和 **Mode-seeking（模式寻找的）**。
*   **视频目标**：通过高度可视化的方式，让人永远理解 Forward KL 和 Reverse KL 的区别。

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_000_f82b0dd9-aeb1-4ed5-ae2b-81d7af400754.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_001_b901fb5c-ec5b-47bc-a7c9-97297296e4ca.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_002_187c72cf-712e-45d6-b796-e57e47be9241.jpg)

## 核心示例：“水在___沸腾”
[原片 @ 00:36](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=36s)

为了直观解释，视频引入了一个思想实验：“Water boils at ___”（水在___沸腾）。

*   **Teacher 模型**：知道两个正确答案，即 `100` (Celsius) 和 `212` (Fahrenheit)，中间没有任何其他答案。
*   **Student 模型**：是一个较小的模型，其输出服从单一的 Normal Distribution（正态分布），只能容纳一个答案。初始位置在 `60`。
*   **前向 KL（Forward KL）训练**：Student 模型的峰值会停在 `150`，这是一个在两个单位下都错误的温度（Mode-covering，试图覆盖所有）。
*   **反向 KL（Reverse KL）训练**：Student 模型的峰值会攀升并锁定在 `100`（Mode-seeking，锁定单一模式）。

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_003_fd541397-7ba5-42b2-af6b-194cb4bff48b.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_004_89a920e7-02e4-4aaf-b216-aad53aa4107f.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_005_75b35da3-6e3f-4948-8dfc-9ea8213262fa.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_006_c5191962-387f-4453-8a24-deb85e047f7f.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_007_77940ee2-a293-491a-835b-10f0b1228576.jpg)

## 大语言模型背景与蒸馏问题
[原片 @ 01:42](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=102s)

为了将问题具象化并保持数字可见，视频使用了两个极简的 Token 模型（从 0 到 248，步长为 4，共 63 个 token）。

*   **Teacher 分布**：由两个正态分布混合而成。标准差为 8，55% 集中在 100，45% 集中在 212，并在每个 token 上加了一个极小的基础概率。
*   **Student 分布**：单一的正态分布，标准差固定为 8，因此它需要学习的只有一个数字——它的**均值（Mean, \(c\)）**。
*   **LLM 蒸馏的困境**：像 Quen3 这样的大模型有 151,669 个 token，且无序。Student 模型由于容量限制（单峰），无法完美复制 Teacher 的双峰分布。它必然要犯错，而 **Loss 函数决定了它会犯哪种错**。

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_008_b116aafe-a6f6-4af1-b6fc-4c8be5eaa33a.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_009_a0ecb224-1947-4bab-bed3-659ecc4267c4.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_010_727b2688-f486-445f-91a0-736f6a9cf71d.jpg)

## KL散度的数学定义
[原片 @ 04:03](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=243s)

Kullback-Leibler (KL) Divergence 用于衡量两个概率分布的差异。匹配时为 0，差异越大值越大。

公式为：
\[
 KL(p || q) = \sum_i p_i \log(\frac{p_i}{q_i}) 
\]

*   **第一项列表是乘数（The first list is the multiplier）**。
*   **Forward KL**（Teacher 在前）：\(KL(p || q)\)，乘数是 Teacher 的概率 \(p_i\)。它检查 Teacher 给出的每一个答案。
*   **Reverse KL**（Student 在前）：\(KL(q || p)\)，乘数是 Student 的概率 \(q_i\)。它只检查 Student 自己给出的答案。

视频测试了 5 种不同的 Student 分布情况并计算了两种 KL 值：
*   **完全复制（Copy）**：两者 Loss 均为 0。
*   **平移一个 token（Shift）**：两者 Loss 接近，均为 0.12。
*   **调换高度（Heights traded）**：两者 Loss 均为 0.02。
*   **拉平分布（Flat）**：Forward KL 为 1.34（惩罚 Teacher 高峰处的低概率），Reverse KL 为 3.66（惩罚 Student 低概率处 Teacher 的极小概率，即“无中生有”）。
*   **对称分布在 212**：Forward KL 飙升至 53.26（因为漏掉了 100 处的峰值），Reverse KL 仅为 0.80。

**核心结论**：
*   **Forward KL（Mode-covering）**：无法忽略遗漏的答案。如果 Student 丢掉了某个 Teacher 的答案，Loss 会无穷大。
*   **Reverse KL（Mode-seeking）**：无法忽略生造的答案。如果 Student 在 Teacher 几乎没概率的地方产生概率，Loss 会无穷大。

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_011_249390b8-7701-4967-afc8-1cb6ede5d416.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_012_88a59faa-5d9e-4f44-8d17-0ba31169bd27.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_013_7d624356-ab68-456c-a985-0f49500719f2.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_014_d8cb19ab-0698-45d7-a37e-13f8fd0bf4db.jpg)

## 直觉理解与模式覆盖/模式寻找
[原片 @ 06:48](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=408s)

视频通过机器人漫画直观地解释了两种 Loss：
*   **Forward KL**：Teacher 指着自己的答案列表说：“你应该学这个”。Student 会试图同时托起两个答案（100°C 和 212°F），因为无法兼顾，最终落在了中间（150）。**问题：Student 试图覆盖所有模式，导致产生了不准确的中间态。**
*   **Reverse KL**：Student 拿着自己的答案去问 Teacher：“我做对了吗？”。Student 只会关注自己的答案。**问题：Student 永远听不到自己不存在的答案，因此容易陷入局部最优。**

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_015_bf6b72e6-b442-4587-a1f0-ffe2659951f9.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_016_666d72ad-819b-449f-afd6-02cebbc73d73.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_017_cc12702f-879f-4f9b-882a-c8f0694e4494.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_018_5484ca59-3410-4c43-b878-78f62db4ad9d.jpg)

## 寻找最优解与图表分析
[原片 @ 08:18](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=498s)

通过 PyTorch 代码遍历所有可能的均值（0 到 248，步长 0.01，共 24,801 个候选）。

*   **Forward KL 的最优解**：停留在 `150.37`，这恰好是 Teacher 分布的加权平均值（55% * 100 + 45% * 212）。
*   **Reverse KL 的最优解**：有两个低点，分别在 `100` 和 `212`。中间在 `156.2` 处有一个局部最大值。
*   **训练动态**：如果从 `60` 开始，Reverse KL 会继续攀升并停在较近的 `100`。
*   **Loss 解释**：
    *   在 `100` 处，Student 完美对齐了 Celsius 峰值，但漏掉了 Fahrenheit 峰值。此时 Reverse KL 的代价是 \(\log(1/0.55) \approx 0.6\)（只是轻微地惩罚了 Dropped 答案）。
    *   在同样的位置，Forward KL 的代价高达 `43.41`（严厉惩罚了漏掉 Fahrenheit 峰值）。

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_019_aadb8130-b8f1-4dd1-b60a-a051a4e76273.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_020_fe5dabc6-bfcd-40c2-a480-2ca393fd4af6.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_021_d02f58d9-c280-45e3-a065-00f5a3379380.jpg)

## 梯度推导与代码实现
[原片 @ 10:09](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=609s)

视频在单张幻灯片上展示了完整且标注了规则的梯度推导过程。

*   **Forward KL 梯度**：相当于交叉熵。\( \nabla_{\theta} KL(p||q) = - \mathbb{E}_{p}[\nabla_{\theta} \log q] \)。
*   **Reverse KL 梯度**：利用对数求导技巧，化简为 \( \mathbb{E}_{q}[(\log q - \log p)\nabla_{\theta} \log q] \)。这在强化学习中等同于 Policy Gradient（策略梯度），其中奖励是 \(\log p - \log q\)。
*   **均值 \(c\) 的梯度**：对每一个 Logit \(z_i\)，导数是 \(q_i - p_i\)（Forward）或 \(q_i(\log \frac{q_i}{p_i} - KL)\)（Reverse）。
*   **具体计算**：在中心点为 60 时，Forward KL 梯度为 \(-1.41\)，Reverse KL 梯度为 \(-0.099\)。如果学习率设为 16，一次更新后，Forward 会跳向 `82.6`，而 Reverse 只会微小移动。

代码实现分为两种：
1.  **By Hand（手动计算）**：使用上述推导出的公式直接计算梯度。
2.  **Autograd（自动求导）**：只写出 Loss，利用 PyTorch 的 `.backward()` 自动处理链式法则。

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_022_cc137d3b-e351-442b-b98d-9c8de840c9cf.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_023_b71f6185-66ef-48d4-a040-599ae7c8e77d.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_024_58b1c91c-ed34-4103-b1d6-6976e01142b9.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_025_173e5f7b-0a0b-4d73-9c20-2a77b9effa20.jpg)

## 实际应用与不同论文的取舍
[原片 @ 14:28](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=868s)

*   **Hinton 2015 经典论文（Forward KL）**：使用 Cross Entropy 和 Soft Targets 进行训练，本质是 Forward KL。这也是 GKD 等论文公认的常用选择。
*   **MiniLLM 2023 论文（Reverse KL）**：提出用 Reverse KL 替换 Forward KL，以防止 Student 高估 Teacher 低概率区域（防止幻觉）。
*   **Thinking Machines 的食谱（Reverse KL）**：直接使用逐 token 的 Reverse KL，并且强调其在 Reward Model 下是 **Unhackable** 的。
*   **各自的局限性**：
    *   **Forward KL 的局限**：最终会落在中间，两个答案都错。
    *   **Reverse KL 的局限**：如果初始点（如 `40`）距离所有答案都很远，梯度会互相抵消，模型会卡住不动（Mode-seeking 在错误的地方陷入困境）。

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_026_656fb260-2f4d-45be-9c74-8cf2b2e3a11d.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_027_3adc7ddf-6746-4b44-8cbb-7c3c9830d42a.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_028_c77f8161-d818-4a9d-889a-8e6ce377f551.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_029_1e06bcfa-9df0-418b-95d5-d4e3fd7e58fa.jpg)

## 进阶解决方案：GKD 与广义 JSD
[原片 @ 15:46](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=946s)

Google DeepMind 的 GKD（Generalized Knowledge Distillation）论文提出了一种混合方法——**广义 Jensen-Shannon Divergence (JSD)**：

\[
 D_{JSD(\beta)}(P || Q) = \beta D_{KL}(P || M) + (1-\beta)D_{KL}(Q || M) 
\]
其中 \( M = \beta P + (1-\beta)Q \) 是 Teacher 和 Student 分布的混合。

*   **特性**：当 \(\beta = 0\) 时，JSD 退化为 Forward KL；当 \(\beta = 1\) 时，退化为 Reverse KL。
*   **实验结果**：
    *   从 `60` 出发时，即使 \(\beta=0.1\)，模型也会像 Reverse KL 一样停在 `100`。
    *   从 `40` 出发时，任何 \(\beta\) 值都无法让模型移动（因为混合分布依然包含大量空白区域）。
*   **最佳实践（先 Forward，后 Reverse）**：
    先用 40 步 Forward KL 将模型从 `40` 移动到 `150`，使其进入 Reverse KL 的“引力范围”，然后再用 40 步 Reverse KL 让其收敛到 `100`。

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_030_9c91e56b-3731-43e3-8c5c-24aecf657129.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_031_d1fc4c3d-6f7e-4cac-a4bb-7e3ad6da8bff.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_032_71f3fa7b-8df8-485c-8550-2fb2cf58af41.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_033_6e942994-02e5-4849-94f1-74f0965f03d2.jpg)

## 最佳实践与总结
[原片 @ 17:36](https://www.youtube.com/watch?v=mMQRr9TDJQ4&t=1056s)

*   **Thinking Machines 的真实做法**：在应用 On-Policy Distillation 之前，模型通常已经过 **Mid-training**（利用 Forward KL / SFT 在特定领域数据上进行预训练）。这增加了模型在 Teacher 分布范围内生成 token 的概率。
*   **GKD 的结论**：Forward KL 是最常用的；Reverse KL 会减少生成多样性（比如丢失 212 这个答案）；**最佳的 Divergence 取决于具体的任务**。

**最终总结**：
*   **Forward KL**：Mode-covering（模式覆盖），以 Teacher 为权重，惩罚“漏掉的答案”，最终会落在 Teacher 概率的平均位置。
*   **Reverse KL**：Mode-seeking（模式寻找），以 Student 为权重，惩罚“生造的答案”，最终会锁定在某一个峰值上。
*   **实操建议**：先用 Forward KL 标注新的 token，再用 Reverse KL 进行模式寻找（先 SFT/Forward，后 Reverse）。

![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_034_1b07788e-fd86-4397-9ace-7ddc6dff1acd.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_035_4e85d7f1-b668-4b77-8bd0-c3b9dc1122a4.jpg)
![](./Give%20me%2019%20min,%20I%20will%20make%20Reverse%20KL%20Divergence%20Click%20Forever/screenshot_036_4accaeb5-b63e-484d-8743-fdf34f83b47c.jpg)

## AI 总结

本视频通过高度可视化的方式，深度剖析了大型语言模型蒸馏中 **Forward KL** 与 **Reverse KL** 散度的区别与适用场景。
核心结论在于：**Forward KL (Mode-covering)** 迫使 Student 模型去覆盖 Teacher 的每一个概率峰值，因此容易在多个正确答案之间产生错误的“平均”答案；而 **Reverse KL (Mode-seeking)** 只关注 Student 自己生成的 Token，它会锁定并完美模仿 Teacher 的某一个特定模式，忽略其他模式。
尽管 Reverse KL 具有 "Unhackable" 且能避免幻觉的特性，但它在初始化较差（距离 Teacher 分布太远）时容易陷入局部最优而停滞不前。因此，现实中的最佳方案是采用混合策略或分阶段训练：**先使用 Forward KL（或 SFT）为模型提供正确的概率支撑（初始化），然后再使用 Reverse KL 进行高质量的模式锁定。**