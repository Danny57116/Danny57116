# youtube_read1
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api import TranscriptsDisabled, NoTranscriptFound
import warnings
import datetime

# 替換成你想獲取轉錄稿的 YouTube 影片 ID
video_id = 'V8RxHtoLVTk' # 請替換成實際的影片 ID
#V8RxHtoLVTk
#
#https://youtu.be/M2Yg1kwPpts?si=Cl35xYtsqI6iOUjl
try:
    # 抑制 ResourceWarning 警告
    warnings.filterwarnings("ignore", category=ResourceWarning)
    
    # --- 方法一：獲取預設語言的轉錄稿 ---
    print(f"--- 正在嘗試獲取影片 '{video_id}' 的預設轉錄稿 ---")
    transcript_list = YouTubeTranscriptApi.get_transcript(video_id)

    print("成功獲取轉錄稿1：")
    full_transcript_text = ""
    for entry in transcript_list:
        # entry 是一個字典，包含 'text', 'start', 'duration'
#        print(f"時間：{entry['start']:.2f}s, 持續：{entry['duration']:.2f}s, 內容：{entry['text']}")
        full_transcript_text += entry['text'] + " "

    print("\n--- 完整的轉錄稿文字2 ---")
    print(full_transcript_text.strip()) # .strip() 去掉前後多餘空格
    

    # --- 方法二：列出所有可用的轉錄稿語言，並獲取指定語言 ---
    print(f"\n--- 正在列出影片3 '{video_id}' 所有可用的轉錄稿語言 ---")
    transcript_list_obj = YouTubeTranscriptApi.list_transcripts(video_id)

    available_languages = {}
    print("可用的語言4：")
    for transcript in transcript_list_obj:
        # transcript 物件包含語言 (language) 和語言代碼 (language_code) 等資訊
        print(f"- {transcript.language} ({transcript.language_code}) {'(自動產生)' if transcript.is_generated else '(手動上傳)'}")
        available_languages[transcript.language_code] = transcript.language

    # 嘗試獲取特定語言的轉錄稿，例如英文 ('en') 或繁體中文 ('zh-Hant')
    target_language_code = 'zh-Hant' # 嘗試獲取繁體中文

    if target_language_code in available_languages:
        print(f"\n--- 正在嘗試獲取 '{available_languages[target_language_code]}' ({target_language_code}) 的轉錄稿 ---")
        # 找到指定語言的 transcript 物件
        selected_transcript = transcript_list_obj.find_transcript([target_language_code])
        # 獲取該語言的轉錄稿內容
        specific_transcript_data = selected_transcript.fetch()

        print(f"成功獲取 '{target_language_code}' 轉錄稿：")
        specific_full_text = ""
        for entry in specific_transcript_data:
            print(f"時間：{entry['start']:.2f}s, 內容：{entry['text']}")
            specific_full_text += entry['text'] + " "

        print(f"\n--- '{target_language_code}' 的完整轉錄稿文字1 ---")
        print(specific_full_text.strip())

    elif available_languages:
         print(f"\n找不到指定的語言 '{target_language_code}'，但影片有其他語言的轉錄稿。")
    else:
         print(f"\n找不到指定的語言 '{target_language_code}'，且影片沒有其他可用的轉錄稿。")


except TranscriptsDisabled:
    print(f"錯誤：影片 '{video_id}' 的轉錄稿功能已被禁用。")
except NoTranscriptFound:
    print(f"錯誤：找不到影片 '{video_id}' 的任何轉錄稿（指定的語言或預設語言）。")
    # 可以嘗試列出可用的語言（如果有的話）
    try:
        available_manual_transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
        print("但是，找到以下手動上傳或自動產生的語言版本：")
        for t in available_manual_transcripts:
             print(f"- {t.language} ({t.language_code})")
    except Exception:
        print("也無法列出其他可用語言。")

except Exception as e:
    print(f"發生未預期的錯誤：{e}")

finally:
    # 恢復警告設置
    warnings.resetwarnings()
    
def write_to_markdown(file_path, content, mode='w'):
    """
    將內容寫入 Markdown (.md) 檔案
    
    參數:
        file_path (str): 要寫入的檔案路徑
        content (str): 要寫入的內容
        mode (str): 寫入模式，'w'為覆寫，'a'為追加
    """
    
#    file_path = '/doucments/danny7116/'
    current_time = datetime.datetime.now().strftime("%Y%m%d")
    file_path = f"note_{current_time}.md"

    try:
        with open(file_path, mode, encoding='utf-8') as file:
            file.write(content)
        print(f"成功將內容寫入 {file_path}")
    except IOError as e:
        print(f"寫入檔案時發生錯誤: {e}")


