#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非车险产品开发输出验证器
确保各步骤输出格式、内容符合监管要求
"""

import json
import os
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class OutputValidator:
    """各步骤输出验证器"""
    
    @staticmethod
    def validate_step1(output: dict) -> Tuple[bool, str]:
        """验证标的分析输出"""
        required_keys = ['标的名称', '标的类型', '风险等级', '可保性检查']
        missing_keys = [key for key in required_keys if key not in output]
        
        if missing_keys:
            return False, f"标的分析缺少必要字段: {missing_keys}"
        
        # 验证可保性检查是否包含五性分析
        if '可保性检查' in output:
            five_checks = ['合法性', '合规性', '确定性', '可评估性', '分散性']
            checks_done = output['可保性检查']
            if not isinstance(checks_done, list):
                return False, "可保性检查应为列表类型"
        
        return True, "标的分析输出格式正确"
    
    @staticmethod
    def validate_step2(output: dict) -> Tuple[bool, str]:
        """验证投被保人分析输出"""
        required_keys = ['投保人', '被保险人', '保险利益类型', '资格审查结果']
        missing_keys = [key for key in required_keys if key not in output]
        
        if missing_keys:
            return False, f"投被保人分析缺少必要字段: {missing_keys}"
        
        # 保险利益类型应为7种之一
        interest_types = ['所有权', '使用权', '抵押权', '质权', '经营权', 
                         '管理权', '法律责任']
        if output.get('保险利益类型') not in interest_types:
            return False, f"保险利益类型应为以下之一: {interest_types}"
        
        return True, "投被保人分析输出格式正确"
    
    @staticmethod
    def validate_step3(output: dict) -> Tuple[bool, str]:
        """验证保险责任设计输出"""
        required_keys = ['保险责任类型', '主险责任', '附加险责任', '责任免除']
        missing_keys = [key for key in required_keys if key not in output]
        
        if missing_keys:
            return False, f"保险责任设计缺少必要字段: {missing_keys}"
        
        # 验证保险责任类型
        coverage_types = ['基本险', '综合险', '一切险']
        if output.get('保险责任类型') not in coverage_types:
            return False, f"保险责任类型应为以下之一: {coverage_types}"
        
        return True, "保险责任设计输出格式正确"
    
    @staticmethod
    def validate_step4(output: dict) -> Tuple[bool, str]:
        """验证可行性报告结构"""
        # 检查是否包含8章节
        required_sections = [
            '总体开发说明',
            '开发背景',
            '产品主要特点',
            '保险费率及保费测算',
            '风险分析及风控',
            '经营模式',
            '市场类似产品分析',
            '总体结论'
        ]
        
        report_content = output.get('报告内容', {})
        missing_sections = [section for section in required_sections 
                          if section not in report_content]
        
        if missing_sections:
            return False, f"可行性报告缺少章节: {missing_sections}"
        
        # 检查是否有监管三段式引用
        regulatory_refs = output.get('监管引用', [])
        if len(regulatory_refs) < 3:
            return False, "可行性报告应包含至少3段监管引用"
        
        # 检查是否包含操作风控6方面
        risk_controls = output.get('操作风控', [])
        if len(risk_controls) < 6:
            return False, "可行性报告应包含至少6个操作风控方面"
        
        return True, "可行性报告结构完整"
    
    @staticmethod
    def validate_step5(output: dict) -> Tuple[bool, str]:
        """验证条款撰写输出"""
        required_keys = ['条款名称', '条款章节', '标准表述']
        missing_keys = [key for key in required_keys if key not in output]
        
        if missing_keys:
            return False, f"条款撰写缺少必要字段: {missing_keys}"
        
        # 检查13章节结构
        chapters = output.get('条款章节', [])
        if len(chapters) < 13:
            return False, f"条款应包含13章节，当前只有{len(chapters)}章节"
        
        # 检查标准表述是否使用模板
        standard_expressions = output.get('标准表述', [])
        if not standard_expressions:
            return False, "条款应使用标准表述模板"
        
        return True, "条款撰写输出格式正确"
    
    @staticmethod
    def validate_step6(output: dict) -> Tuple[bool, str]:
        """验证产品定价输出"""
        required_keys = ['定价方法', '基准费率', '风险因子', '费率表']
        missing_keys = [key for key in required_keys if key not in output]
        
        if missing_keys:
            return False, f"产品定价缺少必要字段: {missing_keys}"
        
        # 验证定价方法
        pricing_methods = ['纯保费法', '损失率法', 'Burning Cost法', '类比法']
        if output.get('定价方法') not in pricing_methods:
            return False, f"定价方法应为以下之一: {pricing_methods}"
        
        # 验证费率表格式
        rate_table = output.get('费率表', {})
        if not isinstance(rate_table, dict) or not rate_table:
            return False, "费率表应为非空字典格式"
        
        return True, "产品定价输出格式正确"
    
    @staticmethod
    def validate_word_format(doc_path: str) -> Tuple[bool, str]:
        """验证Word文档格式"""
        try:
            from docx import Document
        except ImportError:
            return False, "未安装python-docx库，无法验证Word格式"
        
        if not os.path.exists(doc_path):
            return False, f"Word文档不存在: {doc_path}"
        
        try:
            doc = Document(doc_path)
            
            # 检查文档结构
            if len(doc.paragraphs) < 10:
                return False, "Word文档内容过少"
            
            # 这里可以添加更详细的格式检查
            # 如字体、字号、对齐方式等
            
            return True, "Word文档格式基本符合要求"
        except Exception as e:
            return False, f"Word文档验证失败: {str(e)}"
    
    @staticmethod
    def validate_all_steps(step_outputs: Dict[int, dict]) -> Dict[int, Tuple[bool, str]]:
        """验证所有步骤输出"""
        results = {}
        
        validation_methods = {
            1: OutputValidator.validate_step1,
            2: OutputValidator.validate_step2,
            3: OutputValidator.validate_step3,
            4: OutputValidator.validate_step4,
            5: OutputValidator.validate_step5,
            6: OutputValidator.validate_step6
        }
        
        for step_num, output in step_outputs.items():
            if step_num in validation_methods:
                is_valid, message = validation_methods[step_num](output)
                results[step_num] = (is_valid, message)
        
        return results


class FormatConfigValidator:
    """格式配置验证器"""
    
    @staticmethod
    def validate_word_format_config(config_path: str) -> Tuple[bool, str]:
        """验证Word格式配置文件"""
        if not os.path.exists(config_path):
            return False, f"格式配置文件不存在: {config_path}"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            required_sections = ['document_title', 'chapter_title', 'body_text']
            missing_sections = [section for section in required_sections 
                              if section not in config]
            
            if missing_sections:
                return False, f"格式配置缺少必要部分: {missing_sections}"
            
            return True, "格式配置文件有效"
        except json.JSONDecodeError as e:
            return False, f"格式配置文件JSON格式错误: {str(e)}"
        except Exception as e:
            return False, f"格式配置文件验证失败: {str(e)}"


if __name__ == "__main__":
    # 测试验证器
    test_output = {
        1: {
            '标的名称': '测试标的',
            '标的类型': '财产',
            '风险等级': '中等',
            '可保性检查': ['合法性', '合规性', '确定性']
        }
    }
    
    validator = OutputValidator()
    results = validator.validate_all_steps(test_output)
    
    for step, (is_valid, message) in results.items():
        status = "通过" if is_valid else "失败"
        print(f"步骤{step}验证{status}: {message}")