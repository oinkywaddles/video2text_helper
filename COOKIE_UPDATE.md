# Cookie 参数更新说明

## 更新时间
2025-12-01

## 更改内容

### 1. 函数参数调整
**修改前**：
```python
def download_audio(url, output_dir="downloads", proxy=None, use_cookies=False)
```

**修改后**：
```python
def download_audio(url, output_dir="downloads", proxy=None, use_cookies=True)
```

**变化**：`use_cookies` 默认值从 `False` 改为 `True`

### 2. 命令行参数调整
**修改前**：
```bash
--use-cookies    # 启用 cookies
```

**修改后**：
```bash
--no-cookies     # 禁用 cookies（默认启用）
```

**变化**：采用反向逻辑，默认启用 cookies，提供选项来禁用

### 3. 使用方式

#### 默认行为（使用 cookies）
```bash
python downloader.py "https://www.bilibili.com/video/BV1xxxxxx"
```
- ✅ 自动从 Chrome 浏览器导入 cookies
- ✅ 可以绕过 Bilibili 反爬虫限制
- ✅ 提示信息：`🍪 已启用 Cookie 导入 (从 Chrome 浏览器)`

#### 禁用 cookies
```bash
python downloader.py "https://www.bilibili.com/video/BV1xxxxxx" --no-cookies
```
- ⚠️ 不导入 cookies
- ⚠️ 可能遇到 HTTP 412 错误（反爬虫限制）

#### 查看帮助
```bash
python downloader.py --help
```

### 4. 测试结果

#### 测试 1：默认行为（使用 cookies）
```
命令：python downloader.py "https://www.bilibili.com/video/BV1Z6SEBrE1H"
结果：✅ 成功
提示：🍪 已启用 Cookie 导入 (从 Chrome 浏览器)
      Extracted 1270 cookies from chrome
文件：76 MB MP3, 192 kbps, 44.1 kHz, Stereo
速度：~15 MB/s
```

#### 测试 2：禁用 cookies
```
命令：python downloader.py "https://www.bilibili.com/video/BV1Z6SEBrE1H" --no-cookies
结果：❌ 失败
错误：HTTP Error 412: Precondition Failed
说明：Bilibili 反爬虫限制，需要 cookies
```

### 5. 技术细节

#### Cookie 获取机制
- **来源**：Chrome 浏览器本地存储
- **方法**：yt-dlp 的 `cookiesfrombrowser` 功能
- **数量**：自动提取约 1270 个 cookies
- **隐私**：完全本地操作，不上传第三方

#### 为什么默认启用？
1. **必要性**：Bilibili 等网站有严格的反爬虫机制
2. **成功率**：启用 cookies 可确保下载成功
3. **安全性**：仅读取本地浏览器数据，不涉及网络传输
4. **用户体验**：避免用户遇到下载失败问题

### 6. 完整命令示例

```bash
# 基本用法（默认使用 cookies）
python downloader.py "https://www.bilibili.com/video/BV1Z6SEBrE1H"

# 使用代理（YouTube）
python downloader.py "https://www.youtube.com/watch?v=xxxxxx" --proxy "http://127.0.0.1:7890"

# 禁用 cookies
python downloader.py "https://www.bilibili.com/video/BV1xxxxxx" --no-cookies

# 自定义输出目录
python downloader.py "https://www.bilibili.com/video/BV1xxxxxx" --output-dir "my_downloads"

# 组合使用
python downloader.py "https://www.youtube.com/watch?v=xxxxxx" \
  --proxy "http://127.0.0.1:7890" \
  --output-dir "youtube_downloads" \
  --no-cookies
```

### 7. API 调用方式

#### Python 代码中使用

```python
from downloader import download_audio

# 使用 cookies（默认）
result = download_audio("https://www.bilibili.com/video/BV1xxxxxx")

# 不使用 cookies
result = download_audio(
    "https://www.bilibili.com/video/BV1xxxxxx",
    use_cookies=False
)

# 完整参数
result = download_audio(
    url="https://www.youtube.com/watch?v=xxxxxx",
    output_dir="my_downloads",
    proxy="http://127.0.0.1:7890",
    use_cookies=True
)

if result:
    print(f"下载成功: {result}")
else:
    print("下载失败")
```

### 8. 常见问题

#### Q1: 为什么要默认启用 cookies？
A: Bilibili 等网站会阻止无 cookies 的请求，启用后可确保下载成功。

#### Q2: cookies 安全吗？
A: 完全安全。cookies 仅从本地浏览器读取，不会上传或分享给任何人。

#### Q3: 我没有 Chrome 怎么办？
A: 可以修改代码中的 `('chrome',)` 为 `('firefox',)` 或 `('safari',)` 等。

#### Q4: 如何禁用 cookies？
A: 使用 `--no-cookies` 参数，但可能导致部分网站下载失败。

#### Q5: cookies 会被保存吗？
A: 不会。yt-dlp 仅在下载过程中临时使用，不会保存到磁盘。

### 9. 更新总结

✅ **优点**：
- 提高下载成功率
- 更好的用户体验
- 明确的提示信息
- 灵活的控制选项

⚠️ **注意事项**：
- 需要安装 Chrome 浏览器
- 首次运行会提取 cookies（可能稍慢）
- 如果不需要可以随时使用 `--no-cookies` 禁用

## 下一步

阶段一视频下载模块已完成并经过验证 ✅

可以进入阶段二：语音转写模块开发
