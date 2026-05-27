"""
Prompt 模板工具函数
用于处理和验证 Prompt 模板
"""

BUILTIN_PROMPTS = {
    "correct": """你是一个文本纠错助手。请对用户提供的文本进行以下处理：
1. 纠正所有语法错误和错别字
2. 修正标点符号使用错误
3. 保持原文风格和意思完全不变
4. 直接返回处理后的文本，不要添加任何解释或前缀""",

    "optimize": """你是一个文本编辑助手。请对用户提供的文本进行以下处理：
1. 纠正所有语法错误和错别字
2. 优化语句表达，使其更清晰流畅
3. 保持原意和核心信息不变
4. 直接返回处理后的文本，不要添加任何解释或前缀""",

    "expand": """你是一个专业的文本编辑助手。请对用户提供的文本进行以下处理：
1. 纠正所有语法错误和错别字
2. 优化语句表达，使其更清晰流畅和专业
3. 适当添加背景信息和细节，丰富内容
4. 保持原意和核心信息不变
5. 直接返回处理后的文本，不要添加任何解释或前缀""",

    "summarize": """你是一个文本总结助手。请对用户提供的文本进行精简：
1. 纠正语法错误
2. 提取核心要点
3. 删除冗余信息
4. 保持关键信息完整
5. 直接返回处理后的文本，不要添加任何解释或前缀"""
}


def get_prompt(name: str, prompts_config: dict) -> str:
    """
    获取 Prompt 模板

    Args:
        name: Prompt 名称
        prompts_config: 配置文件中的 prompts 字典

    Returns:
        Prompt 模板内容

    Raises:
        ValueError: Prompt 不存在
    """
    if name in prompts_config:
        return prompts_config[name]
    elif name in BUILTIN_PROMPTS:
        return BUILTIN_PROMPTS[name]
    else:
        raise ValueError(f"Prompt '{name}' 不存在")


def validate_prompt(prompt: str) -> bool:
    """
    验证 Prompt 是否有效

    Args:
        prompt: Prompt 内容

    Returns:
        是否有效
    """
    if not prompt or not prompt.strip():
        return False
    return True
