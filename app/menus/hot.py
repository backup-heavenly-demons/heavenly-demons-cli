import json

from app.client.engsel import get_family, get_package_details
from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, format_quota_byte, pause, display_html
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.console import console, print_cyber_panel, cyber_input, loading_animation, print_step
from rich.table import Table
from rich.panel import Panel

WIDTH = 55

def show_hot_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        
        hot_packages = []
        with open("hot_data/hot.json", "r", encoding="utf-8") as f:
            hot_packages = json.load(f)

        table = Table(show_header=True, header_style="neon_pink", box=None, padding=(0, 1))
        table.add_column("No", style="neon_green", justify="right", width=4)
        table.add_column("Family Name", style="bold white")
        table.add_column("Variant", style="cyan")
        table.add_column("Option", style="dim white")

        for idx, p in enumerate(hot_packages):
            table.add_row(
                str(idx + 1),
                p['family_name'],
                p['variant_name'],
                p['option_name']
            )

        print_cyber_panel(table, title="HOT PACKAGES 🔥")
        console.print("[dim]00. Kembali ke menu utama[/]")
        
        choice = cyber_input("Pilih paket (nomor)")
        if choice == "00":
            in_bookmark_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_bm = hot_packages[int(choice) - 1]
            family_code = selected_bm["family_code"]
            is_enterprise = selected_bm["is_enterprise"]
            
            with loading_animation("Fetching family data..."):
                family_data = get_family(api_key, tokens, family_code, is_enterprise)

            if not family_data:
                console.print("[error]Gagal mengambil data family.[/]")
                pause()
                continue
            
            package_variants = family_data["package_variants"]
            option_code = None
            for variant in package_variants:
                if variant["name"] == selected_bm["variant_name"]:
                    selected_variant = variant
                    
                    package_options = selected_variant["package_options"]
                    for option in package_options:
                        if option["order"] == selected_bm["order"]:
                            selected_option = option
                            option_code = selected_option["package_option_code"]
                            break
            
            if option_code:
                print_step(f"Option Code: {option_code}")
                show_package_details(api_key, tokens, option_code, is_enterprise)            
            
        else:
            console.print("[error]Input tidak valid. Silahkan coba lagi.[/]")
            pause()
            continue

def show_hot_menu2():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()
        main_package_detail = {}
        
        hot_packages = []
        with open("hot_data/hot2.json", "r", encoding="utf-8") as f:
            hot_packages = json.load(f)

        table = Table(show_header=True, header_style="neon_pink", box=None, padding=(0, 1))
        table.add_column("No", style="neon_green", justify="right", width=4)
        table.add_column("Name", style="bold white")
        table.add_column("Price", style="yellow")

        for idx, p in enumerate(hot_packages):
            table.add_row(str(idx + 1), p['name'], str(p['price']))

        print_cyber_panel(table, title="HOT PACKAGES 2 🔥")
        console.print("[dim]00. Kembali ke menu utama[/]")
        
        choice = cyber_input("Pilih paket (nomor)")
        if choice == "00":
            in_bookmark_menu = False
            return None

        if choice.isdigit() and 1 <= int(choice) <= len(hot_packages):
            selected_package = hot_packages[int(choice) - 1]
            packages = selected_package.get("packages", [])
            if len(packages) == 0:
                console.print("[warning]Paket tidak tersedia.[/]")
                pause()
                continue
            
            payment_items = []
            failed = False

            with loading_animation("Fetching package details..."):
                for package in packages:
                    package_detail = get_package_details(
                        api_key,
                        tokens,
                        package["family_code"],
                        package["variant_code"],
                        package["order"],
                        package["is_enterprise"],
                        package["migration_type"],
                    )

                    if package == packages[0]:
                        main_package_detail = package_detail

                    # Force failed when one of the package detail is None
                    if not package_detail:
                        failed = True
                        break

                    payment_items.append(
                        PaymentItem(
                            item_code=package_detail["package_option"]["package_option_code"],
                            product_type="",
                            item_price=package_detail["package_option"]["price"],
                            item_name=package_detail["package_option"]["name"],
                            tax=0,
                            token_confirmation=package_detail["token_confirmation"],
                        )
                    )

            if failed:
                console.print(f"[error]Gagal mengambil detail paket untuk {package['family_code']}.[/]")
                pause()
                return None
            
            clear_screen()
            
            # Package Overview Panel
            overview_text = f"""Name: [bold white]{selected_package['name']}[/]
Price: [yellow]{selected_package['price']}[/]
Detail: {selected_package['detail']}"""
            print_cyber_panel(overview_text, title="PACKAGE OVERVIEW")

            # Show package 0 details
            price = main_package_detail["package_option"]["price"]
            detail = display_html(main_package_detail["package_option"]["tnc"])
            validity = main_package_detail["package_option"]["validity"]

            option_name = main_package_detail.get("package_option", {}).get("name","")
            family_name = main_package_detail.get("package_family", {}).get("name","")
            variant_name = main_package_detail.get("package_detail_variant", "").get("name","")
            
            title = f"{family_name} - {variant_name} - {option_name}".strip()
            
            family_code = main_package_detail.get("package_family", {}).get("package_family_code","")
            parent_code = main_package_detail.get("package_addon", {}).get("parent_code","")
            if parent_code == "":
                parent_code = "N/A"
            
            payment_for = main_package_detail["package_family"]["payment_for"]

            # Detailed Info Table
            info_table = Table(show_header=False, box=None, padding=(0, 2))
            info_table.add_column("Key", style="cyan", justify="right")
            info_table.add_column("Value", style="white")

            info_table.add_row("Nama:", title)
            info_table.add_row("Harga:", f"Rp {price}")
            info_table.add_row("Payment For:", str(payment_for))
            info_table.add_row("Masa Aktif:", str(validity))
            info_table.add_row("Point:", str(main_package_detail['package_option']['point']))
            info_table.add_row("Plan Type:", main_package_detail['package_family']['plan_type'])
            info_table.add_row("Family Code:", family_code)
            info_table.add_row("Parent Code:", parent_code)

            print_cyber_panel(info_table, title="MAIN PACKAGE DETAILS")

            benefits = main_package_detail["package_option"]["benefits"]
            if benefits and isinstance(benefits, list):
                benefit_table = Table(show_header=True, header_style="neon_pink", box=None)
                benefit_table.add_column("Benefit Name", style="white")
                benefit_table.add_column("Total", style="neon_green")
                benefit_table.add_column("Type", style="dim")

                for benefit in benefits:
                    total_display = ""
                    data_type = benefit['data_type']
                    if data_type == "VOICE" and benefit['total'] > 0:
                        total_display = f"{benefit['total']/60} menit"
                    elif data_type == "TEXT" and benefit['total'] > 0:
                        total_display = f"{benefit['total']} SMS"
                    elif data_type == "DATA" and benefit['total'] > 0:
                        if benefit['total'] > 0:
                            quota = int(benefit['total'])
                            quota_formatted = format_quota_byte(quota)
                            total_display = f"{quota_formatted}"
                    elif data_type not in ["DATA", "VOICE", "TEXT"]:
                        total_display = str(benefit['total'])
                    
                    if benefit.get("is_unlimited"):
                        total_display = "Unlimited"

                    benefit_table.add_row(benefit['name'], total_display, data_type)
                
                print_cyber_panel(benefit_table, title="BENEFITS")

            console.print(Panel(detail, title="[neon_pink]SnK MyXL[/]", border_style="dim white"))
            
            payment_for = selected_package.get("payment_for", "BUY_PACKAGE")
            ask_overwrite = selected_package.get("ask_overwrite", False)
            overwrite_amount = selected_package.get("overwrite_amount", -1)
            token_confirmation_idx = selected_package.get("token_confirmation_idx", 0)
            amount_idx = selected_package.get("amount_idx", -1)

            in_payment_menu = True
            while in_payment_menu:
                payment_menu_table = Table(show_header=False, box=None)
                payment_menu_table.add_row("1", "Balance")
                payment_menu_table.add_row("2", "E-Wallet")
                payment_menu_table.add_row("3", "QRIS")
                payment_menu_table.add_row("00", "Kembali ke menu sebelumnya")
                
                print_cyber_panel(payment_menu_table, title="METODE PEMBELIAN")

                input_method = cyber_input("Pilih metode (nomor)")
                if input_method == "1":
                    if overwrite_amount == -1:
                        console.print(f"[bold red]Pastikan sisa balance KURANG DARI Rp{payment_items[-1]['item_price']}!!![/]")
                        balance_answer = cyber_input("Apakah anda yakin ingin melanjutkan pembelian? (y/n)")
                        if balance_answer.lower() != "y":
                            console.print("[warning]Pembelian dibatalkan oleh user.[/]")
                            pause()
                            in_payment_menu = False
                            continue

                    with loading_animation("Processing balance payment..."):
                        settlement_balance(
                            api_key,
                            tokens,
                            payment_items,
                            payment_for,
                            ask_overwrite,
                            overwrite_amount=overwrite_amount,
                            token_confirmation_idx=token_confirmation_idx,
                            amount_idx=amount_idx,
                        )
                    pause()
                    in_payment_menu = False
                    in_bookmark_menu = False
                elif input_method == "2":
                    show_multipayment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )
                    pause()
                    in_payment_menu = False
                    in_bookmark_menu = False
                elif input_method == "3":
                    show_qris_payment(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        ask_overwrite,
                        overwrite_amount,
                        token_confirmation_idx,
                        amount_idx,
                    )

                    pause()
                    in_payment_menu = False
                    in_bookmark_menu = False
                elif input_method == "00":
                    in_payment_menu = False
                    continue
                else:
                    console.print("[error]Metode tidak valid. Silahkan coba lagi.[/]")
                    pause()
                    continue
        else:
            console.print("[error]Input tidak valid. Silahkan coba lagi.[/]")
            pause()
            continue
