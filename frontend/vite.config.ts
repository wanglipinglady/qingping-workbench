import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 加载环境变量
  const env = loadEnv(mode, process.cwd(), '');

  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      // 开发服务器端口
      port: 5173,
      // 启动时自动打开浏览器
      open: false,
      // 允许跨域
      cors: true,
      // 代理配置（可选，用于开发环境 API 代理）
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8080',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '/api'),
        },
      },
    },
    build: {
      // 输出目录
      outDir: 'dist',
      // 静态资源目录
      assetsDir: 'assets',
      // 构建时是否生成 source map
      sourcemap: false,
      // 代码压缩配置
      minify: 'esbuild',
      // chunk 大小警告限制（KB）
      chunkSizeWarningLimit: 1500,
      rollupOptions: {
        output: {
          // 手动分包
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'markdown-vendor': ['react-markdown', 'react-syntax-highlighter', 'remark-gfm'],
          },
        },
      },
    },
    // 预构建优化
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        'zustand',
        'axios',
        'react-markdown',
        'react-syntax-highlighter',
      ],
    },
  };
});
