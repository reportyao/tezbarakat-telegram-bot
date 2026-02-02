"""
Tezbarakat Telegram Bot - Dify AI 服务集成
"""

import httpx
import json
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
    
    async def analyze_intent(
        self,
        message_text: str,
        user_id: int,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析消息意图
        
        返回:
        {
            "is_opportunity": bool,  # 是否为商机
            "confidence": float,     # 置信度
            "group_reply": str,      # 群内回复文本
            "private_reply": str,    # 私信回复文本
            "category": str          # 意图分类
        }
        """
        if not self._api_key or not self._workflow_id:
            logger.warning("Dify API 未配置")
            return {
                "is_opportunity": False,
                "confidence": 0,
                "group_reply": "",
                "private_reply": "",
                "category": "unknown"
            }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # 调用 Dify 工作流
                response = await client.post(
                    f"{self._api_url}/workflows/run",
                    headers=self._get_headers(),
                    json={
                        "inputs": {
                            "user_message": message_text,
                            "user_id": str(user_id),
                            "username": username or "",
                            "current_stage": "initial"
                        },
                        "response_mode": "blocking",
                        "user": f"tg_user_{user_id}"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Dify API 调用失败: {response.status_code} - {response.text}")
                    return self._default_response()
                
                result = response.json()
                
                # 解析工作流输出
                outputs = result.get("data", {}).get("outputs", {})
                
                is_opportunity = outputs.get("is_opportunity", False)
                confidence = float(outputs.get("confidence", 0))
                
                # 检查置信度阈值
                if confidence < self._confidence_threshold:
                    is_opportunity = False
                
                return {
                    "is_opportunity": is_opportunity,
                    "confidence": confidence,
                    "group_reply": outputs.get("group_reply", ""),
                    "private_reply": outputs.get("private_reply", ""),
                    "category": outputs.get("category", "unknown"),
                    "workflow_run_id": result.get("workflow_run_id")
                }
                
        except httpx.TimeoutException:
            logger.error("Dify API 调用超时")
            return self._default_response()
        except Exception as e:
            logger.error(f"Dify API 调用异常: {e}")
            return self._default_response()
    
    async def chat_with_knowledge(
        self,
        message_text: str,
        user_id: int,
        conversation_id: Optional[str] = None
    ) -> Tuple[str, Optional[str]]:
        """
        使用知识库进行对话
        
        返回: (回复文本, 对话ID)
        """
        if not self._api_key or not self._knowledge_workflow_id:
            logger.warning("Dify 知识库 API 未配置")
            return "抱歉，我暂时无法回答您的问题。", None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                payload = {
                    "inputs": {
                        "user_message": message_text
                    },
                    "query": message_text,
                    "response_mode": "blocking",
                    "user": f"tg_user_{user_id}"
                }
                
                # 如果有对话 ID，添加到请求中
                if conversation_id:
                    payload["conversation_id"] = conversation_id
                
                response = await client.post(
                    f"{self._api_url}/chat-messages",
                    headers=self._get_headers(),
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Dify 知识库 API 调用失败: {response.status_code}")
                    return "抱歉，我暂时无法回答您的问题。", conversation_id
                
                result = response.json()
                
                answer = result.get("answer", "")
                new_conversation_id = result.get("conversation_id", conversation_id)
                
                return answer, new_conversation_id
                
        except httpx.TimeoutException:
            logger.error("Dify 知识库 API 调用超时")
            return "抱歉，响应超时，请稍后再试。", conversation_id
        except Exception as e:
            logger.error(f"Dify 知识库 API 调用异常: {e}")
            return "抱歉，发生了错误，请稍后再试。", conversation_id
    
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
        """返回默认响应"""
        return {
            "is_opportunity": False,
            "confidence": 0,
            "group_reply": "",
            "private_reply": "",
            "category": "unknown"
        }


# 全局 Dify 服务实例
dify_service = DifyService()
