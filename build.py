#!/usr/bin/env python3
"""
静态博客生成器 - 把 Markdown 文章变成 HTML 网站
用法: python3 build.py
"""
import os
import re
import yaml
import markdown
from pathlib import Path

# ========== 配置 ==========
SITE_NAME = "私人博客"
SITE_DESC = "用文字记录生活"
SITE_URL = ""  # 部署后填入，如 https://312651739-sexy.github.io/my-blog
ARTICLES_DIR = "articles"
OUTPUT_DIR = "docs"
PER_PAGE = 10

# ========== 读取文章 ==========
def load_articles():
    articles = []
    art_dir = Path(ARTICLES_DIR)
    if not art_dir.exists():
        return articles
    for f in sorted(art_dir.glob("*.md")):
        text = f.read_text(encoding='utf-8')
        # 解析 front matter
        if text.startswith('---'):
            parts = text.split('---', 2)
            if len(parts) >= 3:
                meta = yaml.safe_load(parts[1]) or {}
                body = parts[2].strip()
            else:
                meta = {}
                body = text
        else:
            meta = {}
            body = text

        slug = f.stem  # 文件名作为 slug
        html = markdown.markdown(body, extensions=['extra', 'toc', 'nl2br', 'sane_lists'])
        articles.append({
            'title': meta.get('title', slug),
            'date': meta.get('date', ''),
            'pinned': meta.get('pinned', False),
            'summary': meta.get('summary', ''),
            'content': body,
            'html': html,
            'slug': slug,
            'reading_time': max(1, len(body) // 500),
        })
    # 置顶的排前面，然后按日期排
    articles.sort(key=lambda a: (not a['pinned'], a['date']), reverse=True)
    return articles


# ========== HTML 模板 ==========
STYLE = """
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#faf9f7;--card:#fff;--text:#1c1917;--text2:#78716c;--muted:#a8a29e;--primary:#b45309;--primary-h:#92400e;--primary-l:#fef3c7;--border:#e7e5e4;--radius:12px;--radius-sm:8px;--font:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif;--mono:'SF Mono','Fira Code',Menlo,monospace}
html{scroll-behavior:smooth}
body{font-family:var(--font);background:var(--bg);color:var(--text);line-height:1.7;-webkit-font-smoothing:antialiased}
a{color:var(--primary);text-decoration:none;transition:color .2s}
a:hover{color:var(--primary-h)}

.nav{position:sticky;top:0;z-index:100;background:rgba(250,249,247,.85);backdrop-filter:blur(12px);border-bottom:1px solid #f5f5f4;padding:0 1.5rem}
.nav-inner{max-width:900px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:56px}
.nav-brand{display:flex;align-items:center;gap:.4rem;font-weight:700;font-size:1.1rem;color:var(--text)}
.nav-brand span:first-child{color:var(--primary);font-size:1.2rem}
.nav-links{display:flex;gap:.2rem}
.nav-link{padding:.4rem .75rem;border-radius:var(--radius-sm);font-size:.85rem;color:var(--text2);transition:all .2s}
.nav-link:hover{color:var(--text);background:#f5f5f4}

.hero{padding:4rem 1.5rem 2.5rem;text-align:center;background:linear-gradient(180deg,#fffbeb 0%,var(--bg) 100%)}
.hero h1{font-size:clamp(1.6rem,4vw,2.5rem);font-weight:800;letter-spacing:-.02em;margin-bottom:.6rem}
.hero p{color:var(--text2);font-size:1rem;margin-bottom:1.2rem}
.hero a{display:inline-block;padding:.6rem 1.4rem;background:var(--primary);color:#fff;border-radius:99px;font-weight:600;font-size:.9rem;transition:all .2s}
.hero a:hover{background:var(--primary-h);color:#fff;transform:translateY(-1px)}

.container{max-width:900px;margin:0 auto;padding:2rem 1.5rem 4rem}
.container-narrow{max-width:720px}

.card{display:block;background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:1.4rem;transition:all .25s;color:var(--text);position:relative}
.card:hover{border-color:var(--primary);box-shadow:0 4px 12px rgba(0,0,0,.08);transform:translateY(-2px);color:var(--text)}
.card+.card{margin-top:1rem}
.card-pin{position:absolute;top:.8rem;right:.8rem;background:var(--primary-l);color:var(--primary);font-size:.72rem;padding:.15rem .5rem;border-radius:99px;font-weight:600}
.card h2{font-size:1.15rem;font-weight:700;line-height:1.4;margin-bottom:.5rem}
.card p{color:var(--text2);font-size:.88rem;line-height:1.6;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;margin-bottom:.8rem}
.card-meta{display:flex;gap:.8rem;color:var(--muted);font-size:.78rem}

.article{background:var(--card);border-radius:var(--radius);padding:2rem 2.5rem;border:1px solid var(--border)}
.back{font-size:.82rem;color:var(--text2);display:inline-block;margin-bottom:1.2rem}
.back:hover{color:var(--primary)}
.article h1{font-size:clamp(1.4rem,3vw,2rem);font-weight:800;line-height:1.3;margin-bottom:.8rem}
.article-meta{color:var(--muted);font-size:.82rem;margin-bottom:1.8rem;padding-bottom:1.2rem;border-bottom:1px solid #f5f5f4;display:flex;gap:.5rem;flex-wrap:wrap}
.article-body{font-size:1.02rem;line-height:1.9}
.article-body h1,.article-body h2,.article-body h3{margin:1.6em 0 .5em;font-weight:700;line-height:1.3}
.article-body h2{font-size:1.35rem}
.article-body h3{font-size:1.1rem}
.article-body p{margin-bottom:1em}
.article-body blockquote{border-left:3px solid var(--primary);padding:.4rem .9rem;margin:1em 0;background:var(--primary-l);border-radius:0 var(--radius-sm) var(--radius-sm) 0;color:var(--text2)}
.article-body code{background:#f5f5f4;padding:.12em .35em;border-radius:4px;font-family:var(--mono);font-size:.86em}
.article-body pre{background:#1c1917;color:#e7e5e4;padding:1rem;border-radius:var(--radius-sm);overflow-x:auto;margin:1em 0}
.article-body pre code{background:none;padding:0;color:inherit}
.article-body img{max-width:100%;border-radius:var(--radius-sm);margin:1em 0}
.article-body ul,.article-body ol{padding-left:1.4em;margin-bottom:1em}
.article-body li{margin-bottom:.25em}
.article-body hr{border:none;border-top:1px solid var(--border);margin:2em 0}
.article-body a{color:var(--primary);text-decoration:underline;text-underline-offset:2px}
.article-footer{margin-top:2rem;padding-top:1.2rem;border-top:1px solid #f5f5f4;text-align:center;color:var(--text2);font-size:.88rem}
.article-footer a{display:inline-block;margin-top:.4rem;padding:.4rem 1rem;background:var(--primary);color:#fff;border-radius:99px;font-size:.82rem;font-weight:600}
.article-footer a:hover{background:var(--primary-h);color:#fff}

.subscribe-page{background:var(--card);border-radius:var(--radius);padding:2.5rem 2rem;border:1px solid var(--border);text-align:center}
.subscribe-page .icon{font-size:2.5rem;margin-bottom:.6rem}
.subscribe-page h1{font-size:1.4rem;font-weight:800;margin-bottom:.4rem}
.subscribe-page .desc{color:var(--text2);line-height:1.6;margin-bottom:1.5rem}
.sub-features{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:1rem;text-align:left;margin-top:1.5rem}
.sub-feat{display:flex;gap:.6rem;padding:.8rem;background:var(--bg);border-radius:var(--radius-sm)}
.sub-feat span:first-child{font-size:1.3rem;flex-shrink:0}
.sub-feat h4{font-size:.85rem;font-weight:700;margin-bottom:.1rem}
.sub-feat p{font-size:.78rem;color:var(--text2)}

.footer{border-top:1px solid #f5f5f4;padding:2rem 1.5rem;text-align:center}
.footer p:first-child{font-weight:700;font-size:.9rem;margin-bottom:.25rem}
.footer p:last-child{color:var(--muted);font-size:.82rem}

#wechat-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.7);z-index:9999;display:flex;align-items:flex-start;justify-content:flex-end;padding:1rem}
.wc-guide{color:#fff;text-align:right;padding:1rem;animation:fadeIn .5s ease}
.wc-guide .arrow{font-size:2.5rem;margin-bottom:.4rem;animation:bounce 1s infinite}
.wc-guide p{font-size:.9rem;line-height:1.7;background:rgba(255,255,255,.15);padding:.6rem .8rem;border-radius:var(--radius-sm)}
@keyframes fadeIn{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:translateY(0)}}
@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}

@media(max-width:600px){
  .hero{padding:2.5rem 1rem 1.5rem}
  .article{padding:1.2rem}
  .subscribe-page{padding:1.5rem 1rem}
}
"""

NAV = f"""<nav class="nav"><div class="nav-inner"><a href="index.html" class="nav-brand"><span>✦</span><span>{SITE_NAME}</span></a><div class="nav-links"><a href="index.html" class="nav-link">首页</a><a href="subscribe.html" class="nav-link">订阅</a></div></div></nav>"""

FOOTER = """<footer class="footer"><p>✦ 私人博客 · 用文字记录生活</p><p>订阅即可收到新文章推送 <a href="subscribe.html">去订阅 →</a></p></footer>"""

WECHAT_SCRIPT = """
<script>
(function(){var ua=navigator.userAgent.toLowerCase();if(ua.indexOf('micromessenger')!==-1||ua.indexOf('qq/')!==-1){if(!sessionStorage.getItem('bg')){var o=document.createElement('div');o.id='wechat-overlay';o.innerHTML='<div class="wc-guide"><div class="arrow">↗</div><p>点击右上角 <strong>···</strong> 选择「在浏览器中打开」</p></div>';document.body.appendChild(o);sessionStorage.setItem('bg','1');o.addEventListener('click',function(){o.remove()});setTimeout(function(){if(document.getElementById('wechat-overlay'))o.remove()},5000)}}})();
</script>
"""


def build_index(articles):
    """生成首页"""
    cards = ""
    for a in articles:
        pin = '<span class="card-pin">📌 置顶</span>' if a['pinned'] else ''
        summary = a['summary'] or a['content'][:120].replace('#','').replace('*','')
        if not a['summary']:
            summary += '...'
        cards += f"""<a href="article/{a['slug']}.html" class="card">
            {pin}
            <h2>{a['title']}</h2>
            <p>{summary}</p>
            <div class="card-meta"><span>{a['date']}</span><span>阅读 {a['reading_time']}分钟</span></div>
        </a>\n"""

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>{SITE_NAME}</title><meta name="description" content="{SITE_DESC}"><link rel="alternate" type="application/rss+xml" title="RSS" href="rss.xml"><style>{STYLE}</style></head>
<body>{NAV}<div class="hero"><h1>欢迎来到我的文字世界</h1><p>这里是思考的栖息地，记录生活的温度与深度</p><a href="subscribe.html">订阅推送 →</a></div><div class="container">{cards}</div>{FOOTER}{WECHAT_SCRIPT}</body></html>"""


def build_article(article):
    """生成文章页"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>{article['title']} - {SITE_NAME}</title><meta name="description" content="{article['summary']}"><style>{STYLE}</style></head>
<body>{NAV}<div class="container container-narrow"><article class="article"><a href="../index.html" class="back">← 返回首页</a><h1>{article['title']}</h1><div class="article-meta"><span>{article['date']}</span><span>·</span><span>阅读 {article['reading_time']}分钟</span></div><div class="article-body">{article['html']}</div><div class="article-footer"><p>觉得不错？分享给朋友吧～</p><a href="../subscribe.html">订阅推送 →</a></div></article></div>{FOOTER}{WECHAT_SCRIPT}</body></html>"""


def build_subscribe():
    """生成订阅页"""
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>订阅推送 - {SITE_NAME}</title><style>{STYLE}</style></head>
<body>{NAV}<div class="container container-narrow"><div class="subscribe-page"><div class="icon">📬</div><h1>订阅我的博客</h1><p class="desc">RSS 订阅地址放在下面，复制到任何 RSS 阅读器中即可<br>新文章发布后自动收到通知</p><div style="background:var(--bg);padding:.8rem 1rem;border-radius:var(--radius-sm);margin:1rem 0;font-family:var(--mono);font-size:.85rem;word-break:break-all"><a href="rss.xml">RSS 订阅链接</a></div><div class="sub-features"><div class="sub-feat"><span>📡</span><div><h4>RSS 推送</h4><p>RSS 阅读器自动接收</p></div></div><div class="sub-feat"><span>🔒</span><div><h4>随时退订</h4><p>不想收了随时取消</p></div></div><div class="sub-feat"><span>📱</span><div><h4>全平台</h4><p>手机电脑都能看</p></div></div></div></div></div>{FOOTER}{WECHAT_SCRIPT}</body></html>"""


def build_rss(articles):
    """生成 RSS"""
    base = SITE_URL or "."
    items = ""
    for a in articles:
        summary = a['summary'] or a['content'][:200].replace('#','').replace('*','')
        items += f"""<item><title>{a['title']}</title><link>{base}/article/{a['slug']}.html</link><description>{summary}</description></item>\n"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{SITE_NAME}</title><link>{base}</link><description>{SITE_DESC}</description><language>zh-CN</language>{items}</channel></rss>"""


def build_404():
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><title>页面不存在 - {SITE_NAME}</title><style>{STYLE}</style></head>
<body>{NAV}<div class="container" style="text-align:center;padding:6rem 1.5rem"><div style="font-size:3rem;margin-bottom:.75rem">🔍</div><h1 style="margin-bottom:.5rem">页面不存在</h1><p style="color:var(--text2)"><a href="index.html">返回首页</a></p></div>{FOOTER}</body></html>"""


# ========== 构建 ==========
def build():
    print("📦 开始构建静态博客...")
    articles = load_articles()
    print(f"   找到 {len(articles)} 篇文章")

    # 清空输出目录
    out = Path(OUTPUT_DIR)
    if out.exists():
        import shutil
        shutil.rmtree(out)
    out.mkdir()
    (out / "article").mkdir()

    # 生成首页
    (out / "index.html").write_text(build_index(articles), encoding='utf-8')
    print("   ✅ index.html")

    # 生成文章页
    for a in articles:
        (out / "article" / f"{a['slug']}.html").write_text(build_article(a), encoding='utf-8')
        print(f"   ✅ article/{a['slug']}.html")

    # 生成订阅页
    (out / "subscribe.html").write_text(build_subscribe(), encoding='utf-8')
    print("   ✅ subscribe.html")

    # 生成RSS
    (out / "rss.xml").write_text(build_rss(articles), encoding='utf-8')
    print("   ✅ rss.xml")

    # 生成404页
    (out / "404.html").write_text(build_404(), encoding='utf-8')
    print("   ✅ 404.html")

    print(f"\n🎉 构建完成！共 {len(articles)} 篇文章，输出到 {OUTPUT_DIR}/")


if __name__ == '__main__':
    build()
