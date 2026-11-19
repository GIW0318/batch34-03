# GSB Bugfix Task
## 题面
第三人称镜头贴墙时被肩膀挡住，镜头臂还穿进柱子；只打一条中心射线时近裁剪面仍会切进墙面；镜头被挤进角色身体，松开又弹回最大距离；放两根柱子时总命中先加入的那根而不是最近的。camera_occlusion.py 的 CameraBoom(target, max_distance, probe_radius, min_distance) 需要实现 add_obstacle 和 solve：障碍物用球体表示，add_obstacle(center, radius) 返回加入后的索引；solve(direction) 归一化方向后，从目标点沿垂直方向偏移 probe_radius 发五条平行射线，分别对每个球求最近的正向交点；所有射线里最小的命中距离就是镜头臂长度，再夹到 [min_distance, max_distance]；目标点落在球内视为距离 0，仍然算命中；返回字典含 distance、hit、point，没有遮挡时 hit 为 None、distance 等于最大距离；零向量或错误维数、最大距离非正、最小距离不小于最大、探测半径或球半径非正一律按 ValueError 拒绝。

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
