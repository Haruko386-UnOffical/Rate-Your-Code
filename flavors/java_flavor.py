import re
from .base import BaseAnalyzer, AnalysisResult

class JavaAnalyzer(BaseAnalyzer):
    def analyze(self, file_path) -> AnalysisResult:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return AnalysisResult(file_path.name, "Java", 0, "D", [f"读取失败: {str(e)}"])

        issues = []
        score = 100.0
        lines = content.splitlines()
 
        # 1. 调试代码残留
        if "System.out.println" in content:
            count = content.count("System.out.println")
            score -= 2 * count
            issues.append(f"🗑️ 杂质残留: 发现 {count} 处 System.out.println，建议使用日志框架")

        # 暴力捕获异常
        catch_all = len(re.findall(r'catch\s*\(\s*Exception\s+[a-z0-9_]+\s*\)', content))
        if catch_all > 0:
            score -= 5 * catch_all
            issues.append(f"🛡️ 掩耳盗铃: 发现 {catch_all} 处捕获所有 Exception，建议捕获具体异常")

        # e.printStackTrace()
        if "e.printStackTrace()" in content:
            score -= 5
            issues.append(f"⚠️ 处理粗糙: 使用了 printStackTrace()，生产环境会导致日志混乱")

        #  2. 命名规范 
        # 类名必须大写开头
        class_decls = re.findall(r'\bclass\s+([a-z][a-zA-Z0-9_]*)', content)
        for c in class_decls:
            score -= 5
            issues.append(f"🎨 类名色泽黯淡: '{c}' 必须使用 PascalCase (大写开头)")
            
        # 常量建议大写蛇形
        bad_constants = re.findall(r'static\s+final\s+\w+\s+([a-z][a-zA-Z0-9]*)', content)
        for c in bad_constants:
            score -= 2
            issues.append(f"🎨 常量命名不当: '{c}' 建议使用 UPPER_SNAKE_CASE")

        #  3. 复杂度分析 
        # Java 很容易写出嵌套很深的 if/else
        clean_code = re.sub(r'//.*|/\*[\s\S]*?\*/', '', content)
        keywords = re.findall(r'\b(if|for|while|switch|case|catch)\b', clean_code)
        
        complexity_density = len(keywords) / (len(lines) or 1)
        if complexity_density > 0.2:
             score -= 10
             issues.append(f"🕸️ 结构纠结: 代码复杂度密度高 ({complexity_density:.2f})")

        #  4. 长度检查 
        if len(lines) > 500:
            score -= 5
            issues.append(f"📏 瓶身过大: 文件包含 {len(lines)} 行，违背了单一职责原则")

        final_score = max(0, min(100, score))
        return AnalysisResult(
            file_name=file_path.name,
            language="Java",
            score=final_score,
            rating=self.calculate_rating(final_score),
            issues=issues
        )