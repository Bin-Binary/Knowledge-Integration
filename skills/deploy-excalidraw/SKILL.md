---
name: deploy-excalidraw
description: 当用户需要在本地部署 Excalidraw 手绘白板工具时使用。触发词如"部署Excalidraw""本地装Excalidraw""搭建手绘画板"。
---

# 本地部署 Excalidraw

## 概述

基于 Vite + React 18 搭建本地 Excalidraw 实例，解决官方包与 React 19 不兼容、Vite 环境下 `process is not defined` 等常见问题。

## 适用场景

- 用户说"部署 Excalidraw""本地装 Excalidraw""搭建手绘画板"
- 需要本地可用的手绘白板，而非 excalidraw.com 在线版

不适用：需要 Docker 部署、需要多人协作后端、需要嵌入已有 React 19 项目。

## 环境前提

- Node.js ≥ 18
- npm
- 无需 Git（手动创建文件）
- 无需 Docker

## 部署步骤

### 1. 创建项目目录

```bash
mkdir <project_dir> && cd <project_dir>
```

### 2. 创建 package.json

```json
{
  "name": "excalidraw-app",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@excalidraw/excalidraw": "0.17.6"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.3.4",
    "typescript": "~5.7.2",
    "vite": "^6.0.5"
  }
}
```

### 3. npm install

```bash
npm install
```

### 4. 创建项目文件

**index.html**

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Excalidraw</title>
    <link href="https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&display=swap" rel="stylesheet">
    <style>
      html, body, #root {
        margin: 0;
        padding: 0;
        height: 100%;
        width: 100%;
        overflow: hidden;
      }
      @font-face {
        font-family: "Virgil";
        src: url("https://excalidraw.com/Virgil.woff2") format("woff2");
        font-display: swap;
      }
      @font-face {
        font-family: "Virgil";
        src: local("ZCOOL KuaiLe"), local("Microsoft YaHei"), local("SimHei");
        unicode-range: U+4E00-9FFF, U+3400-4DBF, U+20000-2A6DF, U+2A700-2B73F, U+2B740-2B81F, U+2B820-2CEAF, U+F900-FAFF, U+2F800-2FA1F;
      }
    </style>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

**vite.config.ts**

```ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  define: {
    "process.env.IS_PREACT": JSON.stringify("false"),
    process: { env: {} },
  },
});
```

**tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

**src/main.tsx**

```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
```

**src/App.tsx**

```tsx
import { Excalidraw } from "@excalidraw/excalidraw";

function App() {
  return (
    <div style={{ height: "100vh", width: "100vw" }}>
      <Excalidraw />
    </div>
  );
}

export default App;
```

### 5. 启动

```bash
npm run dev
```

浏览器打开 `http://localhost:5173/`。

## 常见问题速查

| 问题 | 原因 | 修复 |
|------|------|------|
| ERESOLVE peer dependency | React 19 与 excalidraw 不兼容 | package.json 锁定 react ^18.2.0 |
| `process is not defined` | Vite 不注入 Node.js 全局变量 | vite.config.ts 中 `define: { process: { env: {} } }` |
| 布局溢出/截断 | 容器未撑满视口 | index.html 中 html/body/#root 均 `height:100%; overflow:hidden` |
| 中文显示为宋体/黑体 | Hand-drawn 字体 Virgil 不含中文 | index.html 中 @font-face 用 unicode-range 让中文走 ZCOOL KuaiLe |

## 操作提示

| 操作 | 方法 |
|------|------|
| 画水平/垂直线 | 按住 Shift 拖拽 |
| 大括号 { } | Draw 工具手画（快捷键 P）或 Text 工具键盘输入 |
| 更多颜色 | 选中元素 → 点击 Stroke/Background 文字按钮 → 展开完整调色板 → 可输入 Hex 值 |
| 字体风格 | 选中文本 → Font family：Hand-drawn / Normal / Code |
| 手绘粗糙度 | Sloppiness：Architect（整洁）/ Artist（适中）/ Cartoonist（最潦草） |
| 撤销/重做 | Ctrl+Z / Ctrl+Shift+Z |
