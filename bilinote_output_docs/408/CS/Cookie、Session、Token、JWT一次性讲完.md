> 来源链接：https://www.douyin.com/video/7477806066491755828

目录
- 用户身份识别与登录
- Cookie 机制与安全问题
- 数据签名方案
- Session 机制
- Token 机制
- 分布式系统与会话管理
- JWT 标准与结构

## 用户身份识别与登录
[原片 @ 00:00](https://www.douyin.com/video/7477806066491755828)

服务器是如何区分用户的？首先，客户端会进行登录操作。
- 将用户名和密码发送给服务器。
- 服务器查询数据库后，就能知道这是哪个用户的请求。
- 但后续的请求如何处理？难道每次请求都要带上账号密码吗？
- 这样非常不安全，因为客户端需要保存用户密码，极易导致密码泄露。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_000_df5288d5-7f12-48df-b687-90ee5becbbc0.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_001_3b9c3925-9adc-4a91-b3a3-6dc6538b46cc.jpg)

所以通常是由服务器返回一些标记信息，客户端收到后将这些信息保存起来，以后每次请求都带上，服务器就可以做区分，实现了记住登录状态，这就是 Cookie 的核心思路。

## Cookie 机制与安全问题
[原片 @ 00:24](https://www.douyin.com/video/7477806066491755828)

Cookie 的保存和发送是由浏览器自动实现的，不需要网页代码额外处理。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_002_cb6810d1-5f84-4bd0-9c9d-b56faf320b62.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_003_79923b54-0ce8-48ca-aa86-fb7d61f2d3ba.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_004_8e681c5c-0318-46a7-9f7c-923146f3b120.jpg)

此时的 Cookie 信息存在问题：
- 数据里可能只有用户的 ID 和名字（例如 `ID=1001&name=织点`）。
- 恶意用户很容易猜到这些信息，敲敲向服务器请求，就能拿到同样的权限（伪造 Cookie）。
- 因此还需要加上一些手段，防止 Cookie 数据被篡用、被篡改。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_005_d3f9b3cf-2ba9-463d-9a51-cf4c1269db3d.jpg)

## 数据签名方案
[原片 @ 00:48](https://www.douyin.com/video/7477806066491755828)

解决方案是使用数据签名：
- 例如把所有数据连起来，拼接上存在服务器里的密钥（secret）。
- 去哈希计算（如 `sha256`）作为签名。
- 签名随同数据一并发给客户端作为 Cookie。
- 这样后面的请求，服务器就可以通过验证签名来判定数据是否合法，伪造者很难伪造签名。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_006_22fc2026-82fa-4c78-9ce3-86d4bc9879c7.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_007_6e1a08b0-dfae-40c4-9009-2264b77ee2fa.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_008_30fe3fb6-f30f-46b8-ba78-22b4ef8d9aca.jpg)

**签名算法示例：**
`signature = sha256(ID=1001&name=织点&secret=xxxx)`
`// 8667c3ec6a...`

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_009_678dd801-5fb3-413f-8b11-0d95427fcfa8.jpg)

## Session 机制
[原片 @ 01:18](https://www.douyin.com/video/7477806066491755828)

有时候我们不想让浏览器 Cookie 保存太多的数据，那就把数据保存在服务端：
- 生成一个足够长的随机 Key。
- 将数据与随机 Key 关联，把 Key 返回给浏览器写入 Cookie。
- 下次请求时，服务器可以根据 Cookie 中的 Key 插找出保存在服务器的内容。
- 这个过程就叫 **Session**，而 Cookie 则是 Session 的 ID。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_010_9b585e1c-b0c1-43bd-8420-a565240aa266.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_011_c6421752-4d06-4639-9ee5-42e8a6d58fda.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_012_c61edfd0-b2ab-4a39-811f-a846247b9763.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_013_0d467be8-d553-4992-bf24-aa9cf0cd357e.jpg)

Session 本质还是 Cookie，唯一不同的是：
- 只给浏览器一个 SessionID 用作唯一身份区分。
- 会话数据全都保存在服务器里头，由服务器自行管理。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_014_dc89cfe8-653f-43a8-b371-24afb910f279.jpg)

## Token 机制
[原片 @ 01:48](https://www.douyin.com/video/7477806066491755828)

在移动互联网里，客户端除了网页，还有 APP、小程序等。这些客户端的网络请求接口默认是没有 Cookie 机制的，怎么办？
- 很简单，客户端程序将 SessionID 存储在系统里保存起来。
- 然后把 SessionID 换个名字，叫 **Token**。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_015_c841eaaa-0b0c-4f6a-bfd3-13546e5d7063.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_016_400131e0-0d8e-4e76-b516-8f68da68337c.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_017_30341dae-83f2-44a0-a8c3-5551c014cac0.jpg)

Token 和 Session 本质上是一样的：
- 只是少了浏览器的 Cookie 机制，需要自己维护。
- 为了进行认证规范，客户端请求时不再使用 Cookie 发送，而是使用 `Authorization` 字段（例如 `Authorization: Bearer x00c3e...`）。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_018_cbe61959-77d2-46aa-bbe4-67607947d878.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_019_dee6f4c5-de67-40e4-9a9d-aec90a102b27.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_020_15dda958-e91b-423c-a5e9-8a5e4e3912d3.jpg)

## 分布式系统与会话管理
[原片 @ 02:24](https://www.douyin.com/video/7477806066491755828)

我们发现，Session 和 Token 的会话数据都是存放在服务器里的（Stateful）。
- 在单机服务器下自然没有问题。
- 但在分布式服务器下，就会出现某些服务器没有会话数据，导致校验失败。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_021_0e676b0e-58fa-43f4-ba45-b704a3f17f00.jpg)

通常解决方案是在服务器端加上一个中心化的存储服务，例如 Redis 专门存储会话数据。
- 但这容易给分布式系统造成性能瓶颈。
- 中心化服务器如果出现故障，会造成所有服务器连带故障。
- 在一些边缘计算平台里，也没办法使用中心化的存储。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_022_43cee620-c568-4dc2-873d-8b56549fa7be.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_023_a8879f65-bf01-40eb-9a4a-1dfe9337cf36.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_024_e7786560-fd55-4d80-a3ff-5e6fba34d340.jpg)

所以，我们还是希望会话数据由客户端保管，让接口服务是无状态的。
- 直接把 Cookie 那个数据搬过来作为 Token 就可以了。
- 但是 Cookie 的签名算法是我们自己实现的，可能还会存在漏洞，且每个人的算法不一样，会造成五花八门不方便交互。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_025_a61a95ce-afd5-460b-9eef-7b4a26756b54.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_026_c870f664-ae56-4d1a-bf6a-9d358bb5286b.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_027_f8d26b3c-99fe-4485-a6c0-acb0b871024a.jpg)

## JWT 标准与结构
[原片 @ 03:06](https://www.douyin.com/video/7477806066491755828)

我们需要一个标准，而 **JWT**（JSON Web Token）就是其中一种标准。
JWT 生成的 Token 由三部分组成：
- **Header（头部）**：包含 Hash 算法（如 `alg: HS256`）和 Token 类型（如 `typ: JWT`）。
- **Payload（载荷）**：包含需要携带的会话数据（如 `ID`, `name`, `iat`）。
- **Signature（签名）**：签名原理与刚刚的 Cookie 签名类似。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_028_6a53cdc6-e495-449f-8db0-f236ee656c3b.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_029_679de1e7-4116-49de-b802-0a045f6f05ca.jpg)
![](./Cookie、Session、Token、JWT一次性讲完/screenshot_030_844454e7-8aa5-4698-8cfd-12038a5b6b31.jpg)

这样生成的 Token：
- 可以携带数据。
- 可以用来作为会话凭证。
- 用规范解析，性能好。

**安全提示：**
- 虽然 JWT 生成的 Token 看起来是加密的，但其实任何人都是可以解开（Base64 解码）的。
- 所以和 Cookie 一样，敏感信息（如密码）千万不要写到 JWT 的 Payload 里。

![](./Cookie、Session、Token、JWT一次性讲完/screenshot_031_8f39ba1c-6dba-4970-b07f-8a522c939bf2.jpg)

## AI 总结

本视频以通俗易懂的方式讲解了 Web 身份认证的演变过程。首先，为了解决用户区分问题，引入了浏览器自动管理的 **Cookie** 机制，但明文 Cookie 容易被篡改，因此加入了**数据签名**。随后为了减少客户端数据量，发展出将数据存在服务端、只给客户端返回 ID 的 **Session** 机制。在移动互联网多端环境下，针对非浏览器端没有 Cookie 的问题，演变出了手动维护并放在 Header 中发送的 **Token**。最后，为了解决分布式系统下 Session 状态的存储压力（实现无状态），引出了标准化、可携带定制数据的 **JWT (JSON Web Token)**，并特别强调了 JWT 仅是 Base64 编码而非加密，切忌存放敏感信息。