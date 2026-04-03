# MTR Simulation 项目进度报告 (Project Progress Report)

**更新日期**: 2026年4月3日

## 🌟 整体进度概览
目前项目正处于 **阶段二（数据预处理）** 阶段，**Sprint 1** 的目标已基本完成。我们已经成功建立了数据获取机制，构建了线网拓扑，并提取了 POI 空间特征。

---

## 📊 详细任务完成情况

### 阶段一：数据准备 (Data Acquisition) - ✅ 基本完成
- [x] **T1.1 静态数据集成**: 已成功整合 MTR 静态数据，并生成 `data/processed/stations_master.csv`。
- [ ] **T1.2 实时 API 适配器**: 已打通 Next Train API，但 `data/realtime/` 下目前只有初步的测试性快照数据，暂未形成完整时序数据，需进一步完善定时抓取。
- [x] **T1.3 POI 环境采集**: 已处理抓取的地政总署数据，生成 `data/processed/station_poi_weights.json`。

### 阶段二：数据预处理 (Data Preprocessing) - 🚧 进行中
- [x] **T2.1 图拓扑构建**: 已使用 NetworkX 建立线网模型，生成了 `data/processed/mtr_topology.gml` 和可视化文件 `mtr_topology_viz.html`。
- [x] **T2.3 权重归一化与特征工程**: 刚才成功运行了 `src/data/weight_feature_engineering.py`，并输出了 `data/processed/stations_features.csv`。
- [ ] **T2.2 运力参数建模**: 将实时 Headway 转化为每分钟载客容量 ($C_{max}$) (待办)。

### 阶段三：核心数据挖掘 (Data Mining & Simulation) - ⏳ 计划中
- [ ] **T3.1 需求生成 (OD 挖掘)** (Sprint 2)
- [ ] **T3.2 路径分配算法 (MNL)** (Sprint 2)
- [ ] **T3.3 压力指数计算** (Sprint 2)

### 阶段四及五：预测、分析与验证 - ⏳ 计划中
- 交互式 Dashboard 开发、异常场景模拟及报告验证等将于 Sprint 3 开展。

---

## 🚀 下一步开发重点 (Next Steps)
1. 计算运力参数模型（动态容量）。
2. 在 `src/models/` 开发双约束引力模型 (Gravity Model) 以生成 OD 矩阵。
