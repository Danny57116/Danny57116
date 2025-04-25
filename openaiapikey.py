import requests
import json

def verify_openai_api_key(api_key):
    """
    檢驗 OpenAI API key 是否可用
    
    參數:
        api_key (str): 要驗證的 OpenAI API key
    
    返回:
        bool: API key 是否有效
        str: 響應消息或錯誤信息
    """
    # 設置 API 請求的 URL
    url = "https://api.openai.com/v1/models"
    
    # 設置請求頭，包含 API key
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # 發送 GET 請求來獲取可用的模型列表
        response = requests.get(url, headers=headers)
        
        # 檢查響應狀態碼
        if response.status_code == 200:
            # API key 有效
            return True, "API key 有效，可以使用"
        else:
            # API key 無效或有其他問題
            error_message = response.json().get("error", {}).get("message", "未知錯誤")
            return False, f"API key 無效: {error_message}"
    
    except Exception as e:
        # 處理請求過程中的錯誤
        return False, f"驗證過程中發生錯誤: {str(e)}"

# 使用示例
if __name__ == "__main__":
    print("OpenAI API Key 驗證工具")
    api_key = input("請輸入您的 OpenAI API key: ")
    
    is_valid, message = verify_openai_api_key(api_key)
    
    if is_valid:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")