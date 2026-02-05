import re
from .base import BaseAnalyzer, AnalysisResult

class CsharpAnalyzer(BaseAnalyzer):
    def analyze(self, file_path) -> AnalysisResult:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return AnalysisResult(file_path.name, "C#", 0, "D", [f"读取失败: {str(e)}"])

        issues = []
        score = 100.0
        lines = content.splitlines()

        #  1. 滥用 #region
        regions = content.count("#region")
        if regions > 3:
            score -= 5
            issues.append(f"🙈 视觉欺骗: 使用了 {regions} 个 #region，这通常是为了隐藏过长的代码")

        # 调试输出
        if "Console.WriteLine" in content or "Console.Write" in content:
            score -= 5
            issues.append(f"🗑️ 杂质残留: 包含 Console.Write 输出")

        #  2. 命名规范
        method_pattern = re.compile(r'\b(?:public|private|protected|internal)\s+(?:static\s+)?(?:[\w<>[\]]+\s+)([a-z][a-zA-Z0-9_]*)\s*\(', re.MULTILINE)
        
        bad_methods = []
        for match in method_pattern.finditer(content):
            name = match.group(1)
            # 排除 main (有时候写成小写), 排除 set/get
            if name not in ['main'] and not name.startswith('set_') and not name.startswith('get_'):
                bad_methods.append(name)
        
        if bad_methods:
            score -= min(20, len(bad_methods) * 3)
            sample = ", ".join(bad_methods[:3])
            issues.append(f"🎨 风格不纯: 方法 '{sample}...' 应当使用 PascalCase (大写开头)")

        # 接口命名建议以 I 开头
        interface_pattern = re.compile(r'\binterface\s+([a-zA-Z0-9_]+)')
        for match in interface_pattern.finditer(content):
            name = match.group(1)
            if not name.startswith('I') or (len(name) > 1 and not name[1].isupper()):
                score -= 2
                issues.append(f"🏷️ 标签错误: 接口 '{name}' 建议以 'I' 开头 (如 IService)")

        #  3. 结构分析 
        # C# 的 Lambda 和 LINQ 可能会导致单行极长
        long_lines = [i+1 for i, l in enumerate(lines) if len(l) > 120]
        if len(long_lines) > 5:
            score -= 5
            issues.append(f"📏 行宽溢出: {len(long_lines)} 行代码超过 120 字符 (建议换行)")

        # 嵌套深度
        max_nesting = 0
        depth = 0
        for line in lines:
            line = line.strip()
            if line.startswith('//'): continue
            
            depth += line.count('{')
            depth -= line.count('}')
            max_nesting = max(max_nesting, depth)
        
        if max_nesting > 6:
            score -= 10
            issues.append(f"🏗️ 结构极深: 最大嵌套深度达 {max_nesting} 层 (建议提取方法)")

        final_score = max(0, min(100, score))
        return AnalysisResult(
            file_name=file_path.name,
            language="C#",
            score=final_score,
            rating=self.calculate_rating(final_score),
            issues=issues
        )