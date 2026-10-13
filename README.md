# module3-e2e

模块③ 线路计划集成 E2E：七仓 tag 锁定依赖图上的链上门禁（WP22 起步，WP25 扩全矩阵）。

```
visit-ir v0.2.0 × visitmodel v0.2.0 × opticore v0.4.0 × plan-release v0.3.0
× service-rules v0.2.1 × dq-workbench v0.1.1
（传递：sraf——诊断路由在 ②e2e 已锁，本仓按依赖方向不重复）
```

## 门禁（5 项，WP22）

| # | 不变量 | 断言 |
|---|---|---|
| G1 | visit-plan 六态全链可发布 | new→simulate→submit→approve→activate；冻结字节不变；审计链可验 |
| G2 | visit-plan 形状 fail-fast | 缺 capacity 在 DRAFT 入口即拒（doc_type 分派） |
| G3 | 超载违规桥入工作台 | L2 ValidationReport → Finding（确定性排序）→ ingest → 工单 OPEN；重复 ingest 幂等 |
| G4 | 规则绑定存在性闸 | rule_set_ref 未发布=闸关；publish 后=闸开（F2 fail-closed 在发布时强制） |
| G6 | 池确认进审批链端到端 | spec→池(唯一 grounding)→准入/汰换候选(恒需批准)→confirm→绑定闸先关后开→六态发布零字节漂移 |
| G5 | 三层 import 链与 D2 贯通 | 七仓 pin 共存；W53 分歧 fail-closed 在集成环境可用 |

## 依赖方向纪律

桥（violations→findings）只存在于本集成层：visitmodel/plan-release 均不 import
dq-workbench（下层不知上层）。

## 运行

```bash
# 私有仓 pin 需凭据：git config --global url."https://<TOKEN>@github.com/topprismdata/".insteadOf "https://github.com/topprismdata/"
uv pip install "module3-e2e[dev] @ file:///path/to/this/repo"
# 装完务必 --unset（token 不留 gitconfig——③盘点泄漏教训）
python -m pytest tests -q   # 6 passed，全 hermetic
```
