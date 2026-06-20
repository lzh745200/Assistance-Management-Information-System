# build-scripts — Windows NSIS 安装包脚本

> P2-5 整改说明：历史遗留 9 个 NSI 脚本（`build-scripts/` 7 个 + `installers/` 2 个），
> 内容高度重复。本轮整改先标注主入口与废弃项，后续将抽取 `common.nsh` 公共 include
> 进一步去重（L 工作量，单独 PR）。

## 主入口（推荐使用）

| 脚本 | 用途 | 状态 |
|------|------|------|
| `installer-combined.nsi` | **一体化安装包**（前端 + 后端 + 运行时），主入口 | ✅ 主入口 |
| `installer.nsi` | 标准安装包（中文 PRODUCT_NAME） | ✅ 备用主入口 |

## 按架构

| 脚本 | 架构 | 状态 |
|------|------|------|
| `installer_x64.nsi` | 64 位 | ✅ 维护 |
| `installer_x86.nsi` | 32 位 | ✅ 维护 |
| `installers/installer_x64.nsi` | 64 位（installers/ 目录副本） | ⚠️ 与 build-scripts/ 重复，待合并 |
| `installers/installer_x86.nsi` | 32 位（自带完整运行时） | ⚠️ 与 build-scripts/ 重复，待合并 |

## 已废弃（DEPRECATED，请勿使用，待删除）

| 脚本 | 废弃原因 |
|------|----------|
| `installer-fixed.nsi` | 临时修复脚本，已被 `installer.nsi` 合并覆盖 |
| `installer-simple.nsi` | 精简版，功能不全，已被 combined 取代 |
| `installer-x86.nsi` | 命名不一致（连字符 vs 下划线），与 `installer_x86.nsi` 重复 |

## 后续去重计划

1. 抽取 `common.nsh`：PRODUCT_NAME/VERSION、卸载逻辑、组件分段等公共宏
2. 各 NSI `!include "common.nsh"`，仅保留差异部分
3. 删除上表"已废弃"脚本，合并 installers/ 与 build-scripts/ 重复项
4. 单一主入口：`installer-combined.nsi`（x64/x86 通过 `!ifdef` 切换）
