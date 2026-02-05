import datetime
from typing import List

class MarkdownReporter:
    def generate(self, results: List, file_tree_str: str, output_path: str = "CODE_RATING.md"):
        """
        生成代码品鉴报告
        """
        if not results:
            print("🍷 本次采摘未发现符合年份的代码果实 (No Code Found)。")
            return

        # 1. 计算总体指标
        total_score = sum(r.score for r in results)
        avg_score = total_score / len(results) if results else 0
        overall_rank = self._get_rank(avg_score)
        flavor_text = self._get_flavor_text(avg_score)
        
        # 按分数从低到高排序 
        sorted_results = sorted(results, key=lambda x: x.score)

        # 2. 构建 Markdown 内容
        md = []
        
        #  头部信息 
        md.append(f"# 🍷 Code Sommelier 品鉴报告")
        md.append(f"> **生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"")
        md.append(f"## 1. 庄园综合评级 (Overall Assessment)")
        md.append(f"- **综合评分**: `{avg_score:.2f} / 100`")
        md.append(f"- **品质等级**: **{overall_rank}**")
        md.append(f"- **品鉴结论**: *{flavor_text}*")
        md.append(f"- **样本数量**: {len(results)} 个文件")
        md.append(f"")

        #  项目结构
        md.append(f"## 2. 葡萄园地图 (Vineyard Map)")
        md.append(f"```text")
        md.append(file_tree_str if file_tree_str else "(空目录)")
        md.append(f"```")
        md.append(f"")

        #  详细评分表 
        md.append(f"## 3. 详细风味分析 (Detailed Notes)")
        md.append(f"| 文件名 | 语言 | 得分 | 等级 | 状态 |")
        md.append(f"| :--- | :---: | :---: | :---: | :---: |")
        
        for res in sorted_results:
            status_icon = self._get_status_icon(res.score)
            display_name = res.file_name
            # 提取 S/A/B 等级字符
            short_rank = self._get_rank(res.score).split(' ')[0]
            
            md.append(f"| `{display_name}` | {res.language} | {res.score:.1f} | **{short_rank}** | {status_icon} |")
        
        md.append(f"")

        # 改进建议
        md.append(f"## 4. 酿造师建议 (Winemaker's Suggestions)")
        
        has_issues = False
        for res in sorted_results:
            if res.issues:
                has_issues = True
                rank_str = self._get_rank(res.score).split(' ')[0]
                md.append(f"### 📄 `{res.file_name}` (等级: {rank_str})")
                for issue in res.issues:
                    # 自动添加分类图标
                    icon = self._get_issue_category_icon(issue)
                    md.append(f"- {icon} {issue}")
                md.append(f"")
        
        if not has_issues:
            md.append(f"✨ 完美年份！这批代码口感纯净，结构平衡，无需额外的修饰。")

        # 底部建议 
        md.append(f"---")
        md.append(f"**优化指南**: {self._get_advice(avg_score)}")

        # 3. 写入文件
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md))
            print(f"✨ 报告已装瓶: {output_path} (得分: {avg_score:.2f})")
        except IOError as e:
            print(f"❌ 报告导出失败: {e}")

    def _get_rank(self, score: float) -> str:
        """S-D 等级定义 (优雅版)"""
        if score >= 95: return "S (Grand Cru / 特级园)"
        if score >= 85: return "A (Premier Cru / 一级园)"
        if score >= 75: return "B (Village / 村庄级)"
        if score >= 60: return "C (Regional / 大区级)"
        return "D (Vin de Table / 日常餐酒)"

    def _get_flavor_text(self, score: float) -> str:
        """根据分数生成的优雅评语"""
        if score >= 95: return "如同精密的瑞士钟表，逻辑韵律令人沉醉，结构无懈可击。"
        if score >= 85: return "结构清晰，口感顺滑，代码风格统一，具备极佳的陈年潜力。"
        if score >= 75: return "整体骨架健康，但部分细节略显粗糙，建议适度醒酒（重构）以释放潜力。"
        if score >= 60: return "虽然功能完整，但逻辑结构略显松散，单宁（复杂度）过高，入口干涩。"
        return "代码结构缺乏协调性，杂质较多，难以维护，建议进行深度的过滤与重构。"

    def _get_advice(self, score: float) -> str:
        """根据分数段给出总体建议"""
        if score >= 85:
            return "当前状态极佳。建议保持当前的编码规范，并作为团队的范本（Best Practice）。"
        elif score >= 60:
            return "建议重点关注复杂度过高的函数，通过拆分模块来降低耦合度，提升代码的可读性。"
        else:
            return "急需进行技术债务偿还。建议暂停新功能开发，优先对核心逻辑进行重构和文档补充。"

    def _get_status_icon(self, score: float) -> str:
        if score >= 90: return "✅"
        if score >= 75: return "🆗"
        if score >= 60: return "⚠️"
        return "🛑"

    def _get_issue_category_icon(self, issue_text: str) -> str:
        """根据问题文本自动匹配图标"""
        text = issue_text.lower()
        if any(x in text for x in ["复杂度", "complexity", "纠结", "迷宫", "逻辑"]):
            return "🔄" # 复杂度
        if any(x in text for x in ["命名", "naming", "snake_case", "pascal", "色泽"]):
            return "🏷️"  # 命名
        if any(x in text for x in ["注释", "comment", "docstring", "余味"]):
            return "📝" # 注释
        if any(x in text for x in ["长", "length", "臃肿", "酒体", "拆分"]):
            return "📏" # 长度
        if any(x in text for x in ["重复", "duplication", "copy", "paste", "粘贴"]):
            return "👯‍♀️" # 重复
        if any(x in text for x in ["嵌套", "nest", "depth", "深"]):
            return "🏗️" # 结构
        if any(x in text for x in ["error", "except", "try", "异常", "错误"]):
            return "🛡️" # 错误处理
        return "⚠️"    # 其他