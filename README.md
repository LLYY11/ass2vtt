

# ass2vtt

高效、简洁的 `.ass` → `.vtt` 字幕格式批量转换工具

## 简介

**ass2vtt** 专为将 Advanced SubStation Alpha（`.ass`）字幕文件转换为 Web 兼容的 WebVTT（`.vtt`）格式而设计。适用于视频网站上传、网页字幕嵌入等场景。

### 核心特性

- ✅ **中英文界面自由切换**：支持 `--lang zh` 或 `--lang en`，适配不同用户习惯  
- 🚀 **批量转换**：可一次性处理整个目录下的所有 `.ass` 文件  
- 🔧 **自定义输出后缀名**：通过 `--suffix` 参数指定输出文件扩展名（默认为 `.vtt`）  
- 📁 **智能输出路径**：转换后的文件与原始 `.ass` 文件位于**同一目录**，便于管理  


## 如何使用

### 一、获取工具

1. Star 本仓库（如果觉得有用 ❤️）
2. 克隆或下载：
  `git clone https://github.com/LLYY11/ass2vtt.git`
  `cd ass2vtt`
