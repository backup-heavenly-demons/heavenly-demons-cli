from app.menus.util import clear_screen, pause
from app.client.engsel import get_notification_detail, dashboard_segments
from app.service.auth import AuthInstance
from app.console import console, print_cyber_panel, cyber_input, loading_animation
from rich.table import Table

WIDTH = 55

def show_notification_menu():
    in_notification_menu = True
    while in_notification_menu:
        clear_screen()
        
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        with loading_animation("Fetching notifications..."):
            notifications_res = dashboard_segments(api_key, tokens)

        if not notifications_res:
            console.print("[warning]No notifications found.[/]")
            return
        
        notifications = notifications_res.get("data", {}).get("notification", {}).get("data", [])
        if not notifications:
            console.print("[warning]No notifications available.[/]")
            pause()
            return
        
        unread_count = 0

        table = Table(show_header=True, header_style="neon_pink", box=None)
        table.add_column("No", style="neon_green", justify="right", width=4)
        table.add_column("Status", style="bold white")
        table.add_column("Message", style="cyan")
        table.add_column("Time", style="dim")

        for idx, notification in enumerate(notifications):
            is_read = notification.get("is_read", False)
            full_message = notification.get("full_message", "")
            brief_message = notification.get("brief_message", "")
            time = notification.get("timestamp", "")
            
            status = ""
            if is_read:
                status = "[dim]READ[/]"
            else:
                status = "[bold neon_green]UNREAD[/]"
                unread_count += 1

            table.add_row(
                str(idx + 1),
                status,
                f"{brief_message}\n[dim]{full_message}[/]",
                time
            )

        print_cyber_panel(table, title=f"NOTIFICATIONS ({unread_count} UNREAD)")

        console.print("[dim]1. Read All Unread Notifications\n00. Back to Main Menu[/]")
        choice = cyber_input("Enter your choice")
        if choice == "1":
            with loading_animation("Marking as read..."):
                for notification in notifications:
                    if notification.get("is_read", False):
                        continue
                    notification_id = notification.get("notification_id")
                    detail = get_notification_detail(api_key, tokens, notification_id)
                    if detail:
                        console.print(f"[info]Marked READ: {notification_id}[/]")
            pause()
        elif choice == "00":
            in_notification_menu = False
        else:
            console.print("[error]Invalid choice. Please try again.[/]")
            pause()
