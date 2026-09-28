#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""conversation-playbook 本地检索

零依赖。只读取本技能目录下的 references/，不访问网络、不读写其他路径。

用法:
    python lookup.py --list                 列出全部类别与条目数
    python lookup.py --cat 09               列出冲突与修复类的全部条目
    python lookup.py --cat conflict         按文件名片段定位类别
    python lookup.py 已读不回                关键词检索，打印完整条目块
    python lookup.py --stage 冷淡            按处境检索（读场景索引）
    python lookup.py --scenario             打印完整场景速查索引
    python lookup.py --files                列出全部参考文件
    python lookup.py --cats                 只列类别名（不展开条目）
"""

import os
import re
import sys

# ---------------------------------------------------------------- 路径

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.normpath(os.path.join(HERE, os.pardir, "references"))

INDEX_FILE = "19-scenario-index.md"

ENTRY = re.compile(r"^####\s+(S-\d{2}-\d{2})\s*[·・]\s*(.+?)\s*$")
SECTION = re.compile(r"^(#{1,3})\s+(.+?)\s*$")
STAGE = re.compile(r"^###\s+(.+?)\s*$")

# 类别号 -> 一句话说明（--cats 用，便于快速定位）
CAT_HINT = {
    "00": "底层原则与自检",
    "01": "开口之前：展示面与自我",
    "02": "开场与破冰",
    "03": "话题延续与防尬聊",
    "04": "信号判读",
    "05": "暧昧升级",
    "06": "邀约与见面",
    "07": "好感表达与关系确认",
    "08": "冷淡、不回、被拒",
    "09": "冲突与修复",
    "10": "长期相处与经营",
    "11": "择偶与筛选",
    "12": "自我修复",
    "13": "边界与同意（判据页）",
    "14": "文字媒介（判据页）",
    "15": "守方视角（被追的一方）",
    "16": "判断依据（可信度）",
    "17": "风险识别（判据页）",
    "18": "手法库（含代价与失效信号）",
    "19": "场景速查索引",
    "20": "跨位置镜像对照",
    "21": "红线清单（无条件优先）",
}


def _setup_stdout():
    """Windows 控制台默认可能是 GBK，强制 UTF-8 以免中文乱码。"""
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def list_ref_files():
    if not os.path.isdir(REFS):
        return []
    return sorted(f for f in os.listdir(REFS) if f.endswith(".md"))


def read(fname):
    with open(os.path.join(REFS, fname), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------- 解析


def parse_entries(fname):
    """返回 [(id, title, body, lineno), ...]，body 为条目块全文（含标题行）。"""
    text = read(fname)
    lines = text.splitlines()
    marks = []
    for i, ln in enumerate(lines):
        m = ENTRY.match(ln)
        if m:
            marks.append((i, m.group(1), m.group(2)))
    out = []
    for idx, (i, eid, title) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        # 在下一个条目标题之前，若遇到一级/二级标题则在此收束
        for j in range(i + 1, end):
            sm = SECTION.match(lines[j])
            if sm and len(sm.group(1)) <= 2:
                end = j
                break
        body = "\n".join(lines[i:end]).rstrip()
        out.append((eid, title, body, i + 1))
    return out


def parse_sections(fname, min_level=2):
    """返回 [(level, title, body, lineno), ...]，用于关键词回退检索。

    min_level 默认为 2：**跳过一级标题**。一级标题的 body 是整个文件，
    若纳入比较，任何关键词都会命中每一篇全文，回退检索会退化成刷屏。
    """
    text = read(fname)
    lines = text.splitlines()
    marks = []
    for i, ln in enumerate(lines):
        m = SECTION.match(ln)
        if m:
            marks.append((i, len(m.group(1)), m.group(2)))
    out = []
    for idx, (i, lvl, title) in enumerate(marks):
        if lvl < min_level:
            continue
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        body = "\n".join(lines[i:end]).rstrip()
        out.append((lvl, title, body, i + 1))
    return out


def parse_stages():
    """把场景索引按 ### 小节切开，返回 [(标题, 正文), ...]。"""
    if INDEX_FILE not in list_ref_files():
        return []
    text = read(INDEX_FILE)
    lines = text.splitlines()
    marks = []
    for i, ln in enumerate(lines):
        m = STAGE.match(ln)
        if m:
            marks.append((i, m.group(1)))
    out = []
    for idx, (i, title) in enumerate(marks):
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(lines)
        out.append((title, "\n".join(lines[i:end]).rstrip()))
    return out


def category_label(fname):
    m = re.match(r"^(\d{2})-(.+)\.md$", fname)
    if m:
        return m.group(1), m.group(2)
    return "", os.path.splitext(fname)[0]


# ---------------------------------------------------------------- 命令


def cmd_cats():
    print("conversation-playbook · 类别总表")
    print("=" * 68)
    for fname in list_ref_files():
        num, slug = category_label(fname)
        hint = CAT_HINT.get(num, "")
        n = len(parse_entries(fname))
        tail = "%d 条" % n if n else "判据页"
        print("%s  %-30s %-8s %s" % (num or "--", slug, tail, hint))
    print("=" * 68)


def cmd_list():
    print("conversation-playbook · 全部类别与条目")
    print("=" * 68)
    total = 0
    for fname in list_ref_files():
        num, slug = category_label(fname)
        ents = parse_entries(fname)
        tag = num if num else "  "
        if ents:
            total += len(ents)
            print("%s  %-30s %d 条" % (tag, slug, len(ents)))
            for eid, title, _b, _l in ents:
                print("        %s  %s" % (eid, title))
        else:
            print("%s  %-30s （判据页，无独立编号条目）" % (tag, slug))
    print("=" * 68)
    print("编号条目合计 %d 条" % total)
    print("用法: --cats ｜ --cat 09 ｜ <关键词> ｜ --stage 冷淡 ｜ --scenario")


def cmd_cat(arg):
    arg = (arg or "").strip()
    if not arg:
        print("用法: lookup.py --cat 09   （或 --cat conflict）")
        return
    targets = []
    for fname in list_ref_files():
        num, slug = category_label(fname)
        if arg == num or (arg.isdigit() and arg.zfill(2) == num) or arg.lower() in slug.lower():
            targets.append(fname)
    if not targets:
        print("未匹配到类别: %r" % arg)
        print("可用: " + ", ".join(list_ref_files()))
        return
    for fname in targets:
        num, slug = category_label(fname)
        print("=" * 68)
        print("【%s】%s  （%s）" % (num, slug, fname))
        print("=" * 68)
        ents = parse_entries(fname)
        if ents:
            for eid, title, body, _l in ents:
                print(body)
                print()
        else:
            print(read(fname))


def cmd_stage(arg):
    """按处境检索：在场景索引的 ### 小节里找最匹配的那一节。"""
    arg = (arg or "").strip()
    stages = parse_stages()
    if not stages:
        print("未找到 %s" % INDEX_FILE)
        return 0
    if not arg:
        print("可用的处境（--stage <关键词>）：")
        for title, _b in stages:
            print("  " + title)
        return 0

    # 常见同义词：让「冷淡」这类说法能落到对应的小节上
    alias = {
        "冷淡": "对方在退", "冷了": "对方在退", "不回": "对方在退",
        "已读不回": "对方在退", "被拒": "对方在退",
        "表白": "该不该确认关系", "确认": "该不该确认关系",
        "邀约": "想推进", "约": "想推进", "升级": "想推进",
        "开场": "刚开始接触", "破冰": "刚开始接触", "第一句": "刚开始接触",
        "焦虑": "我自己的状态", "患得患失": "我自己的状态",
        "吵架": "关系里出问题", "修复": "关系里出问题", "冲突": "关系里出问题",
        "分手": "该不该继续", "筛选": "该不该继续", "止损": "该不该继续",
        "长期": "关系稳定之后", "经营": "关系稳定之后", "疲倦": "关系稳定之后",
        "边界": "边界与判断", "同意": "边界与判断", "越界": "边界与判断",
        "守方": "边界与判断", "被追": "边界与判断",
        "操控": "对方是不是在操控我", "PUA": "对方是不是在操控我",
        "文字": "文字层面", "消息": "文字层面", "发什么": "文字层面",
        "危机": "需要停下来的时候", "危险": "需要停下来的时候",
    }
    key = alias.get(arg, arg)

    scored = []
    for title, body in stages:
        if key and key in title:
            scored.append((1000 - len(title), title, body))
            continue
        n = body.count(key) if key else 0
        if n:
            scored.append((n, title, body))
    if not scored:
        print("没有匹配到处境 %r。" % arg)
        print("可用：")
        for title, _b in stages:
            print("  " + title)
        return 0
    scored.sort(key=lambda x: -x[0])
    for _s, title, body in scored[:3]:
        print(body)
        print()
    return 0


def cmd_search(kw):
    """先精确匹配条目块，命中则打印全文；否则回退到章节级命中。"""
    kw_l = kw.lower()
    entry_hits = []
    section_hits = []
    for fname in list_ref_files():
        num, slug = category_label(fname)
        for eid, title, body, lineno in parse_entries(fname):
            if kw_l in title.lower() or kw_l in body.lower():
                entry_hits.append((num, fname, eid, title, body))
        for lvl, title, body, lineno in parse_sections(fname):
            if kw_l in title.lower() or kw_l in body.lower():
                section_hits.append((num, fname, lvl, title, body, lineno))

    if entry_hits:
        print("命中 %d 个条目（关键词: %s）" % (len(entry_hits), kw))
        for num, fname, eid, title, body in entry_hits:
            print("-" * 68)
            print("[%s] %s" % (num, fname))
            print(body)
            print()
        return

    if section_hits:
        # 最深层级优先（h3 比 h2 精确），同类只保留前若干条，避免刷屏
        section_hits.sort(key=lambda h: (-h[2], h[0], h[5]))
        section_hits = section_hits[:8]
        print("未命中编号条目，以下是相关章节（关键词: %s，共 %d 处）"
              % (kw, len(section_hits)))
        for num, fname, lvl, title, body, lineno in section_hits:
            print("-" * 68)
            print("[%s] %s  L%d  %s" % (num, fname, lineno, title))
            print(body[:1200])
            if len(body) > 1200:
                print("……（此处截断，完整内容见 %s L%d）" % (fname, lineno))
            print()
        return

    print("没有匹配到 %r。" % kw)
    print("可以试试: 开场 / 邀约 / 已读不回 / 同意 / 道歉 / 表白 / 留白 /")
    print("          操控 / 代价 / 患得患失 / 仪式感 / 拒绝 / 目标")
    print("或先运行: lookup.py --cats")


def cmd_scenario():
    if INDEX_FILE not in list_ref_files():
        print("未找到 %s" % INDEX_FILE)
        return
    print(read(INDEX_FILE))


def cmd_files():
    for fname in list_ref_files():
        num, slug = category_label(fname)
        print("%s  %s" % (num or "--", fname))


USAGE = __doc__


def main(argv):
    _setup_stdout()
    if not argv:
        print(USAGE)
        return 0
    a0 = argv[0]
    if a0 in ("-h", "--help"):
        print(USAGE)
        return 0
    if a0 == "--list":
        cmd_list()
        return 0
    if a0 == "--cats":
        cmd_cats()
        return 0
    if a0 == "--files":
        cmd_files()
        return 0
    if a0 == "--scenario":
        cmd_scenario()
        return 0
    if a0 == "--stage":
        return cmd_stage(argv[1] if len(argv) > 1 else "")
    if a0 == "--cat":
        cmd_cat(argv[1] if len(argv) > 1 else "")
        return 0
    cmd_search(" ".join(argv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
