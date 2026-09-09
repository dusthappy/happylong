schema: 1
project: $project
title: $title
description: $description
created: $created
updated: $created

# 技术栈（人工维护；doctor 会按仓库清单给出探测差异提醒）
stack:
  langs: []
  frameworks: []

# 代码仓库登记（由 happlylong.py link add 维护）
# 字段: role(frontend|backend|fullstack|lib) / target(绝对路径) / langs /
#       shared(跨项目共享仓) / backend_apps(共享后端子项目) / pending(目标未就绪)
# 活跃迭代不写入项目档案；每个代理会话独立记录在 .hy/session/bindings/。
repos: {}
