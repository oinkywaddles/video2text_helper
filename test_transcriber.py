"""
转写模块测试脚本

用于测试音频转文字功能
"""

from transcriber import transcribe_audio
import os
import glob


def test_transcribe():
    """
    测试转录功能
    自动查找 downloads 目录下的音频文件
    """
    print("=" * 60)
    print("音频转写测试")
    print("=" * 60)

    # 查找 downloads 目录下的音频文件
    audio_files = glob.glob("downloads/*.mp3")

    if not audio_files:
        print("❌ 错误: downloads 目录下没有找到 MP3 文件")
        print("请先运行 downloader.py 下载视频")
        return False

    print(f"\n找到 {len(audio_files)} 个音频文件:")
    for i, file in enumerate(audio_files, 1):
        size = os.path.getsize(file) / 1024 / 1024
        print(f"{i}. {os.path.basename(file)} ({size:.2f} MB)")

    # 测试用例配置
    test_cases = []

    # 检查是否有中文视频
    chinese_files = [f for f in audio_files if "洪灏" in f or "李蓓" in f]
    if chinese_files:
        test_cases.append({
            "name": "中文转写测试",
            "file": chinese_files[0],
            "model": "medium",
            "language": None  # 自动检测
        })

    # 检查是否有英文视频
    english_files = [f for f in audio_files if "OpenAI" in f or "Anthropic" in f or "Closed-Door" in f]
    if english_files:
        test_cases.append({
            "name": "英文转写测试",
            "file": english_files[0],
            "model": "medium",
            "language": None  # 自动检测
        })

    # 如果没有特定文件，就用第一个
    if not test_cases and audio_files:
        test_cases.append({
            "name": "通用转写测试",
            "file": audio_files[0],
            "model": "medium",
            "language": None
        })

    results = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"【测试 {i}/{len(test_cases)}】{test['name']}")
        print(f"{'=' * 60}")

        result = transcribe_audio(
            audio_path=test["file"],
            model_size=test["model"],
            language=test["language"]
        )

        success = result is not None

        results.append({
            "name": test["name"],
            "file": os.path.basename(test["file"]),
            "success": success,
            "output": result
        })

        if success:
            # 保存转录结果
            base_name = os.path.splitext(os.path.basename(test["file"]))[0]
            output_file = f"{base_name}_transcript.txt"

            try:
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(result)
                print(f"\n💾 转录结果已保存: {output_file}")

                # 显示前几行内容
                lines = result.split("\n")[:5]
                print(f"\n📄 内容预览（前5行）:")
                for line in lines:
                    print(f"   {line}")
                if len(result.split("\n")) > 5:
                    print(f"   ... (共 {len(result.split('\n'))} 行)")

            except Exception as e:
                print(f"❌ 保存失败: {e}")

        print()

    # 输出测试结果汇总
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for i, result in enumerate(results, 1):
        status = "✅ 成功" if result["success"] else "❌ 失败"
        print(f"{i}. {result['name']}: {status}")
        print(f"   文件: {result['file']}")
        if result["success"]:
            word_count = len(result["output"])
            line_count = len(result["output"].split("\n"))
            print(f"   输出: {line_count} 行, {word_count} 字符")

    # 统计
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    print(f"\n通过率: {success_count}/{total_count}")

    return success_count == total_count


if __name__ == "__main__":
    print("\n⚠️  注意:")
    print("1. 首次运行会下载 medium 模型（约 1.5 GB）")
    print("2. 下载时间取决于网络速度（可能需要 5-30 分钟）")
    print("3. 转录速度约为 1-5x 实时速度")
    print("4. MacBook Air M4 性能优秀，转录速度会比较快\n")

    input("按 Enter 键开始测试...")

    success = test_transcribe()

    if success:
        print("\n🎉 所有测试通过！")
        exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        exit(1)
