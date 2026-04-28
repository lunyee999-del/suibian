import os
import subprocess
from pathlib import Path

def main():
    profile_dir = Path(__file__).parent / "storage" / "xhs-profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    ]
    
    executable = None
    for c in candidates:
        if c.exists():
            executable = str(c)
            break
            
    if not executable:
        print("未找到 Edge 或 Chrome 浏览器。")
        return

    print("正在为您打开常驻安全浏览器，请稍候...")
    print(f"使用的配置文件目录: {profile_dir}")
    
    args = [
        executable,
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--disable-default-browser-check",
        "--remote-debugging-port=9333",
        "https://creator.xiaohongshu.com/publish/publish"
    ]
    
    subprocess.Popen(args)
    print("浏览器已启动！请在弹出的窗口中扫码登录小红书，登录完成后您可以将浏览器最小化（但不要关闭）。")

if __name__ == "__main__":
    main()
