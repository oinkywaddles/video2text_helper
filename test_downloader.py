"""
下载器模块测试脚本

用于验证视频下载功能是否正常工作
"""

from downloader import download_audio
import os


def test_download():
    """
    测试下载功能
    你可以修改下面的测试链接来测试不同的视频
    """
    print("=" * 60)
    print("视频下载器测试")
    print("=" * 60)

    # 测试用例 - 请根据需要修改
    # 示例 1: Bilibili 短视频 (通常不需要代理)
    test_urls = [
        {
            "name": "Bilibili 测试",
            "url": "https://www.bilibili.com/video/BV1xx411c7mu",  # 这是一个示例，请替换为实际链接
            "proxy": None
        },
        # 示例 2: YouTube 视频 (需要代理)
        # {
        #     "name": "YouTube 测试",
        #     "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        #     "proxy": "http://127.0.0.1:7890"  # 根据你的代理端口修改
        # }
    ]

    results = []

    for i, test in enumerate(test_urls, 1):
        print(f"\n【测试 {i}/{len(test_urls)}】{test['name']}")
        print("-" * 60)

        result = download_audio(
            url=test["url"],
            proxy=test["proxy"]
        )

        results.append({
            "name": test["name"],
            "success": result is not None,
            "file": result
        })

        print()

    # 输出测试结果
    print("=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    for i, result in enumerate(results, 1):
        status = "✅ 成功" if result["success"] else "❌ 失败"
        print(f"{i}. {result['name']}: {status}")
        if result["file"]:
            file_size = os.path.getsize(result["file"]) / 1024 / 1024  # MB
            print(f"   文件: {result['file']}")
            print(f"   大小: {file_size:.2f} MB")

    # 统计
    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    print(f"\n通过率: {success_count}/{total_count}")

    return success_count == total_count


if __name__ == "__main__":
    print("\n提示: 请在运行测试前修改 test_urls 中的视频链接\n")

    success = test_download()

    if success:
        print("\n🎉 所有测试通过！")
        exit(0)
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        exit(1)
