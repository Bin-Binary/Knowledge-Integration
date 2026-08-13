# Writing Good Tests

# 编写优秀测试

**Load this reference when:** writing or changing tests, adding mocks, or
adding cleanup/helper methods for tests.

**何时加载此参考：** 编写或修改测试、添加模拟对象、或添加测试的清理/辅助方法时。

## Overview

## 概述

A test exists to catch a specific break. Two principles govern everything
here:

测试存在的意义在于捕获特定的故障。这里的一切都遵循两条原则：

```
1. Every test names the break it catches
2. Every test exercises the real thing
```

```
1. 每个测试都命名它所捕获的故障
2. 每个测试都演练真实事物
```

Strict TDD produces both naturally: a test written first and watched
failing against real code has already proven it can fail, and only earns
a mock when the real dependency proves slow or external.

严格的TDD自然产生这两点：先编写并观察其在真实代码上失败的测试已经证明它能失败，只有当真实依赖项证明缓慢或外部时才使用模拟。

## Principle 1: Name the Break

## 原则1：命名故障点

Before writing the test body, answer: **what production change should
make this test fail — and is that change a bug or a decision?** A test
earns its place by catching a wrong branch, missing side effect, wrong
argument, boundary case, or broken contract.

在编写测试体之前，先回答：**什么生产代码变更应该让这个测试失败——这种变更是一个bug还是一个决策？** 测试的价值在于捕获错误的分支、遗漏的副作用、错误的参数、边界情况或破坏的契约。

**Derive expectations independently.** Use literals and hand-checked
fixtures; table-driven tests with literal `want` values are the preferred
shape. An expectation computed by the code under test — or its helpers —
passes no matter what that code does:

**独立推导期望值。** 使用字面量和手工检查的固件；带有字面量 `want` 值的表驱动测试是首选形式。由被测代码——或其辅助函数——计算出的期望值，无论该代码做什么都会通过：

```typescript
// ❌ Mirror assertion: the same builder computes both sides — always true
const expected = buildSearchQuery({ tag: 'urgent' });
expect(buildSearchQuery({ tag: 'urgent' })).toBe(expected);

// ❌ 镜像断言：同一个构建器计算两边——总是为真
const expected = buildSearchQuery({ tag: 'urgent' });
expect(buildSearchQuery({ tag: 'urgent' })).toBe(expected);
```

```typescript
// ✅ Hand-derived literal
expect(buildSearchQuery({ tag: 'urgent' })).toBe('tag:"urgent"');

// ✅ 手工推导的字面量
expect(buildSearchQuery({ tag: 'urgent' })).toBe('tag:"urgent"');
```

**No change detectors.** If only intentional decisions can fail a test —
a constant's value, exact message wording, private structure — it fires
on redesign and sleeps through bugs. Test the behavior that depends on
the decision: not `expect(MAX_RETRIES).toBe(5)` but "a failing call is
retried 5 times and the 6th attempt never happens."

**不要写变更检测器。** 如果只有刻意决策才能让测试失败——常量的值、精确的消息措辞、私有结构——它会在重构时报警，却对真正的bug无动于衷。测试依赖该决策的行为：不是 `expect(MAX_RETRIES).toBe(5)`，而是"失败的调用会重试5次，且第6次尝试永远不会发生。"

**Behavior, not text.** Asserting that a script, skill, or config
contains an exact line proves only that the source is the source. Run
scripts against controlled inputs and assert outputs, side effects, or
exit codes. Documents that instruct agents are tested by the consuming
agent's behavior (superpowers:writing-skills); prose for humans earns no
test at all.

**测试行为，而非文本。** 断言脚本、技能或配置包含精确的某一行只能证明源文件就是源文件。用受控输入运行脚本并断言输出、副作用或退出码。用于指导代理的文档通过消费代理的行为来测试；给人类看的文字描述不需要测试。

**Your code, not the framework.** Test the contract your code makes at
its boundaries — the route you register, the query you emit, the payload
you produce. Upstream mechanics are their maintainers' tests to write
(the classic: asserting your router invokes a registered handler — that
is the framework's test, not yours). When upstream behavior genuinely
surprised you, write one narrow characterization test naming the
assumption. The same boundary applies inside your code: constructors,
getters, constants, and trivial forwarding earn tests only when they
validate, normalize, default, derive, enforce, or cause side effects —
otherwise assert the first consumer-visible result that depends on them.

**测试你的代码，而非框架。** 测试你的代码在边界处建立的契约——你注册的路由、你发出的查询、你产生的载荷。上游机制是上游维护者的测试责任（经典案例：断言你的路由器调用了注册的处理器——那是框架的测试，不是你的）。当上游行为确实让你感到意外时，编写一个窄化的表征测试来命名该假设。同样的边界也适用于你的代码内部：构造器、getter、常量和简单转发只有在它们执行验证、规范化、默认值、推导、强制或引起副作用时才值得测试——否则断言依赖它们的第一个对消费者可见的结果。

### Gate Function

### 门禁函数

```
BEFORE writing the test body:
  Name the production change that would make this test fail.

  Cannot name one            → redesign around an observable behavior
  "The source text changed"  → run the artifact and assert its effects
  Only intentional decisions → change detector; test the behavior
                               that depends on the decision

  Confirm the expected value is derived without the code under test.
  IF it reuses the code's logic or helpers:
    Replace it with a literal or hand-checked fixture
```

```
在编写测试体之前：
  命名会让此测试失败的生产代码变更。

  无法命名一个          → 围绕可观察行为重新设计
  "源文本改变了"        → 运行工件并断言其效果
  仅是刻意决策          → 变更检测器；测试依赖该决策的行为

  确认期望值的推导不依赖被测代码。
  如果它复用了代码的逻辑或辅助函数：
    用字面量或手工检查的固件替换它
```

## Principle 2: Exercise the Real Thing

## 原则2：演练真实事物

**The mock earns no assertions.** A mock assertion passes when the mock
is present and fails when it is absent — it says nothing about the
component. Assert the real component's behavior; if the mock is what you
are checking, unmock it or delete the assertion.

**模拟对象不配拥有断言。** 模拟断言在模拟存在时通过，在模拟缺席时失败——它对组件没有任何说明。断言真实组件的行为；如果你检查的就是模拟本身，取消模拟或删除该断言。

```typescript
// ✅ Real behavior
expect(screen.getByRole('navigation')).toBeInTheDocument();

// ✅ 真实行为
expect(screen.getByRole('navigation')).toBeInTheDocument();
```

```typescript
// ❌ Mock existence
expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();

// ❌ 模拟存在性
expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
```

**your human partner's correction:** "Are we testing the behavior of a
mock?"

**你的人类搭档的纠正：** "我们是在测试模拟的行为吗？"

**Mock at the right level.** Learn every side effect of the real method
before replacing it; mock the slow or external operation and keep what
the test depends on real. When unsure, run the test against the real
implementation first and observe what actually needs to happen.

**在正确的层次进行模拟。** 在替换真实方法之前，了解它的每个副作用；模拟缓慢或外部的操作，保持测试依赖的部分真实。当不确定时，先用真实实现运行测试并观察实际需要发生什么。

```typescript
// ❌ The mock swallows the config write that duplicate detection reads
vi.mock('ToolCatalog', () => ({
  discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
}));

// ❌ 模拟吞掉了重复检测读取的配置写入
vi.mock('ToolCatalog', () => ({
  discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
}));
```

```typescript
// ✅ Mock only the slow server startup; the config write stays real
vi.mock('MCPServerManager');

// ✅ 仅模拟缓慢的服务器启动；配置写入保持真实
vi.mock('MCPServerManager');
```

**Make doubles specific.** When arguments, call counts, or ordering are
part of the contract, assert them — a fake that accepts anything verifies
nothing. Give each branch (success, error, malformed) its own fixture or
spy, so the wrong branch cannot satisfy the expectation.

**让替身具体化。** 当参数、调用次数或顺序是契约的一部分时，断言它们——接受任何东西的伪对象验证不了任何东西。给每个分支（成功、错误、畸形）自己的固件或间谍，这样错误的分支无法满足期望。

**Mirror real data completely.** Mock the complete structure as it exists
in reality — all documented fields — not just the ones your test reads.
Partial mocks fail silently when downstream code reads an omitted field:
the test passes while integration breaks.

**完全镜像真实数据。** 模拟现实中存在的完整结构——所有已记录的字段——而不仅仅是测试读取的字段。部分模拟会在下游代码读取被遗漏的字段时静默失败：测试通过，但集成崩溃。

**Production classes carry production methods only.** Cleanup that only
tests need lives in test utilities, never as a `destroy()` on the
production class. Ask: is this method called only from tests? Does this
class own this resource's lifecycle? Wrong answers → test utility.

**生产类只承载生产方法。** 仅测试需要的清理逻辑存在于测试工具中，永远不要作为生产类上的 `destroy()` 方法。问问：这个方法是否只从测试调用？这个类是否拥有此资源的生命周期？错误答案 → 测试工具。

**Prefer real components over complex mocks.** When mock setup outgrows
the test logic, mocks miss methods the real components have, or tests
break when the mock changes, switch to an integration test with real
components. **your human partner's question:** "Do we need to be using a
mock here?"

**优先使用真实组件而非复杂模拟。** 当模拟设置超出测试逻辑、模拟缺少真实组件拥有的方法、或测试在模拟变更时失败，切换到使用真实组件的集成测试。**你的人类搭档的问题：** "我们这里需要使用模拟吗？"

### Gate Function

### 门禁函数

```
BEFORE adding a mock or test helper:
  List the real method's side effects; keep the ones the test
  depends on real — mock the slow/external level below them.

  Mock responses mirror the complete real structure.

  A method only tests call lives in test utilities, not production.

  About to assert on the mock itself?
    Unmock it or delete the assertion.
```

```
在添加模拟或测试助手之前：
  列出真实方法的副作用；保持测试依赖的部分真实——模拟它们之下的缓慢/外部层级。

  模拟响应完全镜像真实结构。

  仅测试调用的方法存在于测试工具中，而非生产代码。

  准备对模拟本身断言？
    取消模拟或删除该断言。
```

## Tests Ship With the Implementation

## 测试与实现一同交付

The TDD cycle — failing test, minimal implementation, refactor — is what
"complete" means. Ship the tests the behavior needs and only those:
trivial code and human prose earn none, and a test written to satisfy
process costs maintenance forever.

TDD循环——失败的测试、最小实现、重构——这就是"完整"的含义。交付行为需要的测试，仅此而已：琐碎代码和人类文字描述不需要测试，为满足流程而编写的测试永远消耗维护成本。

## The Mutation Check

## 变异检查

Before finishing, mentally mutate the production code; at least one test
should fail for each realistic mutation:

在完成之前，在脑海中变异生产代码；每个现实的变异都应该至少有一个测试失败：

- Wrong constant or argument
- 错误的常量或参数

- Wrong branch handler
- 错误的分支处理

- Missing state change or side effect
- 遗漏状态变化或副作用

- Empty or default return
- 空或默认返回

- Missing validation for zero, empty, nil, unauthorized, or malformed input
- 遗漏对零、空、nil、未授权或畸形输入的验证

A mutation nothing catches marks the behavior as unprotected — or the
test as tautological.

没有任何测试捕获的变异标志着行为未受保护——或测试是同义反复。

## Quick Reference

## 快速参考

| When you... | Do |
|-------------|-----|
| Write any test | Name the break it catches — a bug, not a decision |
| Build an expected value | Derive it by hand; never with the code under test |
| Test a script or document | Run it / pressure-test its consumer; never grep its text |
| Reach for a dependency test | Test your boundary contract, not their documented mechanics |
| Want to assert on a mocked element | Test the real component, or unmock it |
| Are about to mock a method | Learn its side effects; mock the slow/external level |
| Build a mock response | Mirror the real structure completely |
| Need cleanup only tests use | Put it in test utilities |
| Watch mock setup balloon | Switch to an integration test with real components |
| Finish a test file | Run the mutation check |

| 当你... | 做 |
|---------|-----|
| 编写任何测试 | 命名它捕获的故障——是bug，不是决策 |
| 构建期望值 | 手工推导；永远不要用被测代码 |
| 测试脚本或文档 | 运行它/压力测试其消费者；永远不要grep其文本 |
| 着手依赖项测试 | 测试你的边界契约，而非他们文档化的机制 |
| 想对模拟元素断言 | 测试真实组件，或取消模拟 |
| 准备模拟一个方法 | 了解其副作用；模拟缓慢/外部层级 |
| 构建模拟响应 | 完全镜像真实结构 |
| 需要仅测试使用的清理 | 放入测试工具 |
| 看着模拟设置膨胀 | 切换到使用真实组件的集成测试 |
| 完成一个测试文件 | 运行变异检查 |

## Warning Signs

## 警示信号

- Setup and assertion share the same object, guaranteeing equality
- 设置和断言共享同一对象，保证相等

- The test can fail only through a panic, crash, or missing selector
- 测试只能通过panic、崩溃或缺失的选择器失败

- The test fails on every intentional change, never on accidental breakage
- 测试在每次刻意变更时失败，从不在意外破坏时失败

- Expected values are hidden behind loops, builders, or helpers
- 期望值隐藏在循环、构建器或辅助函数背后

- The test greps source text, or asserts a removed symbol stays removed
- 测试grep源文本，或断言被移除的符号保持移除

- The test would still matter if only the framework remained
- 如果只剩下框架，测试仍然有意义

- The test exists for coverage, checking no side effect or outcome
- 测试为了覆盖率存在，不检查副作用或结果

- An assertion checks a `*-mock` test ID, or fails if you remove the mock
- 断言检查 `*-mock` 测试ID，或在你移除模拟时失败

- A method is called only from test files
- 方法仅从测试文件调用

- Mock setup is more than half the test, or you can't explain why the mock is needed
- 模拟设置超过测试的一半，或你无法解释为什么需要模拟

- Mocking "just to be safe"
- 模拟"只是为了安全"
