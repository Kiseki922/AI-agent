import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Set
from collections import deque

# 常量
MAX_SHORT_TERM_MEMORY = 10
MAX_LONG_TERM_MEMORY = 50
REFLECTION_INTERVAL = 10  # 每 10 個動作後觸發反思
API_URL = "http://127.0.0.1:1234/v1/chat/completions"

class Memory:
    """記憶模組，用於存儲和檢索代理人的經驗。"""
    
    def __init__(self):
        # 短期記憶作為有限大小的雙端隊列，實現 FIFO 行為
        self.short_term = deque(maxlen=MAX_SHORT_TERM_MEMORY)
        
        # 長期記憶，包含重要性評分、時間戳和內容
        self.long_term = []
        
        # 用於去重的記憶內容集合
        self.memory_set = set()
        
        # 從記憶中生成的反思
        self.reflections = []
        
        # 上次反思後的動作計數器
        self.actions_since_reflection = 0
    
    def add_memory(self, content: str, importance: float = 0.5) -> None:
        """
        向系統添加新記憶。
        
        參數:
            content: 記憶內容
            importance: 記憶的重要性 (0-1)
        """
        # 創建記憶指紋用於去重
        memory_fingerprint = content
        
        # 如果是重複記憶則跳過
        if memory_fingerprint in self.memory_set:
            return
        
        # 添加到記憶集合用於去重
        self.memory_set.add(memory_fingerprint)
        
        # 創建記憶對象
        memory = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "importance": importance
        }
        
        # 總是添加到短期記憶
        self.short_term.append(memory)
        
        # 如果足夠重要則添加到長期記憶
        if importance > 0.3:
            self.long_term.append(memory)
            
            # 如果長期記憶超過限制，移除最不重要的記憶
            if len(self.long_term) > MAX_LONG_TERM_MEMORY:
                self.long_term.sort(key=lambda x: x["importance"])
                self.long_term = self.long_term[1:]  # 移除最不重要的
        
        # 增加動作計數器並檢查是否需要反思
        self.actions_since_reflection += 1
        if self.actions_since_reflection >= REFLECTION_INTERVAL:
            self.reflect()
    
    def retrieve_relevant(self, query: str, limit: int = 5) -> List[Dict]:
        """
        檢索與查詢相關的記憶。
        
        參數:
            query: 搜索查詢
            limit: 返回的最大記憶數量
            
        返回:
            相關記憶的列表
        """
        # 簡單的關鍵詞匹配來確定相關性
        # 在實際實現中，可以使用嵌入向量或語義搜索
        results = []
        
        # 先檢查短期記憶
        for memory in self.short_term:
            if query in memory["content"]:
                results.append(memory)
        
        # 然後檢查長期記憶
        for memory in self.long_term:
            if query in memory["content"] and memory not in results:
                results.append(memory)
                
        # 按重要性和近期性排序（簡單評分）
        results.sort(key=lambda x: (x["importance"], x["timestamp"]), reverse=True)
        return results[:limit]
    
    def reflect(self) -> None:
        """根據最近的記憶生成反思。"""
        # 重置動作計數器
        self.actions_since_reflection = 0
        
        # 獲取用於反思的最近記憶
        recent_memories = list(self.short_term)
        if not recent_memories:
            return
            
        # 組合記憶內容
        memory_texts = [m["content"] for m in recent_memories]
        reflection_prompt = f"根據這些最近的經驗，我能學到或推斷出什麼結論？\n\n{memory_texts}"
        
        # 使用 DeepSeek API 生成反思
        try:
            reflection = self._generate_text(reflection_prompt)
            
            # 添加反思到列表
            self.reflections.append({
                "content": reflection,
                "timestamp": datetime.now().isoformat(),
                "based_on": [m["content"] for m in recent_memories]
            })
            
            # 以較高的重要性將反思添加到長期記憶
            self.long_term.append({
                "content": f"反思: {reflection}",
                "timestamp": datetime.now().isoformat(),
                "importance": 0.8
            })
        except Exception as e:
            print(f"生成反思失敗: {e}")
    
    def _generate_text(self, prompt: str) -> str:
        """使用 DeepSeek API 生成文本。"""
        payload = {
            "model": "deepseek-r1-distill-qwen-7b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(API_URL, json=payload)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API 請求失敗: {e}")
            return "目前無法生成反思。"
    
    def to_dict(self) -> Dict:
        """將記憶轉換為字典以便存儲。"""
        return {
            "short_term": list(self.short_term),
            "long_term": self.long_term,
            "reflections": self.reflections
        }
    
    def from_dict(self, data: Dict) -> None:
        """從字典數據加載記憶。"""
        # 清除當前記憶
        self.short_term.clear()
        self.memory_set.clear()
        
        # 加載短期記憶
        for memory in data.get("short_term", []):
            self.short_term.append(memory)
            self.memory_set.add(memory["content"])
            
        # 加載長期記憶
        self.long_term = data.get("long_term", [])
        for memory in self.long_term:
            self.memory_set.add(memory["content"])
            
        # 加載反思
        self.reflections = data.get("reflections", [])
    
    def save(self, filename: str = "memory.json") -> None:
        """將記憶保存到 JSON 文件。"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
            
    def load(self, filename: str = "memory.json") -> None:
        """從 JSON 文件加載記憶。"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.from_dict(data)
        except FileNotFoundError:
            print(f"記憶文件 {filename} 未找到。從空記憶開始。")
            
    def export_memory(self, filename: str = "memory_export.json") -> None:
        """匯出記憶到單獨的JSON檔案，便於查看。"""
        export_data = {
            "short_term_memories": [{"content": m["content"], 
                                     "time": m["timestamp"], 
                                     "importance": m["importance"]} 
                                    for m in self.short_term],
            "long_term_memories": [{"content": m["content"], 
                                     "time": m["timestamp"], 
                                     "importance": m["importance"]} 
                                    for m in self.long_term],
            "reflections": [{"content": r["content"], 
                            "time": r["timestamp"], 
                            "based_on": r["based_on"]} 
                           for r in self.reflections],
            "export_time": datetime.now().isoformat(),
            "summary": {
                "short_term_count": len(self.short_term),
                "long_term_count": len(self.long_term),
                "reflections_count": len(self.reflections)
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
            
        print(f"記憶已匯出至 {filename}")