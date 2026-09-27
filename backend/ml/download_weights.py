import urllib.request
import os

def download_yolo():
    url = "https://github.com/ultralytics/assets/releases/download/v8.0.0/yolov8n.pt"
    output = "yolov8n.pt"
    
    if not os.path.exists(output):
        print(f"[*] Скачивание весов {output}...")
        try:
            urllib.request.urlretrieve(url, output)
            print("[+] Загрузка успешно завершена.")
        except Exception as e:
            print(f"[-] Ошибка при загрузке: {e}")
    else:
        print(f"[*] Файл {output} уже существует.")

if __name__ == "__main__":
    download_yolo()