/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // 自定义颜色
      colors: {
        // 主色 - 深绿
        primary: {
          50: '#f0f5f3',
          100: '#d9e5e0',
          200: '#b3ccc4',
          300: '#8db2a8',
          400: '#6b988c',
          500: '#4a7c6f', // 主色
          600: '#3d665b',
          700: '#305047',
          800: '#233a34',
          900: '#172522',
        },
        // 辅色 - 橙色
        accent: {
          50: '#fdf5ee',
          100: '#f9e4d0',
          200: '#f2c8a1',
          300: '#ebac73',
          400: '#d89050',
          500: '#c47c4a', // 辅色
          600: '#a5653d',
          700: '#864f30',
          800: '#673923',
          900: '#482316',
        },
        // 紫色
        purple: {
          50: '#f3f1f7',
          100: '#e2ddec',
          200: '#c5bbd9',
          300: '#a899c6',
          400: '#8b77b3',
          500: '#7a6b9d', // 紫色
          600: '#64577e',
          700: '#4e435f',
          800: '#382f40',
          900: '#221b21',
        },
        // 红色
        danger: {
          50: '#faf0f0',
          100: '#f2dada',
          200: '#e5b5b4',
          300: '#d8908e',
          400: '#cb6b68',
          500: '#b85450', // 红色
          600: '#974441',
          700: '#763432',
          800: '#552422',
          900: '#341413',
        },
        // 背景色
        bg: {
          DEFAULT: '#faf8f5',
          secondary: '#f5f2ed',
          card: '#ffffff',
        },
        // 文字色
        text: {
          DEFAULT: '#2c3e3a',
          secondary: '#5a6b66',
          tertiary: '#8a9a95',
          inverse: '#ffffff',
        },
      },
      // 自定义字体
      fontFamily: {
        sans: [
          '-apple-system',
          'BlinkMacSystemFont',
          '"Segoe UI"',
          'Roboto',
          '"Helvetica Neue"',
          'Arial',
          '"PingFang SC"',
          '"Hiragino Sans GB"',
          '"Microsoft YaHei"',
          'sans-serif',
        ],
        mono: [
          '"JetBrains Mono"',
          '"Fira Code"',
          '"Consolas"',
          '"Monaco"',
          'monospace',
        ],
      },
      // 自定义间距
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      // 自定义动画
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'bounce-subtle': 'bounceSubtle 2s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInRight: {
          '0%': { transform: 'translateX(20px)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
        bounceSubtle: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-3px)' },
        },
      },
      // 自定义阴影
      boxShadow: {
        'soft': '0 2px 8px rgba(44, 62, 58, 0.06)',
        'medium': '0 4px 16px rgba(44, 62, 58, 0.08)',
        'large': '0 8px 32px rgba(44, 62, 58, 0.1)',
      },
      // 自定义圆角
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
      },
    },
  },
  plugins: [],
}
