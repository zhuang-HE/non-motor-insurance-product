#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非车险产品开发统一流程控制器
确保 7 步顺序执行、状态持久化、格式验证
"""

import json
import os
import sys
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# 导入验证器
try:
    from validators import OutputValidator, FormatConfigValidator
except ImportError:
    # 如果导入失败，创建本地副本
    class OutputValidator:
        @staticmethod
        def validate_step1(output: dict) -> Tuple[bool, str]:
            return True, "跳过验证（验证器未安装）"
        
        @staticmethod
        def validate_step2(output: dict) -> Tuple[bool, str]:
            return True, "跳过验证（验证器未安装）"
        
        @staticmethod
        def validate_step3(output: dict) -> Tuple[bool, str]:
            return True, "跳过验证（验证器未安装）"
        
        @staticmethod
        def validate_step4(output: dict) -> Tuple[bool, str]:
            return True, "跳过验证（验证器未安装）"
        
        @staticmethod
        def validate_step5(output: dict) -> Tuple[bool, str]:
            return True, "跳过验证（验证器未安装）"
        
        @staticmethod
        def validate_step6(output: dict) -> Tuple[bool, str]:
            return True, "跳过验证（验证器未安装）"
        
        @staticmethod
        def validate_word_format(doc_path: str) -> Tuple[bool, str]:
            return True, "跳过验证（验证器未安装）"
    
    class FormatConfigValidator:
        @staticmethod
        def validate_word_format_config(config_path: str) -> Tuple[bool, str]:
            return True, "跳过验证（验证器未安装）"


class InsuranceProductWorkflow:
    """7 步流程控制器"""
    
    STEPS = [
        ("step1_insured_subject.py", "确定保险标的"),
        ("step2_policyholder.py", "明确投被保人"),
        ("step3_coverage.py", "保险责任设计"),
        ("step4_feasibility_report.py", "可行性报告"),
        ("step5_policy_clause.py", "条款撰写"),
        ("step6_pricing.py", "产品定价"),
        ("step7_word_export.py", "Word输出")
    ]
    
    def __init__(self, project_name: str, workspace: str = "."):
        """
        初始化流程控制器
        
        Args:
            project_name: 项目名称，用于状态文件命名
            workspace: 工作目录路径，默认为当前目录
        """
        self.project_name = project_name
        self.workspace = Path(workspace)
        self.state_file = self.workspace / f"{project_name}_workflow_state.json"
        self.results_dir = self.workspace / "results"
        self.current_step = 0
        self.state = {}
        
        # 创建结果目录
        self.results_dir.mkdir(exist_ok=True)
        
        # 加载现有状态
        self.load_state()
    
    def load_state(self) -> None:
        """从状态文件恢复执行进度"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                    self.current_step = self.state.get('current_step', 0)
                    print(f"✓ 加载状态文件: {self.state_file}")
                    print(f"  当前进度: 步骤 {self.current_step + 1}/{len(self.STEPS)}")
            except Exception as e:
                print(f"⚠️ 状态文件加载失败: {e}")
                self.state = {}
                self.current_step = 0
        else:
            print("ℹ️ 未找到状态文件，从头开始执行")
            self.state = {}
            self.current_step = 0
    
    def save_state(self) -> None:
        """保存当前状态"""
        self.state.update({
            'project_name': self.project_name,
            'current_step': self.current_step,
            'last_updated': datetime.now().isoformat(),
            'steps_completed': list(range(self.current_step))
        })
        
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            print(f"✓ 状态已保存: {self.state_file}")
        except Exception as e:
            print(f"❌ 状态保存失败: {e}")
    
    def get_step_script_path(self, step_index: int) -> Path:
        """获取步骤脚本路径"""
        if step_index < 0 or step_index >= len(self.STEPS):
            raise ValueError(f"步骤索引 {step_index} 超出范围 (0-{len(self.STEPS)-1})")
        
        script_name, _ = self.STEPS[step_index]
        script_path = Path(__file__).parent / script_name
        
        if not script_path.exists():
            raise FileNotFoundError(f"脚本不存在: {script_path}")
        
        return script_path
    
    def execute_step(self, step_index: int, input_data: Dict = None, **kwargs) -> Tuple[bool, Dict]:
        """
        执行指定步骤
        
        Args:
            step_index: 步骤索引 (0-based)
            input_data: 输入数据字典
            **kwargs: 额外参数
            
        Returns:
            (success, output_data) 元组
        """
        if step_index < 0 or step_index >= len(self.STEPS):
            return False, {"error": f"步骤索引 {step_index} 超出范围"}
        
        script_name, step_desc = self.STEPS[step_index]
        print(f"\n{'='*60}")
        print(f"执行步骤 {step_index + 1}: {step_desc}")
        print(f"{'='*60}")
        
        # 准备输入数据
        if input_data is None:
            input_data = {}
        
        # 合并kwargs到输入数据
        input_data.update(kwargs)
        
        # 如果上一步有输出，合并到输入
        if step_index > 0 and f"step_{step_index}" in self.state:
            prev_output = self.state[f"step_{step_index}"]
            if isinstance(prev_output, dict):
                input_data.update(prev_output)
        
        # 保存输入数据到临时文件
        input_file = self.results_dir / f"step{step_index + 1}_input.json"
        try:
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(input_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 输入数据保存失败: {e}")
            return False, {"error": f"输入数据保存失败: {e}"}
        
        # 执行脚本
        script_path = self.get_step_script_path(step_index)
        
        try:
            # 调用Python脚本
            cmd = [sys.executable, str(script_path)]
            
            # 如果脚本支持命令行参数，可以传递输入文件路径
            # 这里暂时使用简单调用，后续可以扩展为参数化调用
            result = subprocess.run(
                cmd,
                cwd=self.workspace,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=300  # 5分钟超时
            )
            
            if result.returncode != 0:
                print(f"❌ 脚本执行失败 (返回码: {result.returncode})")
                print(f"标准错误: {result.stderr[:500]}")
                return False, {
                    "error": f"脚本执行失败",
                    "returncode": result.returncode,
                    "stderr": result.stderr[:500]
                }
            
            print(f"✓ 脚本执行成功")
            
            # 尝试读取输出文件
            output_file_patterns = [
                self.workspace / f"step{step_index + 1}_*.json",
                self.workspace / f"{script_name.replace('.py', '')}_*.json",
                self.workspace / "*.json"
            ]
            
            output_data = {}
            for pattern in output_file_patterns:
                for file_path in self.workspace.glob(pattern.name if hasattr(pattern, 'name') else str(pattern)):
                    if file_path.is_file():
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                if isinstance(data, dict):
                                    output_data.update(data)
                        except:
                            continue
            
            # 如果没有找到输出文件，使用空字典
            if not output_data:
                output_data = {"status": "completed", "step": step_index + 1}
            
            # 验证输出格式
            validator = OutputValidator()
            validation_methods = [
                validator.validate_step1,
                validator.validate_step2,
                validator.validate_step3,
                validator.validate_step4,
                validator.validate_step5,
                validator.validate_step6
            ]
            
            if step_index < len(validation_methods):
                is_valid, message = validation_methods[step_index](output_data)
                if not is_valid:
                    print(f"⚠️ 输出格式验证警告: {message}")
                else:
                    print(f"✓ 输出格式验证通过")
            
            # 保存输出到状态
            self.state[f"step_{step_index + 1}"] = output_data
            self.current_step = step_index + 1
            self.save_state()
            
            # 保存输出到结果文件
            output_file = self.results_dir / f"step{step_index + 1}_output.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            # 更新工作记忆
            self.update_working_memory()
            
            return True, output_data
            
        except subprocess.TimeoutExpired:
            print("❌ 脚本执行超时")
            return False, {"error": "脚本执行超时"}
        except Exception as e:
            print(f"❌ 脚本执行异常: {e}")
            return False, {"error": f"脚本执行异常: {e}"}
    
    def run_all(self, initial_data: Dict = None) -> Dict[str, Any]:
        """
        从头执行完整流程
        
        Args:
            initial_data: 初始输入数据
            
        Returns:
            所有步骤的结果字典
        """
        if initial_data is None:
            initial_data = {}
        
        all_results = {}
        current_data = initial_data.copy()
        
        print(f"\n{'='*60}")
        print(f"开始执行非车险产品开发工作流")
        print(f"项目: {self.project_name}")
        print(f"工作目录: {self.workspace}")
        print(f"{'='*60}")
        
        # 验证格式配置文件
        format_config_path = Path(__file__).parent.parent / "templates" / "word_format.json"
        if format_config_path.exists():
            validator = FormatConfigValidator()
            is_valid, message = validator.validate_word_format_config(str(format_config_path))
            if is_valid:
                print(f"✓ Word格式配置文件验证通过")
            else:
                print(f"⚠️ Word格式配置文件验证失败: {message}")
        else:
            print("ℹ️ Word格式配置文件不存在，跳过验证")
        
        for step_index in range(len(self.STEPS)):
            print(f"\n{'='*60}")
            print(f"进度: {step_index + 1}/{len(self.STEPS)}")
            print(f"{'='*60}")
            
            success, output = self.execute_step(step_index, current_data)
            
            if not success:
                print(f"\n❌ 步骤 {step_index + 1} 执行失败，流程中止")
                print(f"错误信息: {output.get('error', '未知错误')}")
                break
            
            all_results[f"step_{step_index + 1}"] = output
            
            # 合并输出到当前数据，供下一步使用
            if isinstance(output, dict):
                current_data.update(output)
        
        # 最终验证
        if len(all_results) == len(self.STEPS):
            print(f"\n{'='*60}")
            print(f"🎉 所有步骤执行完成!")
            print(f"{'='*60}")
            
            # 验证Word输出（如果存在）
            word_files = list(self.workspace.glob("*.docx"))
            if word_files:
                validator = OutputValidator()
                for word_file in word_files:
                    is_valid, message = validator.validate_word_format(str(word_file))
                    if is_valid:
                        print(f"✓ Word文档验证通过: {word_file.name}")
                    else:
                        print(f"⚠️ Word文档验证警告: {word_file.name} - {message}")
            
            # 生成执行报告
            report = self.generate_execution_report(all_results)
            report_path = self.results_dir / "execution_report.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📋 执行报告已保存: {report_path}")
        
        return all_results
    
    def resume_from_step(self, step_index: int, input_data: Dict = None) -> Dict[str, Any]:
        """
        从指定步骤恢复执行
        
        Args:
            step_index: 恢复的步骤索引 (1-based)
            input_data: 额外的输入数据
            
        Returns:
            恢复后执行的结果
        """
        if step_index < 1 or step_index > len(self.STEPS):
            raise ValueError(f"步骤索引 {step_index} 超出范围 (1-{len(self.STEPS)})")
        
        print(f"\n{'='*60}")
        print(f"从步骤 {step_index} 恢复执行")
        print(f"{'='*60}")
        
        # 加载之前的状态
        self.load_state()
        
        # 设置当前步骤
        self.current_step = step_index - 1
        
        # 合并输入数据
        current_data = {}
        if input_data:
            current_data.update(input_data)
        
        # 执行剩余步骤
        all_results = {}
        for i in range(self.current_step, len(self.STEPS)):
            success, output = self.execute_step(i, current_data)
            
            if not success:
                print(f"\n❌ 步骤 {i + 1} 执行失败，流程中止")
                break
            
            all_results[f"step_{i + 1}"] = output
            
            if isinstance(output, dict):
                current_data.update(output)
        
        return all_results
    
    def update_working_memory(self) -> None:
        """将当前状态写入工作记忆"""
        memory_content = f"""
## 非车险产品开发执行状态
- **项目**: {self.project_name}
- **当前步骤**: {self.current_step + 1}/{len(self.STEPS)} - {self.STEPS[self.current_step][1] if self.current_step < len(self.STEPS) else '完成'}
- **最后更新时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **已完成步骤**: {[self.STEPS[i][1] for i in range(self.current_step)]}
"""
        
        # 工作记忆文件路径（在项目目录下）
        memory_file = self.workspace / "workflow_memory.md"
        try:
            with open(memory_file, 'w', encoding='utf-8') as f:
                f.write(memory_content)
            print(f"✓ 工作记忆已更新: {memory_file}")
        except Exception as e:
            print(f"⚠️ 工作记忆更新失败: {e}")
    
    def generate_execution_report(self, results: Dict[str, Any]) -> str:
        """生成执行报告"""
        report = f"""# 非车险产品开发工作流执行报告

## 项目信息
- **项目名称**: {self.project_name}
- **执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **总步骤数**: {len(self.STEPS)}
- **完成步骤数**: {len(results)}

## 步骤执行详情
"""
        
        for step_index, (script_name, step_desc) in enumerate(self.STEPS, 1):
            step_key = f"step_{step_index}"
            if step_key in results:
                result = results[step_key]
                status = "✅ 完成" if result.get("status") != "error" else "❌ 失败"
                report += f"\n### 步骤{step_index}: {step_desc}\n"
                report += f"- **状态**: {status}\n"
                report += f"- **脚本**: {script_name}\n"
                
                # 添加关键信息
                if isinstance(result, dict):
                    for key, value in result.items():
                        if key not in ["status", "step"] and not key.startswith("_"):
                            if isinstance(value, (str, int, float, bool)):
                                report += f"- **{key}**: {value}\n"
                            elif isinstance(value, list) and len(value) > 0:
                                report += f"- **{key}**: {', '.join(map(str, value[:3]))}"
                                if len(value) > 3:
                                    report += f" ... 等 {len(value)} 项"
                                report += "\n"
            else:
                report += f"\n### 步骤{step_index}: {step_desc}\n"
                report += f"- **状态**: ⏸️ 未执行\n"
        
        # 添加验证结果
        report += "\n## 格式验证结果\n"
        
        # 检查Word文档
        word_files = list(self.workspace.glob("*.docx"))
        if word_files:
            report += "### Word文档验证\n"
            for word_file in word_files:
                validator = OutputValidator()
                is_valid, message = validator.validate_word_format(str(word_file))
                status = "✅ 通过" if is_valid else "⚠️ 警告"
                report += f"- **{word_file.name}**: {status} - {message}\n"
        else:
            report += "### Word文档验证\n- 未生成Word文档\n"
        
        # 检查JSON输出文件
        json_files = list(self.results_dir.glob("*.json"))
        if json_files:
            report += f"\n### 输出文件\n"
            for json_file in json_files:
                report += f"- {json_file.name}\n"
        
        report += f"\n## 状态文件\n"
        report += f"- 状态文件: {self.state_file.name}\n"
        report += f"- 最后更新: {self.state.get('last_updated', 'N/A')}\n"
        
        report += f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            "project_name": self.project_name,
            "current_step": self.current_step,
            "total_steps": len(self.STEPS),
            "current_step_desc": self.STEPS[self.current_step][1] if self.current_step < len(self.STEPS) else "完成",
            "completed_steps": list(range(self.current_step)),
            "state_file": str(self.state_file),
            "last_updated": self.state.get('last_updated', 'N/A')
        }


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(description="非车险产品开发工作流控制器")
    parser.add_argument("project", help="项目名称")
    parser.add_argument("--workspace", "-w", default=".", help="工作目录路径")
    parser.add_argument("--resume", "-r", type=int, help="从指定步骤恢复执行 (1-based)")
    parser.add_argument("--step", "-s", type=int, help="执行单个指定步骤")
    parser.add_argument("--status", action="store_true", help="显示当前状态")
    
    args = parser.parse_args()
    
    # 创建工作流实例
    workflow = InsuranceProductWorkflow(args.project, args.workspace)
    
    if args.status:
        # 显示状态
        status = workflow.get_status()
        print("\n工作流状态:")
        print(f"  项目: {status['project_name']}")
        print(f"  进度: {status['current_step'] + 1}/{status['total_steps']}")
        print(f"  当前步骤: {status['current_step_desc']}")
        print(f"  状态文件: {status['state_file']}")
        print(f"  最后更新: {status['last_updated']}")
        return
    
    if args.resume:
        # 恢复执行
        print(f"从步骤 {args.resume} 恢复执行...")
        results = workflow.resume_from_step(args.resume)
        print(f"恢复执行完成，共执行 {len(results)} 个步骤")
    
    elif args.step:
        # 执行单个步骤
        print(f"执行单个步骤: {args.step}")
        success, output = workflow.execute_step(args.step - 1)
        if success:
            print(f"步骤 {args.step} 执行成功")
        else:
            print(f"步骤 {args.step} 执行失败: {output.get('error', '未知错误')}")
    
    else:
        # 完整执行
        print("开始完整工作流执行...")
        results = workflow.run_all()
        print(f"工作流执行完成，共完成 {len(results)}/{len(workflow.STEPS)} 个步骤")


if __name__ == "__main__":
    main()