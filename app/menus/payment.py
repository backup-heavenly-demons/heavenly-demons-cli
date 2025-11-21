from datetime import datetime, timedelta

from app.client.engsel import get_transaction_history
from app.menus.util import clear_screen
from app.console import console, print_cyber_panel, cyber_input, loading_animation
from rich.table import Table

def show_transaction_history(api_key, tokens):
    in_transaction_menu = True

    while in_transaction_menu:
        clear_screen()

        data = None
        history = []
        try:
            with loading_animation("Fetching transaction history..."):
                data = get_transaction_history(api_key, tokens)
            history = data.get("list", [])
        except Exception as e:
            console.print(f"[error]Gagal mengambil riwayat transaksi: {e}[/]")
            history = []
        
        if len(history) == 0:
             console.print("[warning]Tidak ada riwayat transaksi.[/]")
        else:
            table = Table(show_header=True, header_style="neon_pink", box=None)
            table.add_column("No", style="neon_green", justify="right", width=4)
            table.add_column("Item", style="bold white")
            table.add_column("Date", style="cyan")
            table.add_column("Status", style="dim")

            for idx, transaction in enumerate(history, start=1):
                transaction_timestamp = transaction.get("timestamp", 0)
                dt = datetime.fromtimestamp(transaction_timestamp)
                dt_jakarta = dt - timedelta(hours=7)

                formatted_time = dt_jakarta.strftime("%d %b %Y %H:%M")

                status_color = "green" if transaction['status'] == "SUCCESS" else "red"
                status_display = f"[{status_color}]{transaction['status']}[/]"

                table.add_row(
                    str(idx),
                    f"{transaction['title']}\n[dim]{transaction['payment_method_label']} - {transaction['price']}[/]",
                    formatted_time,
                    status_display
                )

            print_cyber_panel(table, title="RIWAYAT TRANSAKSI")

        # Option
        console.print("[dim]0. Refresh | 00. Kembali ke Menu Utama[/]")
        choice = cyber_input("Pilih opsi")
        if choice == "0":
            continue
        elif choice == "00":
            in_transaction_menu = False
        else:
            console.print("[error]Opsi tidak valid. Silakan coba lagi.[/]")
