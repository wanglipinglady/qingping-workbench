"""
文本分块器
将长文本按策略切分成适合向量化的小块
"""
import re
from typing import List


class TextSplitter:
    """
    文本分块器
    支持按段落 + 字符数的混合分块策略，并使用重叠保证上下文连续性
    """

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        separator: str = "\n\n",
    ):
        """
        初始化文本分块器

        Args:
            chunk_size: 每个分块的最大字符数
            chunk_overlap: 分块之间的重叠字符数
            separator: 段落分隔符
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def split_text(self, text: str) -> List[str]:
        """
        将文本切分为多个小块

        策略：
        1. 先按段落分隔符切分
        2. 小段落合并，不超过 chunk_size
        3. 超长段落进一步按句子切分
        4. 块之间保留重叠，保证上下文连续

        Args:
            text: 原始文本

        Returns:
            文本块列表
        """
        if not text or not text.strip():
            return []

        # 规范化换行
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # 第一步：按段落切分
        paragraphs = self._split_by_paragraph(text)

        # 第二步：合并段落为分块
        chunks = self._merge_paragraphs(paragraphs)

        # 第三步：处理超长块，按句子进一步切分
        final_chunks = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                final_chunks.append(chunk)
            else:
                # 超长块需要进一步切分
                sub_chunks = self._split_long_text(chunk)
                final_chunks.extend(sub_chunks)

        # 第四步：添加重叠
        if self.chunk_overlap > 0 and len(final_chunks) > 1:
            final_chunks = self._add_overlap(final_chunks)

        return final_chunks

    def _split_by_paragraph(self, text: str) -> List[str]:
        """按段落切分文本"""
        # 按空行分割段落
        paragraphs = re.split(rf"{self.separator}+", text)
        # 过滤空段落并去除首尾空白
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs

    def _merge_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """合并小段落为较大的块"""
        chunks: List[str] = []
        current_chunk = ""

        for para in paragraphs:
            if not current_chunk:
                current_chunk = para
            elif len(current_chunk) + len(para) + 2 <= self.chunk_size:
                # 可以合并
                current_chunk += "\n\n" + para
            else:
                # 当前块已满，保存并开始新块
                chunks.append(current_chunk)
                current_chunk = para

        # 保存最后一个块
        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_long_text(self, text: str) -> List[str]:
        """
        切分超长文本
        优先按句子切分，然后按字符硬切分
        """
        # 先按句子切分
        sentences = re.split(r"(?<=[。！？.!?])\s*", text)
        sentences = [s for s in sentences if s.strip()]

        chunks: List[str] = []
        current_chunk = ""

        for sent in sentences:
            if not current_chunk:
                if len(sent) > self.chunk_size:
                    # 单句就超长，按字符硬切
                    chunks.extend(self._split_by_chars(sent))
                else:
                    current_chunk = sent
            elif len(current_chunk) + len(sent) <= self.chunk_size:
                current_chunk += sent
            else:
                chunks.append(current_chunk)
                if len(sent) > self.chunk_size:
                    chunks.extend(self._split_by_chars(sent))
                    current_chunk = ""
                else:
                    current_chunk = sent

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def _split_by_chars(self, text: str) -> List[str]:
        """按字符数硬切分"""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start = end
        return chunks

    def _add_overlap(self, chunks: List[str]) -> List[str]:
        """
        为分块添加重叠
        每个块的开头从前一个块末尾截取 overlap 长度的内容
        """
        if not chunks or self.chunk_overlap <= 0:
            return chunks

        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]

            # 从前一个块末尾取重叠部分
            overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk

            # 合并重叠 + 当前块（注意总长度不要超过 chunk_size + overlap）
            merged = overlap_text + curr_chunk
            if len(merged) > self.chunk_size + self.chunk_overlap:
                # 如果太长，截断
                merged = merged[: self.chunk_size + self.chunk_overlap]

            result.append(merged)

        return result
