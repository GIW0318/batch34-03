# GSB Bugfix Task
## 题面
角色在斜坡上跑动时披风被拉成一条细线，帧率一低整块布直接炸开；挂在肩上的两个固定点会慢慢漂走，横竖两条约束轮流修正后拉伸量越积越大，换一台机器因为帧间隔不同结果又完全不同，网格改成 2 列时还会除零。cloth_solver.py 的 ClothSolver(cols, rows, spacing, gravity, damping, rounds) 需要实现 pin、advance、positions 和 max_stretch：初始化按行列生成等距网格，纵坐标向下为负；每次调用用 Verlet 积分，速度取上一帧位移乘阻尼，再叠加向下的重力加速度；pin 指定的格子永远不动；每轮约束迭代对所有相邻横竖边按距离误差修正，两端都在动的各让一半，只有一端固定的由活动端全额吸收；约束轮数和阻尼可配置；positions 按行优先返回可安全修改的二维列表副本；max_stretch 返回当前最大相对形变。列数或行数小于 2、间距非正、阻尼不在 (0,1]、rounds 小于 1、dt 非正或固定点越界时，直接抛 ValueError。

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
