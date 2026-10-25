## Security-Privacy-Cryptography

云服务安全从完整数据流看边界：数据库主存储、控制平面、日志、工单与分析副本分别审查，见 [云数据库的控制平面与旁路数据安全](#云数据库的控制平面与旁路数据安全)。

### 密码学在计算机领域的应用

#### hash function
##### 1.性质

- Deterministic: the same input always generates the same output.
- Non-invertible: it is hard to find an input `m` such that `hash(m) = h` for some desired output `h`.
- Target collision resistant: given an input `m_1`, it’s hard to find a different input `m_2` such that `hash(m_1) = hash(m_2)`.
- Collision resistant: it’s hard to find two inputs `m_1` and `m_2` such that `hash(m_1) = hash(m_2)` (note that this is a strictly stronger property than target collision resistance).

注意区分Target collision resistant和Collision resistant


##### 2.原理

```c++
int sum=0; 
for(int i=0; i<v.size(); ++i) sum=sum*131+v[i]; 
return sum;
```

* 对`vector<int>`做hash的方法：

  I. 用上面的方法，选取质数131，可能需要再设另一个质数取模

  II. 两个或三个的简单情形，可以利用pair和map

  III. 对于每一个整数， 把0\~7、8\~15、 16\~23、 24\~31的位置取出来变成char，cat之后再hash

* 方法I中取模用质数更好的原因

  * “ 如果p是一个质数，n是任意非零整数（不是p的倍数）， 那么px+ny=z对于任意的x,y,z都有解”， 这样可以保证取模相对均匀一些， 避免所谓的 primary clustering， 要证明这个需要引理：“方程 ax+by=1 有整数解当且仅当 a 和 b 互质”
* 哈希算法可能用到乘除法。模素数的剩余系除去 0 ，这个集合关于乘法构成群。只有群才能保证每个元素都有逆元，除法才能合法。假设要计算 (p / q) mod m，如果想让结果与 (p mod m) / (q mod m) 相等，必须令 m 为素数，否则逆元求不出来。

##### 3.应用
* Git中的id是由SHA-1 hash生成，40个16进制字符
  * SHA-1: 160bit 
  * SHA-2: 有不同位数，比如SHA-256
  * `$ printf 'hello' | sha1sum`

* [Commitment scheme](https://en.wikipedia.org/wiki/Commitment_scheme)



### Security and Cryptography

> [6.NULL Security and Cryptography](https://missing.csail.mit.edu/2020/security/)

[Cryptographic Right Answers](https://latacora.micro.blog/2018/04/03/cryptographic-right-answers.html)

#### Intro

##### Entropy
online guessing - 40 bits of entropy

offline guessing - 80 bits of entropy

##### Hash functions

 [lifetimes of cryptographic hash functions](https://valerieaurora.org/hash.html) 

##### Key derivation functions(KDFs)

应用：

- Producing keys from passphrases for use in other cryptographic algorithms (e.g. symmetric cryptography, see below).
- Storing login credentials. Storing plaintext passwords is bad; the right approach is to generate and store a random [salt](https://en.wikipedia.org/wiki/Salt_(cryptography)) `salt = random()` for each user, store `KDF(password + salt)`, and verify login attempts by re-computing the KDF given the entered password and the stored salt.

#### Symmetric cryptography

应用：

- Encrypting files for storage in an untrusted cloud service. This can be combined with KDFs, so you can encrypt a file with a passphrase. Generate `key = KDF(passphrase)`, and then store `encrypt(file, key)`.

```sh
openssl aes-256-cbc -salt -in {input filename} -out {output filename}
openssl aes-256-cbc -d -in {input filename} -out {output filename}
```



#### Asymmetric cryptography

用private key来sign，用public key来encrypt

- [PGP email encryption](https://en.wikipedia.org/wiki/Pretty_Good_Privacy). People can have their public keys posted online (e.g. in a PGP keyserver, or on [Keybase](https://keybase.io/)). Anyone can send them encrypted email.
- Private messaging. Apps like [Signal](https://signal.org/) and [Keybase](https://keybase.io/) use asymmetric keys to establish private communication channels.
- Signing software. Git can have GPG-signed commits and tags. With a posted public key, anyone can verify the authenticity of downloaded software.

* Key distribution: Asymmetric-key cryptography is wonderful, but it has a big challenge of distributing public keys / mapping public keys to real-world identities. There are many solutions to this problem. Signal has one simple solution: trust on first use, and support out-of-band public key exchange (you verify your friends’ “safety numbers” in person). PGP has a different solution, which is [web of trust](https://en.wikipedia.org/wiki/Web_of_trust). Keybase has yet another solution of [social proof](https://keybase.io/blog/chat-apps-softer-than-tofu) (along with other neat ideas). Each model has its merits; we (the instructors) like Keybase’s model.

应用：

* In use, once the server knows the client’s public key (stored in the `.ssh/authorized_keys` file), a connecting client can prove its identity using asymmetric signatures. This is done through [challenge-response](https://en.wikipedia.org/wiki/Challenge–response_authentication). At a high level, the server picks a random number and sends it to the client. The client then signs this message and sends the signature back to the server, which checks the signature against the public key on record. This effectively proves that the client is in possession of the private key corresponding to the public key that’s in the server’s `.ssh/authorized_keys` file, so the server can allow the client to log in.
* [Set up GPG](https://www.digitalocean.com/community/tutorials/how-to-use-gpg-to-encrypt-and-sign-messages)

[在Github上使用GPG的全过程 - 林溪的文章 - 知乎](https://zhuanlan.zhihu.com/p/76861431)

```sh
sudo apt-get install gnupg
gpg --gen-key
gpg --output ~/revocation.crt --gen-revoke your_email@address.com
chmod 600 ~/revocation.crt

gpg --import name_of_pub_key_file
https://pgp.mit.edu/

gpg --keyserver pgp.mit.edu  --search-keys search_parameters
gpg --fingerprint your_email@address.com

# 信任（用自己的密钥为其签名验证）
gpg --sign-key email@example.com
gpg --output ~/signed.key --export --armor email@example.com
gpg --import ~/signed.key

gpg --output ~/mygpg.key --armor --export your_email@address.com

gpg --keyserver pgp.mit.edu  --send-keys ...
gpg --keyserver pgp.mit.edu  --recv-keys ...

gpg --encrypt --sign --armor -r person@email.com name_of_file
# 如果想自己decrypt，需要第二个-r recipient
gpg file_name.asc

gpg --list-keys
gpg --refresh-keys

gpg --keyserver key_server --refresh-keys

```

Git and GPG
```sh
git config --global user.signingkey {key_id}
git config --global commit.gpgsign true

git commit -S
git tag -s

git log/show --show-signature
git tag -v
```

信任Github所用的GPG密钥，使本地确认在Github网页端进行的操作的真实性
```sh
curl https://github.com/web-flow.gpg | gpg --import
gpg --sign-key 4AEE18F83AFDEB23
```

### Security and Privacy

> [6.NULL Security and Privacy](https://missing.csail.mit.edu/2019/security/)

#### Intro

Follow the [right people](https://heimdalsecurity.com/blog/best-twitter-cybersec-accounts/)

使用安全的密码管理器，比如[1password](https://1password.com/), [KeePass](https://keepass.info/), [KeePass](https://keepass.info/), [`pass`](https://www.passwordstore.org/)

更安全的two-factor authentication双因素认证：a [FIDO/U2F](https://fidoalliance.org/) dongle (a [YubiKey](https://www.yubico.com/quiz/) for example, which has [20% off for students](https://www.yubico.com/why-yubico/for-education/)). TOTP (like Google Authenticator or Duo) will also work in a pinch, but [doesn’t protect against phishing](https://twitter.com/taviso/status/1082015009348104192). SMS is pretty much useless unless your threat model only includes random strangers picking up your password in transit. 

* [SMS's issue](https://www.kaspersky.com/blog/2fa-practical-guide/24219/)

##### General Security Advice

Tech Solidarity has a pretty great list of [do’s and don’ts for journalists](https://techsolidarity.org/resources/basic_security.htm) that has a lot of sane advice, and is decently up-to-date. @thegrugq also has a good blog post on [travel security advice](https://medium.com/@thegrugq/stop-fabricating-travel-security-advice-35259bf0e869) that’s worth reading. We’ll repeat much of the advice from those sources here, plus some more. Also, get a [USB data blocker](https://amzn.com/B00QRRZ2QM), because [USB is scary](https://www.bleepingcomputer.com/news/security/heres-a-list-of-29-different-types-of-usb-attacks/).



#### Private Communication

Use [Signal](https://www.signal.org/) ([setup instructions](https://medium.com/@mshelton/signal-for-beginners-c6b44f76a1f0). [Wire](https://wire.com/en/) is [fine too](https://www.securemessagingapps.com/); WhatsApp is okay; [don’t use Telegram](https://twitter.com/bascule/status/897187286554628096) (不错的文章)). Desktop messengers are pretty broken (partially due to usually relying on Electron, which is a huge trust stack).

E-mail is particularly problematic, even if PGP signed. It’s not generally forward-secure, and the key-distribution problem is pretty severe. [keybase.io](https://keybase.io/) helps, and is useful for a number of other reasons. Also, PGP keys are generally handled on desktop computers, which is one of the least secure computing environments. Relatedly, consider getting a Chromebook, or just work on a tablet with a keyboard.



#### File Security

File security is hard, and operates on many level. What is it you’re trying to secure against?

[![$5 wrench](Security-Privacy-Cryptography/security.png)](https://xkcd.com/538/)

- Offline attacks (someone steals your laptop while it’s off): turn on full disk encryption. ([cryptsetup + LUKS](https://wiki.archlinux.org/index.php/Dm-crypt/Encrypting_a_non-root_file_system) on Linux, [BitLocker](https://fossbytes.com/enable-full-disk-encryption-windows-10/) on Windows, [FileVault](https://support.apple.com/en-us/HT204837) on macOS. Note that this won’t help if the attacker *also* has you and really wants your secrets.

- Online attacks (someone has your laptop and it’s on): use file encryption. There are two primary mechanisms for doing so    

  - Encrypted filesystems: stacked filesystem encryption software  encrypts files individually rather than having encrypted block devices.  You can “mount” these filesystems by providing the decryption key, and  then browse the files inside it freely. When you unmount it, those files are all unavailable.  Modern solutions include [gocryptfs](https://github.com/rfjakob/gocryptfs) and [eCryptFS](http://ecryptfs.org/). More detailed comparisons can be found [here](https://nuetzlich.net/gocryptfs/comparison/) and [here](https://wiki.archlinux.org/index.php/disk_encryption#Comparison_table)
  - Encrypted files: encrypt individual files with symmetric encryption (see `gpg -c`) and a secret key. Or, like `pass`, also encrypt the key with your public key so only you can read it back later with your private key. Exact encryption settings matter a lot!

- [Plausible deniability](https://en.wikipedia.org/wiki/Plausible_deniability) (what seems to be the problem officer?): usually lower performance, and easier to lose data. Hard to actually prove that it provides [deniable encryption](https://en.wikipedia.org/wiki/Deniable_encryption)! See the [discussion here](https://security.stackexchange.com/questions/135846/is-plausible-deniability-actually-feasible-for-encrypted-volumes-disks), and then consider whether you may want to try [VeraCrypt](https://www.veracrypt.fr/en/Home.html) (the maintained fork of good ol’ TrueCrypt).

- Encrypted backups: use  [Tarsnap](https://www.tarsnap.com/) or [Borgbase](https://www.borgbase.com/)

  - Think about whether an attacker can delete your backups if they get a hold of your laptop!

#### 进程安全

##### 最小权限原则

**核心原则**: 任何程序、任何用户都只应拥有其完成任务所必需的最小权限 (Principle of Least Privilege)。以 root 用户运行服务是极大的安全风险。

*   **应用服务 (Tomcat, Redis, Kafka)**: **绝对不应该**以 root 身份运行。
    *   **原因**: 这些服务完全不需要 root 权限。如果服务本身或其上运行的应用被攻破，攻击者将直接获得整个服务器的 root 权限。
    *   **特例**: 如果服务需要监听特权端口（< 1024，如80端口），可以 root *启动*，但必须在端口绑定后立即**降权**，将工作进程切换到低权限用户（如 `www-data`）运行。

*   **系统/安全服务 (HostGuard)**: **通常必须**以 root 身份运行。
    *   **原因**: 其核心功能（如监控所有进程、管理防火墙、扫描文件系统）要求必须具备系统级的最高权限才能有效执行。

#### Internet Security & Privacy

The internet is a *very* scary place. Open WiFi networks [are](https://www.troyhunt.com/the-beginners-guide-to-breaking-website/) [scary](https://www.troyhunt.com/talking-with-scott-hanselman-on/). Make sure you delete them afterwards, otherwise your phone will happily announce and re-connect to something with the same name later!

If you’re ever on a network you don’t trust, a VPN *may* be worthwhile, but keep in mind that you’re trusting the VPN provider *a lot*. Do you really trust them more than your ISP? If you truly want a VPN, use a provider you’re sure you trust, and you should probably pay for it. Or set up [WireGuard](https://www.wireguard.com/) for yourself – it’s [excellent](https://latacora.micro.blog/there-will-be/)!

If you’re particularly privacy-oriented, [privacytools.io](https://privacytools.io) is also a good resource.

Some of you may wonder about [Tor](https://www.torproject.org/). Keep in mind that Tor is *not* particularly resistant to powerful global attackers, and is weak against traffic analysis attacks. It may be useful for hiding traffic on a small scale, but won’t really buy you all that much in terms of privacy. You’re better off using more secure services in the first place (Signal, TLS + certificate pinning, etc.).


##### 常见高危端口

在网络安全中，某些端口因其关联的服务非常核心或存在固有弱点，而成为攻击者的重点扫描和攻击目标。

*   **21 (FTP - 文件传输协议)**: 主要风险在于其默认以**明文传输**数据和用户凭证，极易被网络嗅探工具截获。
*   **22 (SSH - 安全外壳协议)**: 协议本身安全，但作为服务器远程管理的主要入口，是**暴力破解攻击**的常见目标。安全策略包括：禁用密码登录（改用密钥）、禁止root直接登录、更改默认端口。
*   **3389 (RDP - 远程桌面协议)**: Windows远程桌面服务的默认端口。因其广泛使用和通常具备高权限，是勒索软件和黑客攻击的重点目标。
*   **3306 (MySQL)**: MySQL数据库服务的默认端口。直接暴露在公网是极大的安全隐患，容易导致数据泄露或被攻击。


#### Web Security

> 架构层补充来源：[Cloudflare Project Glasswing](https://blog.cloudflare.com/cyber-frontier-models/)。漏洞防御不能只优化 patch 速度；更重要的是让 bug 存在时也难以被利用：在应用前用输入验证、WAF / protocol guard 阻断可达路径；用最小权限与组件隔离限制单点缺陷的横向影响；用统一 rollout 让修复同时抵达所有运行实例。披露窗口的风险更接近 `external reachability × blast radius × rollout inconsistency`，而不只是 `time-to-patch`。完整 agent 漏洞发现与验证漏斗见 [Cloudflare Vulnerability Harness](./AI-Applied-Algorithms.md#cloudflare-vulnerability-harness从-security-skill-到跨仓库控制面)。

So, you want to go on the Web too? Jeez, you’re really pushing your luck here.

Install [HTTPS Everywhere](https://www.eff.org/https-everywhere). SSL/TLS is [critical](https://www.troyhunt.com/ssl-is-not-about-encryption/) (已读, **Login Landing Page Must Use SSL**), and it’s *not* just about encryption, but also about being able to verify that you’re talking to the right service in the first place! If you run your own web server, [test it](https://www.ssllabs.com/ssltest/index.html). TLS configuration [can get hairy](https://wiki.mozilla.org/Security/Server_Side_TLS). HTTPS Everywhere will do its very best to never navigate you to HTTP sites when there’s an alternative. That doesn’t save you, but it helps. If you’re truly paranoid, blacklist any SSL/TLS CAs that you don’t absolutely need.

Install [uBlock Origin](https://github.com/gorhill/uBlock). It is a [wide-spectrum blocker](https://github.com/gorhill/uBlock/wiki/Blocking-mode) that doesn’t just stop ads, but all sorts of third-party communication a page may try to do. And inline scripts and such. If you’re willing to spend some time on configuration to make things work, go to [medium mode](https://github.com/gorhill/uBlock/wiki/Blocking-mode:-medium-mode) or even [hard mode](https://github.com/gorhill/uBlock/wiki/Blocking-mode:-hard-mode). Those *will* make some sites not work until you’ve fiddled with the settings enough, but will also significantly improve your online security.

If you’re using Firefox, enable [Multi-Account Containers](https://support.mozilla.org/en-US/kb/containers). Create separate containers for social networks, banking, shopping, etc. Firefox will keep the cookies and other state for each of the containers totally separate, so sites you visit in one container can’t snoop on sensitive data from the others. In Google Chrome, you can use [Chrome Profiles](https://support.google.com/chrome/answer/2364824) to achieve similar results.


### 云数据库的控制平面与旁路数据安全

来源：[冯若航《疑 TiDB Cloud 数据泄漏：10.6TB》](https://mp.weixin.qq.com/s/c3tpXAjV3RhqIMY4Soz-Aw)（老冯云数，2026-10-20 发布，页面标注 10-21 修改；2026-10-21 读取）与[平凯星辰网络安全事件情况说明公告](https://pingkai.cn/trust/security/updates/2026-10-20)。技术原则另对照 [OWASP Logging](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#data-to-exclude)、[Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html) 与 [Cryptographic Storage](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)。

云数据库的安全边界覆盖“谁能管理数据库”和“数据还被复制到了哪里”。即使数据库引擎本身没有漏洞，控制台、迁移任务、SQL 编辑器、技术支持、计费与分析系统仍需独立审查。以下从争议事件提炼威胁模型，不把攻击者陈述当作已确认根因。

#### 事件声明与证据边界

| 来源 | 本次实际读到的内容 | 能支持的判断与限制 |
| --- | --- | --- |
| 公众号转述的 FulcrumSec 声明 | 声称窃取 10.6 TB、涉及约 18 万租户组织、115,308 对控制台 API 密钥（其中 42,612 对活跃）、约 2,065 万条 SQL、约 1.02 亿次网关连接记录及 413 个私有仓库；声称首批释放解压后约 200 GB。 | 这些数字、密钥有效性、受影响租户范围均为攻击者单方声称，未通过独立取证核验。客户出现在经营或日志记录中，也不等于其整个生产数据库已被攻破。 |
| 公众号转述的入侵过程 | 声称利用仓库中的云服务身份凭证，在 2026-09-08 至 09-30 每六小时导出一次控制平面，共 88 次，最后一次为 09-30 06:02 UTC；另引用一份据称来自 2022 年的组织成员重置 root 密码问题工单。 | 这是待核验的攻击路径和时间线。历史工单不能单独证明问题一直未修复；“没有触发告警”也未取得独立监控证据。组织内越权与跨租户越权应分别核验。 |
| 平凯星辰 2026-10-20 官方公告 | 确认部分内部经营数据遭未经授权访问并泄露，涉及部分销售线索、订单及需求单；称已采取处置、消除相关风险。公告称事件不涉及平凯数据库企业版、平凯数据库云服务等产品漏洞和缺陷，不影响客户数据库系统和业务数据安全。 | 确认的是厂商承认内部经营数据事件。其对客户影响和风险消除的表述仍是厂商声明；该公告未逐项解释攻击者所称的控制平面、客户凭证和 SQL 范围，也不能自动代表全球 TiDB Cloud 的全部产品与区域。 |

本次读到公众号渲染正文及其攻击者公告截图、官方公告正文；攻击者原站、泄露数据包、私有仓库和内部工单原件未读取，未验证任何披露的凭证。两方声明的影响范围存在冲突，当前材料不足以认定完整根因。作者对云数据库普遍风险的担忧属于评论，不能据此推导所有托管数据库均已失守。

#### 从事件线索提炼防御边界

下表中“事件线索”均来自公众号对攻击者声明的转述；工程边界是据此提出的审查问题，不是对涉事系统现状的认定。

| 事件线索 | 应检查的工程边界 |
| --- | --- |
| 仓库中的云凭证被用于持续导出 | 服务身份按任务与资源授予最小权限；审查导出、复制和订阅配置的创建权限、接收端与存续时间。撤销入口凭证后，还要核对已创建的数据通道是否终止。 |
| 控制台 API 密钥、迁移源库账号及集群凭证集中存储 | 控制平面保存的可能是通往数据面的能力，而不只是元数据。分别检查凭证可读性、解密权限、备份访问和轮换；租户与项目边界不能只靠客户端传入的标识。 |
| SQL 编辑器、Chat2Query、慢查询日志和支持附件保留原始 SQL 或连接串 | SQL 文本可能含业务数据、密码或外部平台令牌。排障上传、日志采集、分析入仓和工单附件均应最小采集、入口脱敏、限制读取与留存；不能只保护数据库主副本。 |
| 信任请求头身份、模拟登录例外、低权限角色可重置高权限账号 | 鉴权绑定可信身份；每次访问都核对主体、角色、租户和资源关系。计费、审计、支持与数据库管理权限分离；特权操作要覆盖无权限、跨租户及过期授权的拒绝场景。 |
| 静态 IV、共享解密秘密 | 加密算法名称不代表密钥管理安全。使用成熟库和认证加密，按所选模式满足 nonce / IV 要求；隔离密钥与密文、限制解密权限。共享主密钥可能扩大影响，但仅凭该描述不能证明所有密码已被解密。 |
| 计费成本、CRM、收入记录与租户标签可关联；分析标识可映射到实名 | 经营数据也包含商业秘密；可关联的哈希标识属于假名化线索，不能直接视为匿名。分别治理采集目的、关联权限、第三方处理方和保留期限，不复制客户名单或个人档案作为案例证明。 |
| 大量、周期性导出据称未被发现 | 审计云 API、批量读取、复制任务、对象存储外传与异常身份行为，并验证告警能否到达响应人员。EDR、业务可用性监控与数据外传检测承担不同职责。 |

OWASP 的可复用原则是：日志不直接记录令牌、密码、连接串和主密钥等敏感值；秘密管理覆盖创建、授权、审计、轮换、撤销与过期。重启应用不等于撤销已泄露凭证；删除公开副本也不能让已复制的信息失效。应急完成需要核对旧凭证失效、异常数据通道关闭、相关访问日志和下游影响，不能只以“已更新配置”验收。

选型应比较明确的威胁模型和运维责任。托管服务减少自建部署负担，但仍需审查控制平面权限、支持流程和旁路副本；自建则要自行承担补丁、备份、监控、轮换与响应。集中秘密管理和持续审计会增加集成、维护、存储及告警处置成本；本材料没有可比较的成本数据，不能据此断言“下云更安全”或给出节省比例。数据库入口见 [典型场景决策](./Database.md#典型场景决策)，多租户架构入口见 [云原生：多租户系统](./云原生-ToB.md#多租户系统)。

### AI 服务供应链与 Agent 滥用

来源：[Anthropic 威胁情报报告，2026 年 9 月](https://www.anthropic.com/threat-intelligence-report-september-2026)。报告选取 2025 年 12 月至 2026 年 8 月发现并处置的突出案例，属于服务商调查材料，不代表典型使用情况；组织归因与数据流转指控未经本文独立核实。

**AI 放大的既有能力，也有执行规模。** 工具调用、并行 agent、跨会话记忆和反馈重试，让少数操作者能持续处理多个陌生环境。复杂工作流不再能单独证明操作者技术高超；评价增益要分别看速度、规模和能力深度。Agent 评测还需区分请求、生成、执行与现实结果，见 [Agent 评估与安全](./AI-Applied-Algorithms.md#agent-评估与安全)。

#### 供应链既是入口，也是资产

AI API key 和会话令牌有三重价值：转卖获利、使用受害者的计算额度、借合法账户掩盖来源。模型代理、客户端、评测沙箱及其生产凭证因此都进入攻击面。

报告中的代表案例：

- **评测沙箱泄密（GTG-50020）**：Anthropic 称，恶意指令使某 AI 厂商的自动评测沙箱交出其持有的生产 API 密钥。关键边界是“不可信任务内容能否触达真实凭证”，而不仅是模型能否识别恶意请求。
- **伪装低价 AI 服务（GTG-50021）**：报告描述了冒充折扣模型服务、替换实际模型并窃取用户凭证的活动。价格和界面名称都不能证明后端身份与客户端可信性。
- **虚假约会应用（GTG-15001）**：报告称某应用网络使用大量 AI 身份与用户交谈，却宣传真人服务。风险来自规模化运营和身份欺骗，不要求模型先获得突破性能力。

工程原则：生产凭证留在受信执行层，模型侧只得到受限工具或不透明句柄；沙箱按任务授予最小权限，限制网络出口、预算与敏感数据访问。模型拒绝、环境隔离和异常检测分别承担不同职责，不能互相替代。

#### 模型名称不等于数据处理边界

**工程师内部系统案例（GTG-16002）**：Anthropic 称，一名工程师使用 Kimi 开发企业内部系统时提交了内部代码和多家企业的有效访问凭证，相关请求被转发到 Claude。`live credentials` 表示当时仍可用于认证的凭证；公开材料没有说明具体权限，也没有证明这些凭证随后被用于入侵。

这个案例涉及两道独立授权：**允许把数据提交给某服务，不等于允许该服务再转交其他处理方。** 报告对用户是否获告知存在不确定表述，因此不能把所有客户均未获告知、所有请求均被转发写成已证实事实。

调用链可拆为：

```text
用户 → 应用 / 模型路由 → 名义供应商 → 实际推理供应商 → 返回结果
                         └→ 交互保存 / 数据整理 / 训练用途（需分别核验）
```

推理转发、交互留存、用于训练是三种不同处理行为，不能仅凭发生第一种就认定后两种。数据治理应核对实际处理方、路由与 fallback、保存期限、训练用途和删除机制；凭证应在请求、工具参数、日志与附件入口统一脱敏。

#### 反蒸馏与证据边界

蒸馏本身是正常训练方法；报告针对的是未经授权的能力提取及其伴随的账户、凭证和数据滥用。Preserved thinking 通过约束受保护推理之前的上下文改写，缩小诱导模型重新输出推理轨迹的路径；最终答案仍可能提供训练信号，不能据此声称阻止所有蒸馏。协议机制见 [推理记录与上下文绑定](./AI-Applied-Algorithms.md#stealing-reasoning-traces-与-external-thinking推理记录是可提取的侧信道)。

读取威胁报告时保留三条证据纪律：**观察到请求不等于任务成功；使用 AI 不等于证明净增益；封禁账户不等于受害系统恢复。** 服务商案例能揭示具体风险路径，但缺少对照实验与总体分母时，不能据此计算全社会风险增长或模型的因果贡献。

#### 主动模型归因：用生成数字偏差反推后端身份（ModelTrace）

> 来源：[ModelTrace 浏览器本地版](https://xqy2006.github.io/ModelTrace/) 与 [xqy2006/ModelTrace](https://github.com/xqy2006/ModelTrace)（MIT；初版整理基于 commit `3f0dd2f4`，2026-10-25 复核至 [`6cd4a8ff`](https://github.com/xqy2006/ModelTrace/tree/6cd4a8ff0f3f4e49d6d6969dd2fbadfa1569fde2)）。算法与建库见 [`fingerprint.py`](https://github.com/xqy2006/ModelTrace/blob/6cd4a8ff0f3f4e49d6d6969dd2fbadfa1569fde2/fingerprint.py)、[`bank_builder.py`](https://github.com/xqy2006/ModelTrace/blob/6cd4a8ff0f3f4e49d6d6969dd2fbadfa1569fde2/bank_builder.py) 和 [`challenge_suite.py`](https://github.com/xqy2006/ModelTrace/blob/6cd4a8ff0f3f4e49d6d6969dd2fbadfa1569fde2/challenge_suite.py)；前置工作参考 [hlwy-ai-checker](https://github.com/hanlinwenyuan/hlwy-ai-checker)。

上一节 GTG-50021 的边界是「价格和界面名称都不能证明后端身份」。ModelTrace 把这条边界变成可操作的检测：**不问供应商要证据，而是让模型自己产出可统计的偏差**。做法是三条独立的「长整数生成」挑战（每次 218–333 个 `[1, 355]` 区间整数，要求逐项凭第一反应、禁止工具 / 计算器 / 搜索 / 计数递增 / 等差 / 循环 / 重复区块），把输出分布当成指纹，在候选库里做归因。

- **指纹表示**：`355` 维计数分布（取值区间 `[1, 355]`，α = 0.5 平滑）做 Hellinger 特征，叠加有序块特征（序列切 4 段各 16 桶 + 末位数字分布）。总分 `0.75 × Hellinger 模型中心相似度 + 0.25 × 有序块特征`（库内 `ordered_block_weight = 0.25`）。
- **环境去偏是核心设计**：建库时把各共享环境下特征的平均偏移做 SVD，取前 `2` 个方向当 nuisance basis；归因时先投影掉这些方向再与全部模型中心比较。这样「换了 system prompt / 中英文 / 上下文长度」造成的整体位移不会被误算成模型差异。挑战套件预设 12 种环境，并非三组变量的完整笛卡尔积：既有 `clean` 下的 JSON / 中文 / 英文基线，也有 `system / user` 通道中的 96 / 512 / 2048 词中文前缀，以及固定 system prompt 的 JSON 条件。
- **概率与校准**：多份回答分别打分取平均，再用与查询数配套的温度做全局 softmax。当前库中，1 / 2 / 3 次查询的 β 为 `7.1295 / 12 / 12`；grouped cross-validation 分别为 `624/648 = 0.9630`、`646/648 = 0.9969`、`216/216 = 1.0000`。这些数字来自建库数据的分组交叉验证，不是独立真实渠道的 holdout 识别率。家族概率是该家族具体模型概率之和；单次检测要求至少 80 个有效数字。
- **闭集边界**：结果是「当前候选库内、均匀先验」的闭集概率，**库外模型照样会被归到最相似的候选**，这是最常见的误用点。参考库从初版 13 个模型扩到 18 个：原有 GPT 6 个与 Claude 7 个保留，新增 `gpt-6-sol / gpt-6-luna / claude-opus-5-5 / claude-sonnet-5-5 / claude-haiku-5-5`。GPT 采自官方订阅 Codex，Claude 采自第三方中转 OAIPro——**Claude 侧指纹刻画的是那条渠道的行为，不等于官方 API 特征**。
- **参考数据卫生不等于外部效度**：[`validate-reference-data.mjs`](https://github.com/xqy2006/ModelTrace/blob/6cd4a8ff0f3f4e49d6d6969dd2fbadfa1569fde2/codex-plugin/validate-reference-data.mjs) 对部分新增模型检查每模型 36 条、12 种环境各 3 条、记录与输出唯一、解析数量与请求数量之比在 `[0.8, 1.2]`，并锁定 provider / model / CLI / reasoning metadata。这能防止坏样本混入参考库，不能替代跨渠道、同上下文和多语言条件下的独立校准。
- **作者自述的失效条件**：结果仅供参考、不是决定性证据；system prompt 会强烈影响数字偏好，因此在 Claude Code 里测得的结果偏差较大，官方建议不要在 Claude Code 内测试。API 自动测试支持 OpenAI Chat Completions 与 Anthropic Messages 两种格式，Key 只用于当次请求、不落盘。

对工程判断的意义：

- **模型身份是需要主动验证的运行时属性，而不是配置项**：路由、fallback、渠道替换、量化版本差异都会改变实际后端，而客户端能拿到的只有行为，所以「行为统计 + 参考库」是少数可落地的证据形式。
- **它的证据强度由可探测能力决定**：只有三条挑战、闭集候选库、且依赖环境去偏，因此适合当 canary / 可疑信号，不适合当判定结论；把它当开放集识别使用会系统性高估把握度。
- 当前插件的 [`provenance.json`](https://github.com/xqy2006/ModelTrace/blob/6cd4a8ff0f3f4e49d6d6969dd2fbadfa1569fde2/codex-plugin/modeltrace-guard/assets/provenance.json) 明示 `sameContextCalibrated: false`、`multilingualCalibrated: false`。SVD 去除共享环境方向只能减弱已建模的整体偏移，不能把未校准条件变成可靠概率。
- 与上面 [模型名称不等于数据处理边界](#模型名称不等于数据处理边界) 是同一问题的两面：那一节说「名义供应商 ≠ 实际处理方」，这一节给的是「用输出行为反推实际处理方」的一个具体手段。
- 同一指纹库还被封装成任务内监测（按工具调用间隔 fork 快照做后台复测），用于发现**任务进行中后端模型被静默替换**，机制见 [AI-Agent-Engineering.md - ModelTrace Guard](./AI-Agent-Engineering.md#modeltrace-guard把后端模型被静默替换做成任务内可探测信号)。

### 训练完整性：内部篡改与随机故障伪装

> 来源：[2024 年模型训练攻击事件报告](https://keyu-tian-sabotage.github.io/#zh-5)（2026-10-12 发布，2026-10-13 首读，2026-10-14 复核）；版本固定于报告仓库 [`e4292f4`](https://github.com/keyu-tian-sabotage/keyu-tian-sabotage.github.io/blob/e4292f48b3ad69b196b98adf60acdc3c88eb91d0/index.html#L336-L552)。本次更新仅增加转载说明与对应样式，技术正文未变。这是基于受害者陈述、代码节选与报道的事件材料；公开仓库未提供完整攻击源码、内部取证记录或可重放实验。本节提炼技术机制，不将报告中的人员归因、动机或全部损失认定为独立核验事实。

**核心威胁是具有写权限的内部人员改变训练依赖和状态，再让破坏表现得像普通故障。** 不需要模型越狱，也不一定需要外部入侵。攻击入口包括共享权重、已安装的库、进程启动路径、共享挂载盘与部署产物；项目 Git 没有变化，不代表实际训练环境没有变化。

#### 破坏训练不变量的技巧

下表是报告描述的手段；机制对照使用 PyTorch `v2.4.0`，不是对事件实际安装版本的认定。

| 被改变的对象 | 报告描述的技巧与原理 | 为什么常规排障可能被误导 |
| --- | --- | --- |
| T5 权重 / 文本特征链路 | 在张量中混入扰动后恢复原范数。范数衡量数值规模，不能证明方向、坐标关系或语义保持；破坏共享编码器会影响其下游缓存特征与训练。 | 张量 shape、范数仍可能正常，容易先怀疑数据或训练代码。报告称重新下载可信权重后异常消失；这支持检查依赖完整性，不单独证明是谁改的。 |
| 优化器更新方向 | 强制启用 `maximize`，翻转损失梯度的优化方向；部分版本只作用于部分 rank。普通 DDP 同步梯度后，各 rank 仍独立执行优化器，更新规则不同会打破副本一致性。 | 同步成功不保证参数更新一致。Loss 仍在变化，也不等于模型在正确学习；AdamW 的动量与权重衰减使“每一步 loss 必然上升”并不成立。 |
| 梯度裁剪 | 将正常的不放大缩放改成放大梯度，报告中的系数为 2；仍返回裁剪前的 norm。 | 返回值本来就不是裁剪后的 norm，日志可能仍有限、平滑，而真正进入优化器的梯度已改变。不能把“日志没异常”当作裁剪正确。 |
| 算子 / 精度路径 | 报告还描述关闭 Flash / 显存高效注意力、改变 matmul 精度与 TF32 配置。 | 数值、吞吐和显存症状同时改变，容易被解释为性能回退或机器差异；实际影响依版本、硬件、shape 与所选 kernel 而定，不能一概断言必然变慢或 OOM。 |
| 集合通信参与条件 | 极低概率误判某 rank 不属于通信组，使其提前返回而不参与 `all_gather` / `reduce_scatter`。这些操作依赖成员按相容次序共同参与。 | 其余 rank 可能等待、超时或失败，看起来像网络 / NCCL 故障；具体后果依后端与检查机制而定，并非必然静默产生错误结果。 |
| 分布式采样 | 将所有 rank 共享的 `seed + epoch` 换成各进程各自取得的时间种子。正常流程先生成相同全局排列，再按 rank 分片；不同排列破坏互补分片关系。 | 样本可能重复或遗漏、每次重启现象又不同。并不是“所有 rank 的全部随机数必须相同”；约束针对共同排列。报告所称全局 RNG 重置不能仅由所示局部 Generator 节选推出。 |
| 共享盘命令通道 | 把共享目录中的文本解释为命令，结果再写回；报告称通过库初始化路径加载。文件共享由数据面变成了控制面。 | 不依赖新外网连接，只有网络出口监控可能遗漏。执行权限来自训练进程身份，共享盘可写权限由此可能扩展成执行影响。 |
| 训练进程存活 | 按 trial / node 条件终止部分 worker。同步作业依赖其他成员，局部退出可扩散成整个任务中断。 | 故障只落在特定作业或节点，像调度、驱动或硬件问题；故障域与恢复语义取决于框架，不等于失去一张卡只损失该卡的计算。 |
| Checkpoint 加载语义 | 在加载时把 NaN / Inf 替换为 0。该数值操作本身有合法用途，但未经约定静默修补会改变模型状态并遮蔽原始异常。 | “加载成功”不代表状态可信。报告另称 checkpoint 是后门载体，但节选不足以核验其完整执行链，不能直接认定是哪一种反序列化利用。 |
| 已安装依赖及文件元数据 | 替换已安装的 PyTorch 文件，再恢复时间戳、属主和权限等表象；这需要对应写入或提权能力，报告提到使用 sudo。 | 比对项目源码、查看修改时间或重启进程可能都无效。时间戳和权限位不是内容完整性证明，持久化修改会再次被加载。 |

三个机制需要特别区分：

1. **大小保持 ≠ 信息保持。** 两个张量可以满足相同范数，却在方向和逐元素值上完全不同。完整性检查应依据可信来源绑定的内容 digest / 签名，而不是单看统计量。
2. **梯度同步 ≠ 更新同步。** 用 SGD 作简化说明，正常更新为减去梯度，改变方向则变成加上梯度；若同一同步梯度进入不同 rank 的不同更新规则，副本仍会分离。具体 AdamW 机制见[梯度取反](https://github.com/pytorch/pytorch/blob/d990dada86a8ad94882b5c23e859b88c0c255bda/torch/optim/adamw.py#L351-L355)，DDP 各进程独立执行优化步骤见[官方说明](https://docs.pytorch.org/docs/2.4/distributed.html#basics)。
3. **观测位置 ≠ 执行位置。** 正常 norm clipping 的缩放不大于 1；返回值是缩放前的梯度范数。对梯度 `(3, 4)`、阈值 1，正常结果约为 `(0.6, 0.8)`，返回 norm 仍为 5；若实际放大两倍，结果是 `(6, 8)`、norm 为 10，旧日志仍可返回 5。机制见[裁剪源码](https://github.com/pytorch/pytorch/blob/d990dada86a8ad94882b5c23e859b88c0c255bda/torch/nn/utils/clip_grad.py#L74-L100)。

$$
g_{\mathrm{clipped}}=g\cdot\min\left(1,\frac{\mathrm{max\_norm}}{\lVert g\rVert+\varepsilon}\right)
$$

采样也有一个简明反例：全局排列 `[0,1,2,3]` 按两 rank 交错划分为 `[0,2]` 和 `[1,3]`；若第二个 rank 自己生成 `[1,0,3,2]`，其分片变成 `[0,2]`，两者就重复处理同一部分并遗漏另一部分。正常 `DistributedSampler` 也可能为整除而有意 padding，不能把全部重复都归为攻击。机制见[共同种子及按 rank 分片](https://github.com/pytorch/pytorch/blob/d990dada86a8ad94882b5c23e859b88c0c255bda/torch/utils/data/distributed.py#L96-L121)。集合通信的合法成员检查见[源码](https://github.com/pytorch/pytorch/blob/d990dada86a8ad94882b5c23e859b88c0c255bda/torch/distributed/distributed_c10d.py#L773-L777)与 [`all_gather` 提前返回](https://github.com/pytorch/pytorch/blob/d990dada86a8ad94882b5c23e859b88c0c255bda/torch/distributed/distributed_c10d.py#L3095-L3097)；这证明路径可解释，不替代对报告中完整补丁与调用链的核验。

#### 随机故障的外观与验证边界

报告描述的组合是：**低概率触发 + rank / 节点选择 + 非确定性种子 + 持久依赖修改 + 根据排查进展调整行为。** 异常既不覆盖所有机器，也不稳定出现；工程师恢复现场时可能已经不触发，或攻击状态已变化。大规模训练中每次调用概率小，不代表整场实验概率小。

$$
P(\text{至少一次触发})=1-(1-p)^M
$$

这里的公式只是假定独立、同概率触发的直觉模型：例如 `p=2^{-18}`、累计 10 万次机会时，概率约为 31.7%；不是事件实测失败率，各 rank / 调用可能相关，真正的机会数与触发条件未公开。故障定位应保留异常 rank、通信序号、进程退出原因、实际依赖 digest 与样本分片信息，而不只保留一条全局 loss。

报告还描述了另一类完整性问题：[以开源 PixArt 的输出冒充 VAR 训练成果](https://github.com/keyu-tian-sabotage/keyu-tian-sabotage.github.io/blob/e4292f48b3ad69b196b98adf60acdc3c88eb91d0/index.html#L574-L592)。据报告，推理前偷偷加入 `City` 前缀，使相同输入不再直接对应开源模型输出，并将 pipeline 打包成二进制交付。机制是展示身份、实际权重与有效输入脱节；二进制打包本身不证明造假，输出相似性也不是可靠的模型身份鉴定。本次依据正文说明整理，未核验该演示原始产物或图 1 像素。

防御落在可核验的边界，而不是仅要求成员可信：

- **依赖与状态不可随意覆写**：训练镜像、安装库、共享模型和 checkpoint 采用版本化、只读使用与最小写权限；校验基线放在独立受信位置，避免内容和 digest 一起被改。
- **对关键不变量独立观测**：记录实际模块加载路径、依赖版本和内容 digest、有效配置；采样验证分片覆盖，更新后验证副本一致性，裁剪后验证实际 norm。检查策略需匹配 DP / TP / 分片拓扑，不能强求所有参数逐 rank 相同。
- **数据面不自动成为执行面**：共享文件不应因被写入而获得命令权限；加载外来 checkpoint 与部署黑盒产物，分别核对加载行为、权限和来源链。
- **保留可归因的执行记录**：训练 run、权重 / checkpoint digest、部署构建、有效 prompt 与推理日志绑定；Demo 效果不替代训练进展与模型身份。完整性证据与排障记录独立留存、按角色共享，普通 loss spike 或通信超时本身不能反推出恶意攻击。

上层关系：训练可靠性同时依赖算法、数据、通信和软件供应链，见 [LLM-MLSys：跨层诊断](./LLM-MLSys.md#跨层诊断重新检查共同假设与故障边界)。已读报告中文正文与全部技术卡片、核对上述官方代码；未运行攻击代码或独立复现，也未取得内部日志、完整攻击源码、当事人完整回应及司法结论。

### Cryptography I, Stanford University, Dan Boneh

* [coursera课程](https://www.coursera.org/learn/crypto/home/welcome)
* [密码学资源推荐](https://blog.cryptographyengineering.com/useful-cryptography-resources/)
* [A Graduate Course In Applied Cryptography](https://toc.cryptobook.us/)
* [A Computational Introduction to Number Theory and Algebra](https://www.shoup.net/ntb/)



### Potpourri

* [Python沙盒逃逸](https://ciphersaw.me/ctf-wiki/pwn/linux/sandbox/python-sandbox-escape/)
  * `__builtins__`

* SSRF (Server-Side Request Forgery) attack
  * 本质上，不允许访问内网资源即可修复，但可能会被301/302/307/308重定向、DNS重绑定攻破，修复的时候有可能手抖。
  * 方案：可以用安全开发包，从传输层彻底断掉内网请求，提供自定义黑白名单功能

* RCE (Remote Code Execution) attach
  * 根本原因：开发者使用python的eval进行json解析，而本身eval是用来执行一个字符串表达式，并返回表达式的值，这意味着可以执行任何python代码，从而执行系统命令。
  * 方案：通过AST Node类型识别，干掉不安全的执行

* 任意文件读取/下载漏洞
* SQL注入漏洞
  * 编码不规范引发。攻击者拼接SQL片段，通过返回包内容的大小，逐步获取数据库的内容
* [炮打Ollama鉴权机制——为什么CS从业者都需要学习网络安全](https://www.bilibili.com/video/BV1eZ421z79W/)
