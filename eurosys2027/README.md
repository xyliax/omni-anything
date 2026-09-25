# 论文写作工作区

主稿：[paper.pdf](paper.pdf)（[TeX 源文件](main.tex)）；补充材料：[supplement.tex](supplement.tex)。[论文大纲](../docs/PAPER.md)维护章节任务、图件和剩余工作；[AGENTS.md](AGENTS.md)维护写作规则。研究材料见大纲中的文档链接。

需要 `latexmk`、`pdflatex` 和 BibTeX，在本目录运行：

```bash
make paper
make supplement
make check
```

`paper.pdf` 纳入 Git 跟踪；修改正文后运行 `make paper` 或 `make check` 更新它，并与源文件一起提交。`supplement.pdf` 和 `build/` 不入库。`make check` 检查编译与部分格式要求，不能替代人工审阅。

| 路径 | 用途 |
| --- | --- |
| `sections/` | 分章 TeX 正文 |
| `references.bib` | 引用 |
| `figures/` | 作者维护的 Draw.io 和导出 PDF |
| `planning/submission-checklist.md` | 投稿规则与最终检查 |
| `planning/ai-use-log.md` | AI 使用披露记录，仅按需读取 |
| `scripts/` | 编译与格式检查 |
| `vendor/acmart/` | 锁定模板与来源 |

当前原型与已测路径不自动成为最终论文范围；实验配置与协议见 [实验设计](../docs/experiments.md)。论文注册和提交状态以作者或投稿系统为准。
