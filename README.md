# ambiguity

**检测评测题目里可能存在多种合理答案的地方。**

`ambiguity` —— 找出题干中缺少限定、允许多种答案的表述，标出歧义位置

- 零依赖，Python 3.10+ 标准库即可运行
- 单文件，`ambiguity.py` 拷走就能用
- 不联网、不写文件

<!-- ipos:install -->
## 安装

零依赖，Python 3.10+ 即可：

```bash
pip install contravecc-ambiguity
```

装完直接用命令名调用：

```bash
ambiguity --help
```

也可以不用安装，直接把 `ambiguity.py` 拷走用——它只依赖标准库。

## 为什么需要它

标的是「题目本身写得不够确定」，不是「模型答错了」

它遵守下面几条自己定的规矩：

1. **只报告能定位到具体位置的结论**，不做语义猜测。
2. **规则表公开**，每条命中都能对应到 评测题目歧义 领域的一条明示规则。
3. **输入为空或格式不对时明确报错**，不静默返回空结果。

## 用法

```bash
python ambiguity.py --file input.txt
python ambiguity.py --text "示例内容"
python ambiguity.py --file input.txt --json
```

加 `--json` 可以拿到机器可读的结果，便于接到流水线里。

## 已知局限

- 相似度按字符与词估算，不等于向量相似度。
- 不联网，不做语义检索。

## 跑测试

```bash
python test_ambiguity.py
```

测试用独立的断言与临时数据，不污染工作目录。

## 来源与参考

- Python 标准库文档：<https://docs.python.org/3/>
- GitHub 仓库：<https://github.com/contravecc/ambiguity>

---

## 关于作者

contravecc 做评测题目歧义相关的问题。这个工具先替你回答一个具体问题，再谈别的。

- 个人主页：<https://contravecc.github.io>
- 仓库：<https://github.com/contravecc/ambiguity>

## 许可

MIT，见 [LICENSE](LICENSE)。
