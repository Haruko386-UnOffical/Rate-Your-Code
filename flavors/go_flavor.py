import re
from .base import BaseAnalyzer, AnalysisResult

class GoAnalyzer(BaseAnalyzer):
    def analyze(self, file_path) -> AnalysisResult:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return AnalysisResult(file_path.name, "Go", 0, "D", [f"无法开启瓶塞: {str(e)}"])

        issues = []
        score = 100.0
        lines = content.splitlines()

        # --- 1. 注释覆盖率 (Go 社区非常看重 Godoc) ---
        # 简单去除字符串干扰，统计 // 和 /*
        clean_code = re.sub(r'(".*?"|`.*?`)', '', content, flags=re.DOTALL)
        comment_matches = re.findall(r'(//[^\n]*|/\*.*?\*/)', content, flags=re.DOTALL)
        
        # 估算注释行数
        comment_lines = sum(len(m.splitlines()) for m in comment_matches)
        total_lines = len(lines)
        ratio = comment_lines / total_lines if total_lines > 0 else 0
        
        if ratio < 0.1:
            score -= 10
            issues.append(f"🍷 缺乏陈酿说明: 注释率仅 {ratio*100:.1f}% (Go 标准建议 > 15%)")

        # --- 2. 导出函数文档检查 (Public Func) ---
        # Go 规则: 大写开头的函数是导出的，应该有注释
        # 匹配: func (r Receiver) FuncName 或 func FuncName
        func_pattern = re.compile(r'^func\s+(?:\([^)]+\)\s+)?([A-Z][a-zA-Z0-9_]*)', re.MULTILINE)
        
        for i, line in enumerate(lines):
            match = func_pattern.search(line)
            if match:
                func_name = match.group(1)
                # 检查上一行是否有注释
                if i > 0 and not lines[i-1].strip().startswith('//'):
                    score -= 2
                    issues.append(f"📝 标签缺失: 导出函数 '{func_name}' 缺少文档注释")

        # --- 3. 复杂度分析 (if err != nil 地狱) ---
        keywords = re.findall(r'\b(if|for|switch|select|case|\|\||&&)\b', clean_code)
        complexity = len(keywords)
        density = complexity / total_lines if total_lines > 0 else 0
        
        if density > 0.25:
             score -= 15
             issues.append(f"🕸️ 逻辑纠结: 控制流密度过高 ({density:.2f})")

        # --- 4. 命名规范 (Go 偏好短命名，但不能太短) ---
        # 检查是否有 interface{} 滥用 (Empty Interface)
        empty_interfaces = len(re.findall(r'interface\{\}', clean_code))
        if empty_interfaces > 5:
            score -= 5
            issues.append(f"⚠️ 类型模糊: 过度使用 interface{{}} ({empty_interfaces}处)，建议定义具体接口")

        # 检查蛇形命名 (Go 严格要求 CamelCase)
        snake_vars = re.findall(r'\bvar\s+([a-z]+_[a-z]+)\s+', clean_code)
        for v in snake_vars:
            score -= 2
            issues.append(f"🎨 色泽偏差: 变量 '{v}' 使用了蛇形命名，Go 推荐 CamelCase")

        # --- 5. 函数长度 ---
        # 简单括号计数法
        current_len = 0
        brace_balance = 0
        in_func = False
        start_line = 0

        for i, line in enumerate(lines):
            if line.startswith('func '):
                in_func = True
                start_line = i
                current_len = 0
                brace_balance = 0
            
            if in_func:
                current_len += 1
                brace_balance += line.count('{') - line.count('}')
                
                if brace_balance == 0 and current_len > 1: # 函数结束
                    in_func = False
                    if current_len > 80: # Go 代码通常较短
                        score -= 5
                        issues.append(f"📏 酒体过重: 函数 (行{start_line+1}) 长度 {current_len} 行")

        final_score = max(0, min(100, score))
        return AnalysisResult(
            file_name=file_path.name,
            language="Go",
            score=final_score,
            rating=self.calculate_rating(final_score),
            issues=issues
        )