import re
from .base import BaseAnalyzer, AnalysisResult

class CppAnalyzer(BaseAnalyzer):
    def analyze(self, file_path) -> AnalysisResult:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            content = "".join(lines)
        except Exception as e:
            return AnalysisResult(file_path.name, "C++", 0, "D", [f"无法读取: {str(e)}"])

        issues = []
        score = 100.0
        
        #  1. 注释覆盖率 
        # 简单正则去除 // 和 /* */
        def remove_comments(text):
            pattern = r"(\".*?\"|\'.*?\')|(/\*.*?\*/|//[^\r\n]*$)"
            # group 1 是字符串，group 2 是注释
            regex = re.compile(pattern, re.MULTILINE|re.DOTALL)
            def _replacer(match):
                if match.group(2) is not None:
                    return "" # 删掉注释
                else:
                    return match.group(1) # 保留字符串
            return regex.sub(_replacer, text)

        clean_code = remove_comments(content)
        clean_lines_count = len([l for l in clean_code.splitlines() if l.strip()])
        total_lines_count = len(lines)
        
        # 估算注释行
        comment_lines_est = total_lines_count - clean_lines_count
        ratio = comment_lines_est / total_lines_count if total_lines_count > 0 else 0
        
        if ratio < 0.1:
            score -= 10
            issues.append(f"🍷 余味干涩: 注释率仅 {ratio*100:.1f}%")

        #  2. 复杂度与嵌套分析
        # 统计关键字
        keywords = re.findall(r'\b(if|for|while|catch|case|\|\||&&)\b', clean_code)
        complexity_points = len(keywords)
        
        # 密度检测
        density = complexity_points / clean_lines_count if clean_lines_count > 0 else 0
        if density > 0.2: # 每5行就有1个逻辑跳转
             score -= 20
             issues.append(f"🕸️ 整体结构纠结: 逻辑密度过高 ({density:.2f})")

        #  3. 函数长度与嵌套
        brace_level = 0
        in_function = False
        func_start_line = 0
        current_func_lines = 0
        max_nesting = 0
        
        # 简单的函数头检测正则
        func_head_pattern = re.compile(r'\b([a-zA-Z0-9_]+)\s*\([^;]*\)\s*\{')

        for i, line in enumerate(lines):
            stripped = line.strip()
            # 忽略注释行
            if stripped.startswith('//') or stripped.startswith('/*'): continue
            
            # 统计开闭括号
            open_braces = stripped.count('{')
            close_braces = stripped.count('}')
            
            # 检测是否进入函数 (在 Level 0 时发现 '{' 且看起来像函数)
            if brace_level == 0 and open_braces > 0:
                match = func_head_pattern.search(line)
                if match:
                    in_function = True
                    func_start_line = i
                    current_func_lines = 0
                    max_nesting = 0
                    # 命名检查 (Go logic: C++ func usually Pascal or Camel)
                    func_name = match.group(1)
                    if not re.match(r'^[a-z]+[a-zA-Z0-9]*$', func_name) and not re.match(r'^[A-Z][a-zA-Z0-9]*$', func_name):
                         pass 

            if in_function:
                current_func_lines += 1
                
                # 嵌套深度估算
                if brace_level > 5:
                    max_nesting = max(max_nesting, brace_level)
            
            brace_level += (open_braces - close_braces)
            
            # 检测函数结束
            if in_function and brace_level == 0:
                in_function = False
                # 结算函数指标
                # 1. 长度
                if current_func_lines > 120:
                    score -= 5
                    issues.append(f"📏 极度臃肿: 函数 (约行{func_start_line}) 长度 {current_func_lines} 行")
                elif current_func_lines > 70:
                    score -= 2
                    issues.append(f"📏 臃肿: 函数 (约行{func_start_line}) 长度 {current_func_lines} 行")
                
                # 2. 嵌套
                if max_nesting > 5:
                    score -= 3
                    issues.append(f"🏗️ 嵌套过深: 函数 (约行{func_start_line}) 达到 {max_nesting} 层")

        #  4. 命名规范 (类名) 
        class_decls = re.findall(r'class\s+([a-zA-Z0-9_]+)', clean_code)
        for c in class_decls:
            if not c[0].isupper():
                score -= 2
                issues.append(f"🎨 类名缺乏威严: '{c}' 建议大写开头 (PascalCase)")

        #  5. 宏定义滥用检测 
        macros = len(re.findall(r'#define\s+', content))
        if macros > 20:
             score -= 5
             issues.append(f"⚠️ 预处理依赖: 宏定义过多 ({macros}个)，建议使用 const 或 inline")

        final_score = max(0, min(100, score))
        return AnalysisResult(
            file_name=file_path.name,
            language="C++",
            score=final_score,
            rating=self.calculate_rating(final_score),
            issues=issues
        )