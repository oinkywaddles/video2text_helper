# 阶段二准备工作：语音转写模块

## 目标
实现语音转写功能，将下载的音频文件转换为带时间戳的文本。

## 核心依赖

### 1. faster-whisper
- **作用**: 语音识别引擎（Whisper 的优化版本）
- **优势**: 比原版 Whisper 快 4-5 倍，内存占用更少
- **安装命令**: `uv pip install faster-whisper`

### 2. torch (PyTorch)
- **作用**: 深度学习框架，faster-whisper 的依赖
- **版本**: 2.0.0+
- **安装命令**: `uv pip install torch`

### 3. 其他依赖
- **ctranslate2**: faster-whisper 的后端引擎（自动安装）
- **tokenizers**: 文本分词器（自动安装）
- **onnxruntime**: 推理引擎（自动安装）

## 系统要求

### 磁盘空间
- **模型文件大小**:
  - `tiny`: ~75 MB
  - `base`: ~150 MB
  - `small`: ~500 MB
  - `medium`: ~1.5 GB （推荐）
  - `large-v3`: ~3 GB
- **建议预留**: 至少 5 GB 空闲空间

### 内存要求
- **CPU 运行**:
  - tiny/base: 2 GB RAM
  - small: 4 GB RAM
  - medium: 8 GB RAM
  - large-v3: 16 GB RAM
- **GPU 运行**: 显存需求减半

### macOS 特别说明
- ✅ **Mac M1/M2/M3**: CPU 性能足够强大，无需 GPU
- ✅ **推荐模型**: medium（性能和精度平衡）
- ✅ **预期速度**: 比 GPU 慢，但完全可用

## 准备步骤

### 步骤 1: 检查磁盘空间
```bash
df -h .
```
确保至少有 5 GB 空闲空间。

### 步骤 2: 安装依赖
```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装依赖（可能需要 10-20 分钟）
uv pip install faster-whisper torch
```

### 步骤 3: 验证安装
```bash
python -c "from faster_whisper import WhisperModel; print('✅ faster-whisper 安装成功')"
python -c "import torch; print(f'✅ torch 版本: {torch.__version__}')"
```

### 步骤 4: 模型下载说明
- **首次运行会自动下载模型**
- **下载位置**: `~/.cache/huggingface/hub/`
- **下载时间**: 取决于网络速度
  - medium 模型: ~1.5 GB，可能需要 5-30 分钟
- **可以提前下载**: 运行测试脚本会自动触发下载

## 预期问题及解决方案

### 问题 1: torch 安装缓慢
**原因**: torch 包很大（~70 MB compressed）

**解决方案**:
```bash
# 使用国内镜像（如果在中国）
uv pip install torch -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 2: 模型下载失败
**原因**: Hugging Face 被墙或网络不稳定

**解决方案**:
1. 使用代理
2. 使用国内镜像
3. 手动下载模型文件

### 问题 3: 内存不足
**原因**: 模型太大

**解决方案**:
- 使用更小的模型（small 或 base）
- 关闭其他占用内存的应用

### 问题 4: Mac M1/M2/M3 兼容性
**状态**: ✅ 完全兼容

**说明**:
- faster-whisper 支持 Apple Silicon
- 使用 CPU 模式，性能良好
- 不需要额外配置

## 功能规划

### 核心功能
1. ✅ 加载音频文件
2. ✅ 自动语言检测
3. ✅ 语音转文字
4. ✅ 生成时间戳
5. ✅ 保存为文本文件

### 可选功能
- [ ] 多语言支持
- [ ] 字幕格式导出 (SRT, VTT)
- [ ] 说话人识别
- [ ] 自定义模型选择
- [ ] 进度条显示

## 实现计划

### 文件结构
```
video2text_helper/
├── transcriber.py      # 转写模块（待实现）
├── main.py            # 主程序（待实现）
├── downloader.py      # 下载模块 ✅
└── downloads/         # 音频文件
    ├── 20251128洪灏展望2026.mp3
    └── Inside the Closed-Door Deals.mp3
```

### transcriber.py 功能
```python
def transcribe_audio(
    audio_path,           # 音频文件路径
    model_size="medium",  # 模型大小
    device="auto",        # 设备选择（auto/cpu/cuda）
    language=None         # 语言（None=自动检测）
):
    """
    转录音频文件
    返回: 带时间戳的文本字符串
    """
    # 1. 加载模型
    # 2. 转录音频
    # 3. 生成时间戳文本
    # 4. 返回结果
```

### main.py 功能
```python
# 整合下载和转写
# 1. 下载视频音频（使用 downloader.py）
# 2. 转写音频（使用 transcriber.py）
# 3. 保存结果
```

## 测试计划

### 测试文件
使用阶段一已下载的音频：
1. `20251128洪灏展望2026.mp3` (76 MB, 中文)
2. `Inside the Closed-Door Deals.mp3` (30 MB, 英文)

### 测试用例
1. **中文转写**: 测试中文语音识别准确度
2. **英文转写**: 测试英文语音识别准确度
3. **自动语言检测**: 测试语言识别功能
4. **时间戳准确性**: 验证时间戳是否正确
5. **长音频处理**: 测试 76 MB 大文件处理能力

### 性能基准
- **转写速度**: 预期 1-5x 实时速度（Mac M1/M2/M3）
  - 实时速度 = 转写时间 / 音频时长
  - 例如：10 分钟音频，转写需要 2-10 分钟
- **准确率**: 预期 85-95%（取决于音频质量）

## 时间估算

### 依赖安装: 10-30 分钟
- torch 下载: 5-10 分钟
- faster-whisper 安装: 2-5 分钟
- 其他依赖: 3-5 分钟
- 首次模型下载: 5-30 分钟（取决于网络）

### 代码实现: 1-2 小时
- transcriber.py: 30-60 分钟
- 测试脚本: 15-30 分钟
- 调试优化: 15-30 分钟

### 测试验证: 30-60 分钟
- 安装验证: 5 分钟
- 功能测试: 20-40 分钟（包含转写时间）
- 文档整理: 10-15 分钟

### 总计: 约 2-4 小时

## 检查清单

### 开始前检查
- [ ] 磁盘空间充足（>5 GB）
- [ ] 内存充足（>8 GB 推荐）
- [ ] 网络连接稳定
- [ ] 虚拟环境已激活
- [ ] 阶段一测试文件准备好

### 安装后检查
- [ ] faster-whisper 导入成功
- [ ] torch 导入成功
- [ ] 无错误或警告信息
- [ ] 可以创建 WhisperModel 实例

### 实现后检查
- [ ] transcriber.py 文件创建
- [ ] 基本功能实现
- [ ] 测试脚本创建
- [ ] 功能测试通过

## 风险评估

### 高风险
- ❌ **模型下载失败**: Hugging Face 可能被墙
  - 缓解: 提供代理或镜像方案

### 中风险
- ⚠️ **内存不足**: large 模型可能超出可用内存
  - 缓解: 使用 medium 模型

### 低风险
- ✅ **Mac 兼容性**: Apple Silicon 完全支持
- ✅ **依赖冲突**: uv 管理依赖较好

## 参考资料

### 官方文档
- [faster-whisper GitHub](https://github.com/SYSTRAN/faster-whisper)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [PyTorch](https://pytorch.org/)

### 模型说明
- Whisper 支持 99 种语言
- 自动检测语言和标点符号
- 生成时间戳精确到 0.01 秒

## 下一步

完成准备工作后，我们将：
1. 安装依赖包
2. 实现 transcriber.py
3. 创建测试脚本
4. 测试中英文转写
5. 优化性能和准确度

准备好了吗？ 🚀
