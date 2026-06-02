# 图标资源说明

本目录存放应用程序图标，用于 Electron 打包和系统集成。

## 必需文件

| 文件名 | 用途 | 规格要求 |
|--------|------|---------|
| `app.ico` | Windows 应用图标 | 256x256, ICO 格式（含 16/32/48/128/256 多尺寸） |
| `app.png` | Linux 应用图标 | 512x512, PNG 格式 |
| `app.icns` | macOS 应用图标（可选） | ICNS 格式 |

## 快速生成

可使用 [electron-icon-builder](https://www.npmjs.com/package/electron-icon-builder) 从一张 1024x1024 PNG 自动生成全部格式:

```bash
npx electron-icon-builder --input=icon-source.png --output=./resources/icons/
```

## 注意事项

- ICO 文件必须包含多个尺寸层（16x16、32x32、48x48、128x128、256x256）
- PNG 建议使用透明背景
- 图标设计应在小尺寸（16x16）下仍清晰可辨
