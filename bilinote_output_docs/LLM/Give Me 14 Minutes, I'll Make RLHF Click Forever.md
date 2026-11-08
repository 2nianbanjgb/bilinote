> 来源链接：https://www.youtube.com/watch?v=bUjJqsDJ6Zc

## 目录

- [引入与基础模型](#引入与基础模型)
- [从 SFT 到 RLHF 的动机](#从-sft-到-rlhf-的动机)
- [SFT 的局限性](#sft-的局限性)
- [偏好数据与奖励模型](#偏好数据与奖励模型)
- [奖励模型评分：从 Elo 到 Bradley-Terry](#奖励模型评分从-elo-到-bradley-terry)
- [通过最大似然估计拟合奖励模型](#通过最大似然估计拟合奖励模型)
- [损失函数与梯度](#损失函数与梯度)
- [InstructGPT 与 Llama 3 中的奖励模型](#instructgpt-与-llama-3-中的奖励模型)
- [强化学习与 KL 惩罚](#强化学习与-kl-惩罚)
- [奖励黑客攻击与 KL 散度的必要性](#奖励黑客攻击与-kl-散度的必要性)
- [代码实现：拟合奖励模型](#代码实现拟合奖励模型)
- [代码实现：REINFORCE 与优势函数](#代码实现reinforce-与优势函数)
- [策略梯度循环演练](#策略梯度循环演练)
- [AI 总结](#ai-总结)

---

## 引入与基础模型
[原片 @ 00:00](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=0s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_000_e442704c-0767-4d76-ba8f-6fddc91677e0.jpg)
本节通过一个简单的例子拆解 RLHF（Reinforcement Learning from Human Feedback）的全流程。

- **背景**：ChatGPT 的训练使用了 RLHF，该技术源自 InstructGPT 论文。
- **核心问题**：如何让一个 LLM 通过人类的偏好反馈来优化输出？
- **简化模型**：
  - 问题：“How do I reverse a list in Python?”
  - 模型有四种回答类别：`right` (正确), `chatty` (废话多), `wrong` (错误), `refuse` (拒绝回答)。
  - 初始概率（由 softmax 决定）：`right` 概率为 0.20, `chatty` 为 0.40, `wrong` 为 0.30, `refuse` 为 0.10。
  - 模型用四个数值 $\theta$ 表示这四个回答的概率权重。Softmax 公式：$\pi_i = \frac{e^{\theta_i}}{\sum_j e^{\theta_j}}$。
- **参考模型 (Reference Model, REF)**：冻结的初始模型，用于对比。

## 从 SFT 到 RLHF 的动机
[原片 @ 01:49](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=109s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_001_c81700ea-faf2-4198-8b7f-b3b3424a1071.jpg)
监督微调（Supervised Fine-Tuning, SFT）是标准的第一步。

- **SFT 原理**：人类写出想要的回答（$y^*$），降低模型输出该回答的 loss（$- \log \pi(y^*)$）。
- **过程演示**：在初始概率 0.20 时，loss 为 1.61。对 $\theta$ 加上负梯度（`onehot(y*) - π`），`right` 的 logit 增加 0.8，其他减少。
- **效果**：经过 5 步训练，`right` 的概率从 0.20 升至 0.84，loss 降至 0.17。
- **现实**：真实的 RLHF 流程通常从 SFT 模型开始，这里为了演示，从 REF 模型开始。

## SFT 的局限性
[原片 @ 02:38](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=158s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_002_f51ea874-a23c-4a61-b759-9d88afac68b4.jpg)
既然 SFT 看起来很有效，为什么还需要 RLHF？视频指出了四个主要问题：

- **数据成本高**：人类需要为每一个 prompt 编写高质量回答，费时费力。
- **多解问题**：许多 prompt（如“写一条生日祝福”）没有唯一标准答案。SFT 只会提高被写下那一个回答的概率，忽略其他同样好的回答。
- **无法学习相对错误程度**：SFT 的梯度更新取决于模型的初始概率（概率越高，向下的推力越大），而不是哪个回答更差。例如，`chatty` 被压低 0.4，而 `wrong` 只被压低 0.3，纯粹因为 `chatty` 的初始概率更高，这不符合实际质量的好坏。
- **上限是模仿**：SFT 模型的最佳表现只能完全复制人类写出的答案。

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_003_c9ae386c-adac-4dde-ac33-213fdd14b036.jpg)
因此，我们需要 **RLHF（Reinforcement Learning）**。RL 允许模型自己生成回答，奖励模型（Reward Model）给这些回答打分，模型再朝着得分更高的回答优化。这被称为 **On-Policy** 学习（从自身错误中学习），无需人类写答案。

## 偏好数据与奖励模型
[原片 @ 04:21](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=261s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_004_7617bde9-fe33-4547-b921-284ec2027784.jpg)
强化学习需要一个奖励函数 $r(y)$，但人类很难直接给回答打绝对分数。相比之下，人类更擅长**两两比较（Preference）**。

- **偏好数据**：给定同一个问题 \(x\)，人类在模型生成的两个回答中选出更喜欢的一个（\(y_w\)），另一个为 \(y_l\)。
- **数据集**：假设有 1000 个这样的偏好对。人类偏好可能并不一致（比如 `right` 赢了 `chatty` 198次，但也输了 35次）。
- **目标**：将偏好转化为奖励模型（Reward Model）。该模型在离线阶段训练。

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_005_55803ab1-0843-414a-b753-044444e08ad9.jpg)
- **Elo 评分系统**：类似于国际象棋。每个回答初始 1000 分。赢者加分，输者扣分；如果弱者赢了强者，分数变化更大。
- **Bradley-Terry 模型**：Elo 公式的底层数学模型。分数差决定了一个回答胜出的概率：\(P(a \text{ preferred over } b) = \sigma(score(a) - score(b))\)。其中 \(\sigma\) 是 Sigmoid 函数。

## 通过最大似然估计拟合奖励模型
[原片 @ 06:24](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=384s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_006_d677284f-4909-4344-9885-0b8cef39044e.jpg)
通过调整每个回答的分数，最大化所有人类偏好数据的概率。

- **初始步骤**：将所有分数设为 0。
- **计算概率**：对于每个偏好对，计算模型预测该偏好的概率：\(P(\text{pair}) = \sigma(r(y_w) - r(y_l))\)。如果所有分都为 0，概率为 0.5。
- **总概率**：样本独立同分布，总概率是各概率的乘积。
- **对数化**：通过取对数将乘积变为求和，得到对数似然（Log-likelihood）。
- **优化**：最大化对数似然，即最小化负对数似然损失函数。
- **结果**：通过梯度下降，模型区分出分数（例如 `right` 极高，`refuse` 极低）。只有分数差有意义，最终可对齐固定 `right` 的分数。

## 损失函数与梯度
[原片 @ 07:14](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=434s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_007_7f511a6c-051d-4fb9-9dec-c6b8d61fdb7f.jpg)
奖励模型的损失函数（Loss）：\(L(r) = -\sum_{pairs} \log \sigma(r(y_w) - r(y_l))\)。

- 如果分数差很大，\(\sigma\) 接近 1，\(\log\) 接近 0，loss 很小。
- 如果分数差为负，\(\sigma\) 接近 0，\(\log\) 极小，loss 巨大。
- 梯度更新时，每一对数据，赢家分往上调，输家分往下调。差距越小，梯度越大（力度越大）。

## InstructGPT 与 Llama 3 中的奖励模型
[原片 @ 08:18](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=498s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_008_83c0310d-1515-4ec0-a6f5-b61e6ffbb4b8.jpg)
- **InstructGPT 的实现**：
  - Step 1: 收集人类写的回答进行 SFT。
  - Step 2: 收集人类对模型生成的多个回答的排序，训练 Reward Model。
  - Step 3: 用 RL 更新策略模型。
- **架构细节**：InstructGPT 的 Reward Model 基于 SFT 模型，但**去掉了最后一层的 unembedding**（即预测下一个词的层），使其输出一个标量（分数）。损失函数与我们的推导完全一致。
- **Llama 3 的实现**：基于预训练模型训练 RM。对于多个排序，采用 Bradley-Terry 损失。有时会加入第三个回答（edited），形成 `edited > chosen > rejected` 的排序。

## 强化学习与 KL 惩罚
[原片 @ 09:30](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=570s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_009_c18142c7-1b66-4240-90f6-b23416a034d3.jpg)
有了 Reward Model 后，进入在线（Online）阶段：
- 策略（Policy，即 Chatbot）生成回答 $y$。
- Reward Model 给出分数 \(r(y)\)。
- 强化学习算法更新策略参数 $\pi$。

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_010_bf2bd0fb-2e72-4f4b-a924-45b0b29e24dd.jpg)
- **优化目标**（最大化）：
  \(\max E_{y \sim \pi}[r(y)] - \beta KL(\pi || \pi_{ref})\)
  即最大化平均奖励，同时减去一个与旧模型（REF model）的 KL 散度惩罚。
- **KL 散度公式**：\(KL(\pi || \pi_{ref}) = \sum_y \pi(y) \log \frac{\pi(y)}{\pi_{ref}(y)}\)。
- **施加惩罚的原因**：
  Reward Model 在训练数据分布外是不准确的。如果没有 KL 惩罚，模型会倾向于把所有概率集中在某个能骗过 Reward Model 的单一回答上（即 **Reward Hacking**）。KL 惩罚将模型拉在初始分布附近，确保奖励模型能给出可靠的_score_。

## 奖励黑客攻击与 KL 散度的必要性
[原片 @ 10:12](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=612s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_011_c1b07863-8be9-4e4f-bf14-836c56167522.jpg)
视频对比了无 KL 惩罚和有 KL 惩罚的效果：

- **无惩罚**：模型坍塌，`right` 的概率几乎飙升到 100%，完全放弃了分布式回答。
- **有惩罚**：`right` 的概率同样上升，但保持在相对合理的分布范围内。
- 在真实的 LLM 中，Reward Model 有缺陷。如果不对其加以限制（KL penalty），模型会找到漏洞，疯狂输出能够获得高分的无意义文本（这就是 **Reward Hacking**）。

## 代码实现：拟合奖励模型
[原片 @ 11:12](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=672s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_012_02d9d4a3-5123-4650-bf61-8534aea543bb.jpg)
Python 代码 `fit_reward_model` 的逐行解析：
- 输入是 1000 对偏好数据。
- 初始化分数为 0。
- 循环 300 次梯度下降。
- 对于每一对，计算：`weight = sigmoid(r[w] - r[l])`。
- 梯度计算：`grad[w] += weight`，`grad[l] -= weight`（赢家加分，输家减分）。
- 更新：`r = r + lr * grad / len(pairs)`。
- 训练后，分数体现出了合理分布（例如 `right` 2.0, `chatty` 0.43, `wrong` -0.55, `refuse` -0.96）。

## 代码实现：REINFORCE 与优势函数
[原片 @ 12:12](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=732s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_013_a2eab396-24f0-4cdc-8967-e4c37c10064b.jpg)
在线 RL 部分的代码使用了简化版的 **REINFORCE** 算法，并带有一个均值基线（Mean Baseline）。

- **奖励计算**：每个样本的奖励 \(R = r(y) - \beta \log \frac{\pi(y)}{\pi_{ref}(y)}\)。
- **优势函数 (Advantage)**：\(A = R - \bar{R}\)，其中 \(\bar{R}\) 是本批次（round）的平均奖励。减去平均值是为了降低方差，稳定训练（这被称为 GRPO，Group Relative Policy Optimization，InstructGPT 使用的是 PPO，原理类似）。
- **策略梯度更新**：\(\theta \leftarrow \theta + lr \cdot A \nabla_\theta \log \pi(y)\)。
  即：好的回答增加其概率，差的回答降低其概率，乘以优势函数 $A$ 表示增量的大小。

## 策略梯度循环演练
[原片 @ 12:48](https://www.youtube.com/watch?v=bUjJqsDJ6Zc&t=768s)

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_014_6bef57d0-3a42-48c8-a51b-ee3b89095b34.jpg)
- **初始化**：`theta` 拷贝自 `REF`，此时模型未更新。
- **采样**：每轮采样 16 个回答。
- **计算奖励**：
  初始状态 $\pi = \pi_{ref}$，KL 惩罚项为 0。所以奖励 $R$ 仅取决于 Reward Model 的分数。
  例如，`right` 得到 2.0 分。
- **计算优势**：用每个样本的奖励减去本批次的平均分（例如 0.317）。
  - `right` 的优势是正数（+1.683）。
  - `wrong` 的优势是负数（-0.871）。
- **更新参数**：
  将优势乘以梯度并累加（注意，梯度中 `onehot - π` 的常数项在有多个样本时会相互抵消，最终相当于每一类回答的增加量正比于“该回答出现的次数 × 该回答的优势”）。
  - 更新后，`right` 的概率从 0.2 升至 0.2055，其他回答概率略微下降。

![](./Give%20Me%2014%20Minutes,%20I'll%20Make%20RLHF%20Click%20Forever/screenshot_015_1eeab295-d253-4d79-9104-b3eada0254d5.jpg)
- **最终结果**：训练 3000 轮（总共 48000 个样本），`right` 的概率上升到 0.911，并且保持了一定的多样性，与初始 REF 模型的 KL 散度稳定在 1.21。

## AI 总结

该视频通过一个高度简化的 Python 列表反转问答模型，完美复现了 RLHF 的完整流程。首先通过监督微调（SFT）引出其无法区分错误回答好坏、依赖人工写答案的局限。接着，引入了人类偏好数据，通过 Bradley-Terry 模型和最大似然估计训练出一个能打分的 Reward Model。最后，使用强化学习（REINFORCE 算法）让 Chatbot 在线生成回答，通过奖励模型反馈进行策略梯度更新；并特别强调了 KL 散度惩罚（KL Penalty）在防止模型偏离旧分布、避免遭到奖励黑客攻击（Reward Hacking）中的关键作用。InstructGPT 与 Llama 3 的工业级架构也一并做了对照解释。