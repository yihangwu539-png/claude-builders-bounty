# Block Destructive Bash Commands — Claude Code Pre-Tool-Use Hook

拦截并阻止Claude Code执行危险bash命令，在命令真正执行前捕获。

## 安装（2步）

```bash
# 1. 创建hooks目录
mkdir -p ~/.claude/hooks

# 2. 复制脚本
cp block_destructive.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/block_destructive.py
```

安装完成！Claude Code会自动检测hook并生效。

## 拦截规则

### 🛑 危险系统命令（永远阻止）
| 模式 | 示例 |
|------|------|
| 递归根目录删除 | `rm -rf /`, `rm -rf /home` |
| 格式化磁盘 | `mkfs.ext4 /dev/sda` |
| 磁盘覆写 | `dd if=/dev/zero of=/dev/sda` |
| Fork炸弹 | `:(){ :|:& };:` |

### 🛑 危险数据库命令
| 模式 | 示例 |
|------|------|
| 删库 | `DROP DATABASE production` |
| 删表 | `DROP TABLE users` |
| 无WHERE删除 | `DELETE FROM users`（不允许） |
| 截断 | `TRUNCATE orders` |

### 🛑 危险Git命令
| 模式 | 示例 |
|------|------|
| 强制推送 | `git push --force` |
| 重置历史 | `git reset --hard HEAD~5` |
| 清理 | `git clean -fd` |

### 🛑 危险文件系统命令
| 模式 | 示例 |
|------|------|
| 拒绝访问 | `chmod -R 0 /` |
| 磁盘直写 | `> /dev/sda` |
| 关机重启 | `shutdown -h now`, `reboot` |

## 日志

所有拦截的命令记录在 `~/.claude/hooks/blocked.log`：

```json
{"timestamp":"2026-04-27T02:00:00Z","category":"git","command":"git push --force","project_path":"/home/user/project"}
```

## 不干扰正常命令

以下常见命令 **不会被拦截**：
- `npm install`, `pip install`
- `git push`, `git pull`, `git commit`
- `rm file.txt`, `rm -rf node_modules`
- `mkdir`, `cp`, `mv`
- `docker`, `kubectl`, `ssh`
- `curl`, `wget`

## 卸载

```bash
rm ~/.claude/hooks/block_destructive.py
```
