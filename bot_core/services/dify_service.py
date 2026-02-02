"""
Tezbarakat Telegram Bot - Dify AI 服务集成
支持多轮对话获客工作流
"""

import httpx
import json
import re
from typing import Optional, Dict, Any, Tuple
from loguru import logger

from config import bot_settings


class DifyService:
    """Dify AI 服务类"""
    
    def __init__(self):
        self._api_url = bot_settings.dify_api_url
        self._api_key = bot_settings.dify_api_key
        self._workflow_id = bot_settings.dify_workflow_id
        self._knowledge_workflow_id = bot_settings.dify_knowledge_workflow_id
        self._confidence_threshold = bot_settings.dify_confidence_threshold
    
    def reload_config(self):
        """重新加载配置"""
        self._api_url = bot_settings.dify_api_url
        self._api_key = bot_settings.dify_api_key
        self._workflow_id = bot_settings.dify_workflow_id
        self._knowledge_workflow_id = bot_settings.dify_knowledge_workflow_id
        self._confidence_threshold = bot_settings.dify_confidence_threshold
    
    def _get_headers(self) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json"
        }
    
    def _parse_stage_analysis(self, text: str) -> Dict[str, Any]:
        """
        解析阶段分析结果
        从 LLM 输出中提取 JSON
        """
        try:
            # 尝试直接解析
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # 尝试从文本中提取 JSON
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # 默认返回
        return {
            "user_sentiment": "neutral",
            "should_continue": False,
            "next_stage": 6,
            "reasoning": "无法解析分析结果"
        }
    
    async def run_multi_round_workflow(
        self,
        user_message: str,
        user_id: int,
        current_stage: int = 0,
        conversation_history: str = "",
        original_intent: str = "",
        user_language: str = "ru"
    ) -> Dict[str, Any]:
        """
        运行多轮对话获客工作流
        
        参数:
        - user_message: 用户最新消息
        - user_id: 用户 ID
        - current_stage: 当前对话阶段 (0-6)
        - conversation_history: 对话历史
        - original_intent: 原始意图（首次触发的关键词/意图）
        - user_language: 用户语言 (ru/tj/mixed)
        
        返回:
        {
            "should_continue": bool,      # 是否继续对话
            "reply_text": str,            # 回复文本
            "next_stage": int,            # 下一阶段
            "user_sentiment": str,        # 用户情绪 (positive/neutral/negative)
            "stage_analysis": dict,       # 阶段分析详情
        }
        """
        if not self._api_key or not self._workflow_id:
            logger.warning("Dify API 未配置")
            return self._default_multi_round_response()
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 调用 Dify 多轮对话工作流
                response = await client.post(
                    f"{self._api_url}/workflows/run",
                    headers=self._get_headers(),
                    json={
                        "inputs": {
                            "user_message": user_message,
                            "current_stage": str(current_stage),
                            "conversation_history": conversation_history or "",
                            "original_intent": original_intent or "",
                            "user_language": user_language or "ru"
                        },
                        "response_mode": "blocking",
                        "user": f"tg_user_{user_id}"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Dify API 调用失败: {response.status_code} - {response.text}")
                    return self._default_multi_round_response()
                
                result = response.json()
                
                # 解析工作流输出
                outputs = result.get("data", {}).get("outputs", {})
                
                # 获取回复文本
                reply_text = outputs.get("reply_text", "")
                
                # 获取阶段分析结果
                stage_analysis_text = outputs.get("stage_analysis", "{}")
                stage_analysis = self._parse_stage_analysis(stage_analysis_text)
                
                should_continue = stage_analysis.get("should_continue", False)
                next_stage = stage_analysis.get("next_stage", current_stage + 1)
                user_sentiment = stage_analysis.get("user_sentiment", "neutral")
                
                # 如果工作流返回了 end_reason（结束对话分支），则不继续
                if outputs.get("end_reason"):
                    should_continue = False
                    end_analysis = self._parse_stage_analysis(outputs.get("end_reason", "{}"))
                    next_stage = end_analysis.get("next_stage", 6)
                    user_sentiment = end_analysis.get("user_sentiment", "negative")
                
                logger.info(f"多轮对话工作流结果: should_continue={should_continue}, next_stage={next_stage}, sentiment={user_sentiment}")
                
                return {
                    "should_continue": should_continue,
                    "reply_text": reply_text,
                    "next_stage": next_stage,
                    "user_sentiment": user_sentiment,
                    "stage_analysis": stage_analysis,
                    "workflow_run_id": result.get("workflow_run_id")
                }
                
        except httpx.TimeoutException:
            logger.error("Dify API 调用超时")
            return self._default_multi_round_response()
        except Exception as e:
            logger.error(f"Dify API 调用异常: {e}")
            return self._default_multi_round_response()
    
    async def analyze_intent(
        self,
        message_text: str,
        user_id: int,
        username: Optional[str] = None,
        current_stage: int = 0,
        conversation_history: str = "",
        original_intent: str = "",
        user_language: str = "ru"
    ) -> Dict[str, Any]:
        """
        分析消息意图（兼容旧接口，内部调用多轮对话工作流）
        
        返回:
        {
            "is_opportunity": bool,  # 是否为商机
            "confidence": float,     # 置信度
            "group_reply": str,      # 群内回复文本（首次触发时使用）
            "private_reply": str,    # 私信回复文本
            "category": str,         # 意图分类
            "next_stage": int,       # 下一阶段
            "should_continue": bool  # 是否继续对话
        }
        """
        # 调用多轮对话工作流
        result = await self.run_multi_round_workflow(
            user_message=message_text,
            user_id=user_id,
            current_stage=current_stage,
            conversation_history=conversation_history,
            original_intent=original_intent,
            user_language=user_language
        )
        
        # 转换为旧接口格式
        return {
            "is_opportunity": result["should_continue"],
            "confidence": 1.0 if result["should_continue"] else 0.0,
            "group_reply": result["reply_text"] if current_stage == 0 else "",
            "private_reply": result["reply_text"],
            "category": result["user_sentiment"],
            "next_stage": result["next_stage"],
            "should_continue": result["should_continue"],
            "stage_analysis": result.get("stage_analysis", {}),
            "workflow_run_id": result.get("workflow_run_id")
        }
    
    async def chat_with_knowledge(
        self,
        message_text: str,
        user_id: int,
        conversation_id: Optional[str] = None,
        current_stage: int = 1,
        conversation_history: str = "",
        original_intent: str = "",
        user_language: str = "ru"
    ) -> Tuple[str, Optional[str], Dict[str, Any]]:
        """
        使用多轮对话工作流进行私信对话
        
        返回: (回复文本, 对话ID, 工作流结果)
        """
        # 调用多轮对话工作流
        result = await self.run_multi_round_workflow(
            user_message=message_text,
            user_id=user_id,
            current_stage=current_stage,
            conversation_history=conversation_history,
            original_intent=original_intent,
            user_language=user_language
        )
        
        reply_text = result.get("reply_text", "")
        
        if not reply_text and not result.get("should_continue", False):
            # 对话结束，不回复
            return "", conversation_id, result
        
        return reply_text, conversation_id, result
    
    async def test_connection(self) -> Tuple[bool, str]:
        """测试 Dify 连接"""
        if not self._api_key:
            return False, "API 密钥未配置"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 尝试获取应用信息
                response = await client.get(
                    f"{self._api_url}/parameters",
                    headers=self._get_headers()
                )
                
                if response.status_code == 200:
                    return True, "连接成功"
                elif response.status_code == 401:
                    return False, "API 密钥无效"
                else:
                    return False, f"连接失败: HTTP {response.status_code}"
                    
        except httpx.ConnectError:
            return False, "无法连接到 Dify 服务"
        except httpx.TimeoutException:
            return False, "连接超时"
        except Exception as e:
            return False, f"连接异常: {str(e)}"
    
    def _default_response(self) -> Dict[str, Any]:
        """返回默认响应（旧接口）"""
        return {
            "is_opportunity": False,
            "confidence": 0,
            "group_reply": "",
            "private_reply": "",
            "category": "unknown"
        }
    
    def _default_multi_round_response(self) -> Dict[str, Any]:
        """返回默认的多轮对话响应"""
        return {
            "should_continue": False,
            "reply_text": "",
            "next_stage": 6,
            "user_sentiment": "unknown",
            "stage_analysis": {}
        }


# 全局 Dify 服务实例
dify_service = DifyService()
