# GSB Bugfix Task
## 题面
战棋单位寻路卡死：同一张图两次点击路径不同；开放场地上 A* 把整张图展开才找到目标；目标被墙围死时接口不返回，预算用完也不给标记。astar_budget.py 需要提供 astar(grid, start, goal, max_expansions, tie_break)：grid 是等长字符串列表，'#' 表示不可通行，其余字符可走；只允许上下左右移动，代价为 1，用曼哈顿启发；start 与 goal 是 (行, 列) 元组，必须落在图内且不能是墙；max_expansions 是正整数，表示最多弹出多少个节点；tie_break 取 "h" 时 f 相同优先展开 h 更小的节点，取 "fifo" 时按入队先后；返回字典含 path、cost、expanded、complete。找到目标时 path 含起点终点且不重复，预算耗尽时 path 为 None 且 complete 为 False，确认不可达时 path 为 None 但 complete 为 True；起点终点相同只返回单点路径；非法图、越界坐标、零预算或未知 tie_break 按 ValueError 报错。

## 运行方式
```bash
python -m pytest tests -q
```

## 平台字段

所属领域：安全
子方向：游戏开发
任务类型：Bugfix
语言 / 框架：Python 3, pytest
环境可复现等级：有外部依赖，未容器化
