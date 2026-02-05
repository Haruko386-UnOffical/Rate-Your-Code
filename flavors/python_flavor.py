import ast
import re
import tokenize
from io import BytesIO
from collections import defaultdict
from .base import BaseAnalyzer, AnalysisResult

class PythonAnalyzer(BaseAnalyzer):
    def analyze(self, file_path) -> AnalysisResult:
        try:
            with open(file_path, 'rb') as f:
                content_bytes = f.read()
            content_str = content_bytes.decode('utf-8')
        except Exception as e:
            return AnalysisResult(file_path.name, "Python", 0, "D", [f"无法读取: {str(e)}"])

        issues = []
        score = 100.0
        
        #  1. 注释覆盖率 (Comment Ratio) 
        # 使用 tokenize 准确区分注释和代码
        total_lines = 0
        comment_lines = 0
        try:
            tokens = tokenize.tokenize(BytesIO(content_bytes).readline)
            for tok in tokens:
                if tok.type == tokenize.COMMENT:
                    comment_lines += 1
                elif tok.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING):
                    # 粗略估算代码行（非空行）
                    pass
            total_lines = len(content_str.splitlines())
        except:
            # Tokenize 失败降级处理
            total_lines = len(content_str.splitlines())
        
        # 移植 Go 逻辑: < 10% 警告
        ratio = comment_lines / total_lines if total_lines > 0 else 0
        if ratio < 0.1:
            score -= 10
            issues.append(f"🍷 余味不足: 注释率仅为 {ratio*100:.1f}% (建议 > 10%)")

        #  AST 解析 
        try:
            tree = ast.parse(content_str)
        except SyntaxError as e:
            return AnalysisResult(file_path.name, "Python", 0, "D", [f"❌ 语法错误: {e}"])

        #  2. 函数分析 (长度、复杂度、参数、嵌套) 
        func_count = 0
        total_complexity = 0
        structure_fingerprints = defaultdict(list) # 用于查重

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_count += 1
                func_name = node.name
                
                # A. 长度 (Function Length) -> Go: >40, >70, >120
                length = node.end_lineno - node.lineno
                if length > 120:
                    score -= 5
                    issues.append(f"📏 酒体过重: 函数 '{func_name}' 长达 {length} 行 (建议拆分)")
                elif length > 70:
                    score -= 2
                    issues.append(f"📏 酒体略重: 函数 '{func_name}' 长度 {length} 行")

                # B. 参数数量 -> Go: >6, >8
                args_count = len(node.args.args)
                if args_count > 6:
                    score -= 2
                    issues.append(f"⚖️ 成分复杂: 函数 '{func_name}' 参数过多 ({args_count}个)")

                # C. 命名规范 (Naming) -> Python: snake_case
                if not re.match(r'^[a-z_][a-z0-9_]*$', func_name) and not (func_name.startswith('__') and func_name.endswith('__')):
                    score -= 1
                    issues.append(f"🎨 色泽偏差: 函数 '{func_name}' 建议使用 snake_case")

                # D. 循环复杂度 (Cyclomatic Complexity) -> Go: >10, >15
                # & E. 嵌套深度 (Nesting) -> Go: >3, >5
                complexity = 1
                max_depth = 0
                
                # 生成结构指纹 (Duplication Check)
                fingerprint = []

                for child in ast.walk(node):
                    # 复杂度计算
                    if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.With, ast.AsyncWith)):
                        complexity += 1
                        fingerprint.append(type(child).__name__)
                    elif isinstance(child, ast.BoolOp):
                         complexity += len(child.values) - 1
                    
                    # 深度计算 (简单估算：节点层级)
                    # 准确计算需要递归 visitor，这里简化为 indent level 估算可能不准，
                    # 但在 AST walk 中很难直接拿 depth。
                    # 我们用一种 tricky 的方法：统计 col_offset
                    if hasattr(child, 'col_offset'):
                        depth = child.col_offset // 4 # 假设 4 空格缩进
                        max_depth = max(max_depth, depth)

                total_complexity += complexity
                
                if complexity > 15:
                    score -= 5
                    issues.append(f"🕸️ 结构极其纠结: 函数 '{func_name}' 复杂度 {complexity}")
                elif complexity > 10:
                    score -= 2
                    issues.append(f"🕸️ 结构纠结: 函数 '{func_name}' 复杂度 {complexity}")

                # 减去函数本身的缩进
                base_depth = node.col_offset // 4
                real_depth = max_depth - base_depth
                if real_depth > 5:
                    score -= 3
                    issues.append(f"🏗️ 嵌套过深: 函数 '{func_name}' 深度 {real_depth} 层")

                # F. 查重指纹记录
                if len(fingerprint) > 5: # 只有包含一定逻辑的才查重
                    sig = "-".join(fingerprint)
                    structure_fingerprints[sig].append(func_name)

        #  3. 重复代码检测 (Duplication) 
        for sig, funcs in structure_fingerprints.items():
            if len(funcs) > 1:
                score -= 5 * (len(funcs) - 1)
                issues.append(f"👯‍♀️ 疑似复制粘贴: {', '.join(funcs)} 逻辑结构完全一致")

        #  4. 类命名规范 
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Class 应该是 PascalCase
                if not re.match(r'^[A-Z][a-zA-Z0-9]*$', node.name):
                    score -= 1
                    issues.append(f"🎨 类名色泽不佳: '{node.name}' 建议使用 PascalCase")

        #  5. 错误处理检测 (Error Handling) 
        # Python 特有: try: ... except: pass
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # 检查 body 是否只有 pass 或 ...
                if len(node.body) == 1 and isinstance(node.body[0], (ast.Pass, ast.Expr)):
                    if isinstance(node.body[0], ast.Pass) or (isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and node.body[0].value.value is Ellipsis):
                         score -= 5
                         issues.append(f"🙈 掩耳盗铃: 第 {node.lineno} 行捕获了异常却未处理")

        final_score = max(0, min(100, score))
        return AnalysisResult(
            file_name=file_path.name,
            language="Python",
            score=final_score,
            rating=self.calculate_rating(final_score),
            issues=issues
        )