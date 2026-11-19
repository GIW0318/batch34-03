# GSB Bugfix Task
## 题面
山坡像刀切一样直，水滴侵蚀跑完把整张高度图削平，山顶没变化、山脚反而堆出一圈土；同种子结果不同，高度出现负数，蒸发参数填 1 之后水还没流动就没了。terrain_erosion.py 的 HydraulicErosion(heightmap, erosion_rate, settle_rate, carry_factor, evaporation) 提供 erode、heights 和 sediment_total：高度图按二维数组传入，必须非空、矩形、元素为有限非负数；erode 支持 droplets、max_steps、seed 和可选起点，逐滴水模拟，每步选四邻域中最低的一格，按落差和水量的乘积算携沙容量，泥沙少于容量就按侵蚀率从当前格刷走，超过容量就按沉积率堆下，水分按蒸发率递减；走到局部最低点或步数用完时把剩余泥沙全部沉在脚下，离场也不能把泥沙带出地图，保证总高度不变；heights 返回深拷贝，sediment_total 返回累计搬运量。行列不齐、高度非法、速率越界、蒸发不小于 1、水滴数为负、max_steps 为零、起点越界时，全部以 ValueError 拒绝。

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
