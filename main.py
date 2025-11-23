from dotenv import load_dotenv

from app.service.git import check_for_updates
load_dotenv()

import sys, json
from datetime import datetime
from app.menus.util import clear_screen, pause
from app.client.engsel import (
    get_balance,
    get_tiering_info,
)
from app.client.famplan import validate_msisdn
from app.menus.payment import show_transaction_history
from app.service.auth import AuthInstance
from app.menus.bookmark import show_bookmark_menu
from app.menus.account import show_account_menu
from app.menus.package import fetch_my_packages, get_packages_by_family, show_package_details
from app.menus.hot import show_hot_menu, show_hot_menu2
from app.service.sentry import enter_sentry_mode
from app.menus.purchase import purchase_by_family
from app.menus.famplan import show_family_info
from app.menus.circle import show_circle_info
from app.menus.notification import show_notification_menu
from app.menus.store.segments import show_store_segments_menu
from app.menus.store.search import show_family_list_menu, show_store_packages_menu
from app.menus.store.redemables import show_redeemables_menu
from app.client.registration import dukcapil

# NEW IMPORTS FOR UI
from rich.table import Table
from rich.columns import Columns
from rich.panel import Panel
from app.console import console, print_cyber_panel, cyber_input, loading_animation, print_step

WIDTH = 55

def show_main_menu(profile):
    clear_screen()

    # Profile Table
    expired_at_dt = datetime.fromtimestamp(profile["balance_expired_at"]).strftime("%Y-%m-%d")

    profile_table = Table(show_header=False, box=None, padding=(0, 2))
    profile_table.add_column("Key", style="neon_cyan", justify="right")
    profile_table.add_column("Value", style="bold white")

    profile_table.add_row("Nomor:", str(profile['number']))
    profile_table.add_row("Type:", str(profile['subscription_type']))
    profile_table.add_row("Pulsa:", f"Rp {profile['balance']}")
    profile_table.add_row("Aktif s/d:", str(expired_at_dt))
    profile_table.add_row("Info:", str(profile['point_info']))

    print_cyber_panel(profile_table, title="USER PROFILE")

    # Menu Grid
    menu_table = Table(show_header=True, header_style="neon_pink", box=None, padding=(0, 1))
    menu_table.add_column("ID", style="neon_green", justify="right", width=4)
    menu_table.add_column("Action", style="bold white")

    menu_items = [
        ("1", "Login/Ganti akun"),
        ("2", "Lihat Paket Saya"),
        ("3", "Beli Paket 🔥 HOT 🔥"),
        ("4", "Beli Paket 🔥 HOT-2 🔥"),
        ("5", "Beli Paket conference"),
        ("6", "BIZ lite (BIZ ORI only )"),
        ("7", "BIZ Data+ (BIZ ORI only )"),
        ("8", "Beli Paket (Option Code)"),
        ("9", "Beli Paket (Family Code)"),
        ("10", "Beli Semua Paket (Loop)"),
        ("11", "Riwayat Transaksi"),
        ("12", "Family Plan/Akrab"),
        ("13", "Circle"),
        ("14", "Store Segments"),
        ("15", "Store Family List"),
        ("16", "Store Packages"),
        ("17", "Redemables"),
        ("R", "Register Dukcapil"),
        ("N", "Notifikasi"),
        ("V", "Validate MSISDN"),
        ("00", "Bookmark Paket"),
        ("99", "Tutup Aplikasi"),
    ]

    for key, desc in menu_items:
        menu_table.add_row(key, desc)

    console.print(Panel(menu_table, title="[neon_pink]MAIN MENU[/]", border_style="neon_cyan"))


show_menu = True
def main():
    
    while True:
        active_user = AuthInstance.get_active_user()

        # Logged in
        if active_user is not None:
            # Use loading animation for fetching data
            with loading_animation("Fetching user data..."):
                balance = get_balance(AuthInstance.api_key, active_user["tokens"]["id_token"])
                balance_remaining = balance.get("remaining")
                balance_expired_at = balance.get("expired_at")

                point_info = "Points: N/A | Tier: N/A"

                if active_user["subscription_type"] == "PREPAID":
                    tiering_data = get_tiering_info(AuthInstance.api_key, active_user["tokens"])
                    tier = tiering_data.get("tier", 0)
                    current_point = tiering_data.get("current_point", 0)
                    point_info = f"Points: {current_point} | Tier: {tier}"
            
            profile = {
                "number": active_user["number"],
                "subscriber_id": active_user["subscriber_id"],
                "subscription_type": active_user["subscription_type"],
                "balance": balance_remaining,
                "balance_expired_at": balance_expired_at,
                "point_info": point_info
            }

            show_main_menu(profile)

            choice = cyber_input("Pilih menu")

            # Testing shortcuts
            if choice.lower() == "t":
                pause()
            elif choice == "1":
                selected_user_number = show_account_menu()
                if selected_user_number:
                    AuthInstance.set_active_user(selected_user_number)
                else:
                    console.print("[error]No user selected or failed to load user.[/]")
                    pause()
                continue
            elif choice == "2":
                fetch_my_packages()
                continue
            elif choice == "3":
                show_hot_menu()
            elif choice == "4":
                show_hot_menu2()
            elif choice == "5":
                get_packages_by_family("5dab52d5-6f02-4678-b72f-088396ceb113")
            elif choice == "6":
                get_packages_by_family("f3303d95-8454-4e80-bb25-38513d358a11")
            elif choice == "7":
                get_packages_by_family("53de8ac3-521d-43f5-98ce-749ad0481709")
            elif choice == "8":
                option_code = cyber_input("Enter option code (or '99' to cancel)")
                if option_code == "99":
                    continue
                show_package_details(
                    AuthInstance.api_key,
                    active_user["tokens"],
                    option_code,
                    False
                )
            elif choice == "9":
                family_code = cyber_input("Enter family code (or '99' to cancel)")
                if family_code == "99":
                    continue
                get_packages_by_family(family_code)
            elif choice == "10":
                family_code = cyber_input("Enter family code (or '99' to cancel)")
                if family_code == "99":
                    continue

                start_from_option = cyber_input("Start purchasing from option number (default 1)")
                try:
                    start_from_option = int(start_from_option)
                except ValueError:
                    start_from_option = 1

                use_decoy = cyber_input("Use decoy package? (y/n)").lower() == 'y'
                pause_on_success = cyber_input("Pause on each successful purchase? (y/n)").lower() == 'y'
                delay_seconds = cyber_input("Delay seconds between purchases (0 for no delay)")
                try:
                    delay_seconds = int(delay_seconds)
                except ValueError:
                    delay_seconds = 0
                purchase_by_family(
                    family_code,
                    use_decoy,
                    pause_on_success,
                    delay_seconds,
                    start_from_option
                )
            elif choice == "11":
                show_transaction_history(AuthInstance.api_key, active_user["tokens"])
            elif choice == "12":
                show_family_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "13":
                show_circle_info(AuthInstance.api_key, active_user["tokens"])
            elif choice == "14":
                input_11 = cyber_input("Is enterprise store? (y/n)").lower()
                is_enterprise = input_11 == 'y'
                show_store_segments_menu(is_enterprise)
            elif choice == "15":
                input_12_1 = cyber_input("Is enterprise? (y/n)").lower()
                is_enterprise = input_12_1 == 'y'
                show_family_list_menu(profile['subscription_type'], is_enterprise)
            elif choice == "16":
                input_13_1 = cyber_input("Is enterprise? (y/n)").lower()
                is_enterprise = input_13_1 == 'y'
                
                show_store_packages_menu(profile['subscription_type'], is_enterprise)
            elif choice == "17":
                input_14_1 = cyber_input("Is enterprise? (y/n)").lower()
                is_enterprise = input_14_1 == 'y'
                
                show_redeemables_menu(is_enterprise)
            elif choice == "00":
                show_bookmark_menu()
            elif choice == "99":
                console.print("[bold red]Exiting the application...[/]")
                sys.exit(0)
            elif choice.lower() == "r":
                msisdn = cyber_input("Enter msisdn (628xxxx)")
                nik = cyber_input("Enter NIK")
                kk = cyber_input("Enter KK")
                
                with loading_animation("Registering..."):
                    res = dukcapil(
                        AuthInstance.api_key,
                        msisdn,
                        kk,
                        nik,
                    )
                console.print_json(data=res)
                pause()
            elif choice.lower() == "v":
                msisdn = cyber_input("Enter the msisdn to validate (628xxxx)")
                with loading_animation("Validating..."):
                    res = validate_msisdn(
                        AuthInstance.api_key,
                        active_user["tokens"],
                        msisdn,
                    )
                console.print_json(data=res)
                pause()
            elif choice.lower() == "n":
                show_notification_menu()
            elif choice == "s":
                enter_sentry_mode()
            else:
                console.print("[error]Invalid choice. Please try again.[/]")
                pause()
        else:
            # Not logged in
            selected_user_number = show_account_menu()
            if selected_user_number:
                AuthInstance.set_active_user(selected_user_number)
            else:
                console.print("[error]No user selected or failed to load user.[/]")
                pause() # Added pause so user can read the error

if __name__ == "__main__":
    try:
        print_step("Checking for updates...")
        with loading_animation("Checking git..."):
            need_update = check_for_updates()
        if need_update:
            pause()

        main()
    except KeyboardInterrupt:
        console.print("\n[bold red]Exiting the application.[/]")
    # except Exception as e:
    #     console.print(f"[error]An error occurred: {e}[/]")
