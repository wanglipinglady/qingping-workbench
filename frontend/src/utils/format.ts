/**
 * 格式化工具函数
 * 提供日期、文件大小、数字等格式化功能
 */

/**
 * 日期格式化
 * @param date 日期对象或日期字符串
 * @param format 格式化字符串
 *  - YYYY: 四位年份
 *  - MM: 两位月份
 *  - DD: 两位日期
 *  - HH: 两位小时(24小时制)
 *  - mm: 两位分钟
 *  - ss: 两位秒数
 *  - dddd: 星期几（中文）
 * @returns 格式化后的日期字符串
 */
export function formatDate(
  date: Date | string | number,
  format: string = 'YYYY-MM-DD HH:mm:ss'
): string {
  const d = new Date(date);

  // 无效日期处理
  if (isNaN(d.getTime())) {
    return '';
  }

  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const seconds = String(d.getSeconds()).padStart(2, '0');

  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六'];
  const weekday = weekdays[d.getDay()];

  return format
    .replace('YYYY', String(year))
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
    .replace('ss', seconds)
    .replace('dddd', weekday);
}

/**
 * 格式化文件大小
 * @param bytes 字节数
 * @returns 格式化后的文件大小字符串
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  if (bytes < 0) return '0 B';

  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${(bytes / Math.pow(k, i)).toFixed(i === 0 ? 0 : 2)} ${sizes[i]}`;
}

/**
 * 格式化数字（千分位）
 * @param num 数字
 * @returns 格式化后的数字字符串
 */
export function formatNumber(num: number): string {
  return num.toLocaleString('zh-CN');
}

/**
 * 相对时间格式化
 * @param date 日期对象或日期字符串
 * @returns 相对时间字符串
 */
export function formatRelativeTime(date: Date | string | number): string {
  const d = new Date(date);
  const now = new Date();
  const diff = now.getTime() - d.getTime();

  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  const week = 7 * day;
  const month = 30 * day;
  const year = 365 * day;

  if (diff < minute) {
    return '刚刚';
  } else if (diff < hour) {
    return `${Math.floor(diff / minute)} 分钟前`;
  } else if (diff < day) {
    return `${Math.floor(diff / hour)} 小时前`;
  } else if (diff < week) {
    return `${Math.floor(diff / day)} 天前`;
  } else if (diff < month) {
    return `${Math.floor(diff / week)} 周前`;
  } else if (diff < year) {
    return `${Math.floor(diff / month)} 个月前`;
  } else {
    return `${Math.floor(diff / year)} 年前`;
  }
}

/**
 * 截断文本
 * @param text 文本
 * @param maxLength 最大长度
 * @returns 截断后的文本
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

/**
 * 格式化持续时间
 * @param seconds 秒数
 * @returns 格式化的持续时间
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds} 秒`;
  } else if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return secs > 0 ? `${mins} 分 ${secs} 秒` : `${mins} 分钟`;
  } else {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    return mins > 0 ? `${hours} 小时 ${mins} 分` : `${hours} 小时`;
  }
}

/**
 * 百分比格式化
 * @param value 小数值 (0-1)
 * @param decimals 小数位数
 * @returns 百分比字符串
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}
