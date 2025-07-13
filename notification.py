import platform
import webbrowser

if platform.system() == "Windows":
    from win10toast_click import ToastNotifier
    notifier = ToastNotifier()

def show_notification(title, message, url=None, duration=5):
    try:
        if platform.system() == "Windows":
            notifier.show_toast(
                title,
                message,
                duration=duration,
                callback_on_click=lambda: webbrowser.open(url) if url else None
            )
        else:
            print(f"[{title}] {message}")
            if url:
                webbrowser.open(url)
    except Exception as e:
        print(f"[!] Notificação falhou: {e}")
        print(f"[{title}] {message}")
