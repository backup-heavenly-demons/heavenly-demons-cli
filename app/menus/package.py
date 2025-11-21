import json
import sys

import requests
from app.service.auth import AuthInstance
from app.client.engsel import get_family, get_package, get_addons, get_package_details, send_api_request, unsubscribe
from app.client.ciam import get_auth_code
from app.service.bookmark import BookmarkInstance
from app.client.purchase.redeem import settlement_bounty, settlement_loyalty, bounty_allotment
from app.menus.util import clear_screen, pause, display_html
from app.client.purchase.qris import show_qris_payment
from app.client.purchase.ewallet import show_multipayment
from app.client.purchase.balance import settlement_balance
from app.type_dict import PaymentItem
from app.menus.purchase import purchase_n_times, purchase_n_times_by_option_code
from app.menus.util import format_quota_byte
from app.service.decoy import DecoyInstance
from app.console import console, print_cyber_panel, cyber_input, loading_animation, print_step
from rich.table import Table
from rich.panel import Panel

def show_package_details(api_key, tokens, package_option_code, is_enterprise, option_order = -1):
    active_user = AuthInstance.active_user
    subscription_type = active_user.get("subscription_type", "")
    
    clear_screen()

    with loading_animation("Fetching package details..."):
        package = get_package(api_key, tokens, package_option_code)

    if not package:
        console.print("[error]Failed to load package details.[/]")
        pause()
        return False

    price = package["package_option"]["price"]
    detail = display_html(package["package_option"]["tnc"])
    validity = package["package_option"]["validity"]

    option_name = package.get("package_option", {}).get("name","")
    family_name = package.get("package_family", {}).get("name","")
    variant_name = package.get("package_detail_variant", "").get("name","")
    
    title = f"{family_name} - {variant_name} - {option_name}".strip()
    
    family_code = package.get("package_family", {}).get("package_family_code","")
    parent_code = package.get("package_addon", {}).get("parent_code","")
    if parent_code == "":
        parent_code = "N/A"
    
    token_confirmation = package["token_confirmation"]
    ts_to_sign = package["timestamp"]
    payment_for = package["package_family"]["payment_for"]
    
    payment_items = [
        PaymentItem(
            item_code=package_option_code,
            product_type="",
            item_price=price,
            item_name=f"{variant_name} {option_name}".strip(),
            tax=0,
            token_confirmation=token_confirmation,
        )
    ]
    
    # Details Table
    details_table = Table(show_header=False, box=None, padding=(0, 2))
    details_table.add_column("Key", style="neon_cyan", justify="right")
    details_table.add_column("Value", style="bold white")

    details_table.add_row("Nama:", title)
    details_table.add_row("Harga:", f"Rp {price}")
    details_table.add_row("Payment For:", str(payment_for))
    details_table.add_row("Masa Aktif:", str(validity))
    details_table.add_row("Point:", str(package['package_option']['point']))
    details_table.add_row("Plan Type:", package['package_family']['plan_type'])
    details_table.add_row("Family Code:", family_code)
    details_table.add_row("Parent Code:", parent_code)

    print_cyber_panel(details_table, title="DETAIL PAKET")

    benefits = package["package_option"]["benefits"]
    if benefits and isinstance(benefits, list):
        benefit_table = Table(show_header=True, header_style="neon_pink", box=None)
        benefit_table.add_column("Benefit Name", style="white")
        benefit_table.add_column("Total/Quota", style="neon_green")
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
                    # It is in byte, make it in GB
                    if quota >= 1_000_000_000:
                        quota_gb = quota / (1024 ** 3)
                        total_display = f"{quota_gb:.2f} GB"
                    elif quota >= 1_000_000:
                        quota_mb = quota / (1024 ** 2)
                        total_display = f"{quota_mb:.2f} MB"
                    elif quota >= 1_000:
                        quota_kb = quota / 1024
                        total_display = f"{quota_kb:.2f} KB"
                    else:
                        total_display = f"{quota} B"
            elif data_type not in ["DATA", "VOICE", "TEXT"]:
                total_display = f"{benefit['total']}"
            
            if benefit["is_unlimited"]:
                total_display = "Unlimited"

            benefit_table.add_row(benefit['name'], total_display, data_type)

        print_cyber_panel(benefit_table, title="BENEFITS")
    
    with loading_animation("Checking addons..."):
        addons = get_addons(api_key, tokens, package_option_code)
    
    # print(f"Addons:\n{json.dumps(addons, indent=2)}") # Reduced noise

    console.print(Panel(detail, title="[neon_pink]SnK MyXL[/]", border_style="dim white"))
    
    in_package_detail_menu = True
    while in_package_detail_menu:
        # Options Menu
        menu_table = Table(show_header=False, box=None)
        menu_table.add_row("1", "Beli dengan Pulsa")
        menu_table.add_row("2", "Beli dengan E-Wallet")
        menu_table.add_row("3", "Bayar dengan QRIS")
        menu_table.add_row("4", "Pulsa + Decoy")
        menu_table.add_row("5", "Pulsa + Decoy V2")
        menu_table.add_row("6", "QRIS + Decoy (+1K)")
        menu_table.add_row("7", "QRIS + Decoy V2")
        menu_table.add_row("8", "Pulsa N kali")

        # Sometimes payment_for is empty, so we set default to BUY_PACKAGE
        if payment_for == "":
            payment_for = "BUY_PACKAGE"
        
        if payment_for == "REDEEM_VOUCHER":
            menu_table.add_row("B", "Ambil sebagai bonus")
            menu_table.add_row("BA", "Kirim bonus")
            menu_table.add_row("L", "Beli dengan Poin")
        
        if option_order != -1:
            menu_table.add_row("0", "Tambah ke Bookmark")
        menu_table.add_row("00", "Kembali ke daftar paket")

        print_cyber_panel(menu_table, title="ACTIONS")

        choice = cyber_input("Pilihan")
        if choice == "00":
            return False
        elif choice == "0" and option_order != -1:
            # Add to bookmark
            success = BookmarkInstance.add_bookmark(
                family_code=package.get("package_family", {}).get("package_family_code",""),
                family_name=package.get("package_family", {}).get("name",""),
                is_enterprise=is_enterprise,
                variant_name=variant_name,
                option_name=option_name,
                order=option_order,
            )
            if success:
                console.print("[neon_green]Paket berhasil ditambahkan ke bookmark.[/]")
            else:
                console.print("[warning]Paket sudah ada di bookmark.[/]")
            pause()
            continue
        
        elif choice == '1':
            settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True
            )
            pause()
            return True
        elif choice == '2':
            show_multipayment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            pause()
            return True
        elif choice == '3':
            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                payment_for,
                True,
            )
            pause()
            return True
        elif choice == '4':
            # Balance with Decoy            
            decoy = DecoyInstance.get_decoy("balance")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                console.print("[error]Failed to load decoy package details.[/]")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                payment_for,
                False,
                overwrite_amount=overwrite_amount,
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        payment_for,
                        False,
                        overwrite_amount=valid_amount,
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        console.print("[neon_green]Purchase successful![/]")
            else:
                console.print("[neon_green]Purchase successful![/]")
            pause()
            return True
        elif choice == '5':
            # Balance with Decoy v2 (use token confirmation from decoy)
            decoy = DecoyInstance.get_decoy("balance")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                console.print("[error]Failed to load decoy package details.[/]")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )

            overwrite_amount = price + decoy_package_detail["package_option"]["price"]
            res = settlement_balance(
                api_key,
                tokens,
                payment_items,
                "🤫",
                False,
                overwrite_amount=overwrite_amount,
                token_confirmation_idx=1
            )
            
            if res and res.get("status", "") != "SUCCESS":
                error_msg = res.get("message", "Unknown error")
                if "Bizz-err.Amount.Total" in error_msg:
                    error_msg_arr = error_msg.split("=")
                    valid_amount = int(error_msg_arr[1].strip())
                    
                    print(f"Adjusted total amount to: {valid_amount}")
                    res = settlement_balance(
                        api_key,
                        tokens,
                        payment_items,
                        "🤫",
                        False,
                        overwrite_amount=valid_amount,
                        token_confirmation_idx=-1
                    )
                    if res and res.get("status", "") == "SUCCESS":
                        console.print("[neon_green]Purchase successful![/]")
            else:
                console.print("[neon_green]Purchase successful![/]")
            pause()
            return True
        elif choice == '6':
            # QRIS decoy + Rpx
            decoy = DecoyInstance.get_decoy("qris")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                console.print("[error]Failed to load decoy package details.[/]")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            
            console.print(Panel(
                f"Harga Paket Utama: Rp {price}\nHarga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}\n\nSilahkan sesuaikan amount (trial & error, 0 = malformed)",
                title="DECOY QRIS INFO",
                border_style="warning"
            ))

            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )
            
            pause()
            return True
        elif choice == '7':
            # QRIS decoy + Rp0
            decoy = DecoyInstance.get_decoy("qris0")
            
            decoy_package_detail = get_package(
                api_key,
                tokens,
                decoy["option_code"],
            )
            
            if not decoy_package_detail:
                console.print("[error]Failed to load decoy package details.[/]")
                pause()
                return False

            payment_items.append(
                PaymentItem(
                    item_code=decoy_package_detail["package_option"]["package_option_code"],
                    product_type="",
                    item_price=decoy_package_detail["package_option"]["price"],
                    item_name=decoy_package_detail["package_option"]["name"],
                    tax=0,
                    token_confirmation=decoy_package_detail["token_confirmation"],
                )
            )
            
            console.print(Panel(
                f"Harga Paket Utama: Rp {price}\nHarga Paket Decoy: Rp {decoy_package_detail['package_option']['price']}\n\nSilahkan sesuaikan amount (trial & error, 0 = malformed)",
                title="DECOY QRIS INFO",
                border_style="warning"
            ))

            show_qris_payment(
                api_key,
                tokens,
                payment_items,
                "SHARE_PACKAGE",
                True,
                token_confirmation_idx=1
            )
            
            pause()
            return True
        elif choice == '8':
            #Pulsa N kali
            use_decoy_for_n_times = cyber_input("Use decoy package? (y/n)").strip().lower() == 'y'
            n_times_str = cyber_input("Enter number of times to purchase (e.g., 3)").strip()

            delay_seconds_str = cyber_input("Enter delay between purchases in seconds (e.g., 25)").strip()
            if not delay_seconds_str.isdigit():
                delay_seconds_str = "0"

            try:
                n_times = int(n_times_str)
                if n_times < 1:
                    raise ValueError("Number must be at least 1.")
            except ValueError:
                console.print("[error]Invalid number entered. Please enter a valid integer.[/]")
                pause()
                continue
            purchase_n_times_by_option_code(
                n_times,
                option_code=package_option_code,
                use_decoy=use_decoy_for_n_times,
                delay_seconds=int(delay_seconds_str),
                pause_on_success=False,
                token_confirmation_idx=1
            )
        elif choice.lower() == 'b':
            settlement_bounty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
                item_name=variant_name
            )
            pause()
            return True
        elif choice.lower() == 'ba':
            destination_msisdn = cyber_input("Masukkan nomor tujuan bonus (mulai dengan 62)").strip()
            bounty_allotment(
                api_key=api_key,
                tokens=tokens,
                ts_to_sign=ts_to_sign,
                destination_msisdn=destination_msisdn,
                item_name=option_name,
                item_code=package_option_code,
                token_confirmation=token_confirmation,
            )
            pause()
            return True
        elif choice.lower() == 'l':
            settlement_loyalty(
                api_key=api_key,
                tokens=tokens,
                token_confirmation=token_confirmation,
                ts_to_sign=ts_to_sign,
                payment_target=package_option_code,
                price=price,
            )
            pause()
            return True
        else:
            console.print("[warning]Purchase cancelled.[/]")
            return False
    pause()
    sys.exit(0)

def get_packages_by_family(
    family_code: str,
    is_enterprise: bool | None = None,
    migration_type: str | None = None
):
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    if not tokens:
        console.print("[error]No active user tokens found.[/]")
        pause()
        return None
    
    packages = []
    
    with loading_animation("Fetching family packages..."):
        data = get_family(
            api_key,
            tokens,
            family_code,
            is_enterprise,
            migration_type
        )
    
    if not data:
        console.print("[error]Failed to load family data.[/]")
        pause()
        return None

    price_currency = "Rp"
    rc_bonus_type = data["package_family"].get("rc_bonus_type", "")
    if rc_bonus_type == "MYREWARDS":
        price_currency = "Poin"
    
    in_package_menu = True
    while in_package_menu:
        clear_screen()

        # Family Info Panel
        family_table = Table(show_header=False, box=None)
        family_table.add_column("Key", style="neon_cyan", justify="right")
        family_table.add_column("Value", style="bold white")

        family_table.add_row("Family Name:", data['package_family']['name'])
        family_table.add_row("Family Code:", family_code)
        family_table.add_row("Family Type:", data['package_family']['package_family_type'])
        family_table.add_row("Variant Count:", str(len(data['package_variants'])))

        print_cyber_panel(family_table, title="FAMILY INFO")

        # Packages List
        pkg_table = Table(show_header=True, header_style="neon_pink", box=None, padding=(0, 1))
        pkg_table.add_column("No", style="neon_green", justify="right", width=4)
        pkg_table.add_column("Package Name", style="bold white")
        pkg_table.add_column("Price", style="yellow")
        
        package_variants = data["package_variants"]
        
        option_number = 1

        # Rebuild packages list each render to ensure correct indexing if needed,
        # though strictly speaking it's static per fetch.
        packages = []
        
        for variant in package_variants:
            variant_name = variant["name"]
            # pkg_table.add_row("", f"[dim]{variant_name}[/]", "") # Section header style

            for option in variant["package_options"]:
                option_name = option["name"]
                price_display = f"{price_currency} {option['price']}"

                full_name = f"{variant_name} - {option_name}"
                
                packages.append({
                    "number": option_number,
                    "variant_name": variant_name,
                    "option_name": option_name,
                    "price": option["price"],
                    "code": option["package_option_code"],
                    "option_order": option["order"]
                })
                                
                pkg_table.add_row(str(option_number), full_name, price_display)
                option_number += 1

        print_cyber_panel(pkg_table, title="AVAILABLE PACKAGES")

        console.print("[dim]00. Kembali ke menu utama[/]")
        pkg_choice = cyber_input("Pilih paket (nomor)")
        if pkg_choice == "00":
            in_package_menu = False
            return None
        
        if isinstance(pkg_choice, str) == False or not pkg_choice.isdigit():
            console.print("[error]Input tidak valid. Silakan masukan nomor paket.[/]")
            pause()
            continue
        
        selected_pkg = next((p for p in packages if p["number"] == int(pkg_choice)), None)
        
        if not selected_pkg:
            console.print("[error]Paket tidak ditemukan. Silakan masukan nomor yang benar.[/]")
            pause()
            continue
        
        show_package_details(
            api_key,
            tokens,
            selected_pkg["code"],
            is_enterprise,
            option_order=selected_pkg["option_order"],
        )
        
    return packages

def fetch_my_packages():
    in_my_packages_menu = True
    while in_my_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        if not tokens:
            console.print("[error]No active user tokens found.[/]")
            pause()
            return None
        
        id_token = tokens.get("id_token")
        
        path = "api/v8/packages/quota-details"
        
        payload = {
            "is_enterprise": False,
            "lang": "en",
            "family_member_id": ""
        }
        
        with loading_animation("Fetching my packages..."):
            res = send_api_request(api_key, path, payload, id_token, "POST")

        if res.get("status") != "SUCCESS":
            console.print("[error]Failed to fetch packages[/]")
            console.print_json(data=res)
            pause()
            return None
        
        quotas = res["data"]["quotas"]
        
        clear_screen()

        my_packages = []
        num = 1

        # Using Columns or a Grid might be too cluttered if many packages.
        # Let's stick to a Table or sequence of Panels.
        # Since user wants "cool", let's use a main Table for the list,
        # but the details are complex.

        # Let's verify content first.

        main_table = Table(show_header=True, header_style="neon_pink", box=None)
        main_table.add_column("No", style="neon_green", justify="right", width=4)
        main_table.add_column("Package Name", style="bold white")
        main_table.add_column("Quota Info", style="cyan")
        main_table.add_column("Exp", style="dim")

        for quota in quotas:
            quota_code = quota["quota_code"]
            quota_name = quota["name"]
            
            product_subscription_type = quota.get("product_subscription_type", "")
            product_domain = quota.get("product_domain", "")
            
            # Summarize benefits for table view
            benefits = quota.get("benefits", [])
            summary = "No benefits"
            if benefits:
                b = benefits[0] # Take first benefit as summary
                data_type = b.get("data_type", "")
                remaining = b.get("remaining", 0)
                total = b.get("total", 0)

                if data_type == "DATA":
                     summary = f"{format_quota_byte(remaining)} / {format_quota_byte(total)}"
                elif data_type == "VOICE":
                     summary = f"{remaining/60:.1f}m / {total/60:.1f}m"
                else:
                     summary = f"{remaining} / {total} {data_type}"

                if len(benefits) > 1:
                    summary += f" (+{len(benefits)-1} more)"

            main_table.add_row(str(num), quota_name, summary, "")
            
            my_packages.append({
                "number": num,
                "name": quota_name,
                "quota_code": quota_code,
                "product_subscription_type": product_subscription_type,
                "product_domain": product_domain,
                "full_data": quota # Store full data for detailed view if needed
            })
            num += 1

        print_cyber_panel(main_table, title="MY PACKAGES")
        
        console.print(Panel(
            """[bold white]Input Number[/]: View Detail
[bold white]del <N>[/]: Unsubscribe
[bold white]00[/]: Back to Main Menu""",
            title="ACTIONS",
            border_style="neon_cyan"
        ))

        choice = cyber_input("Choice")
        if choice == "00":
            in_my_packages_menu = False

        # Handle seletcting package to view detail
        if choice.isdigit() and int(choice) > 0 and int(choice) <= len(my_packages):
            selected_pkg = next((pkg for pkg in my_packages if pkg["number"] == int(choice)), None)
            if not selected_pkg:
                console.print("[error]Paket tidak ditemukan. Silakan masukan nomor yang benar.[/]")
                pause()
                continue
            
            # Show full details
            _ = show_package_details(api_key, tokens, selected_pkg["quota_code"], False)
        
        elif choice.startswith("del "):
            del_parts = choice.split(" ")
            if len(del_parts) != 2 or not del_parts[1].isdigit():
                console.print("[error]Invalid input for delete command.[/]")
                pause()
                continue
            
            del_number = int(del_parts[1])
            del_pkg = next((pkg for pkg in my_packages if pkg["number"] == del_number), None)
            if not del_pkg:
                console.print("[error]Package not found for deletion.[/]")
                pause()
                continue
            
            confirm = cyber_input(f"Are you sure you want to unsubscribe from package  {del_number}. {del_pkg['name']}? (y/n)")
            if confirm.lower() == 'y':
                with loading_animation(f"Unsubscribing from {del_pkg['name']}..."):
                    success = unsubscribe(
                        api_key,
                        tokens,
                        del_pkg["quota_code"],
                        del_pkg["product_subscription_type"],
                        del_pkg["product_domain"]
                    )
                if success:
                    console.print("[neon_green]Successfully unsubscribed from the package.[/]")
                else:
                    console.print("[error]Failed to unsubscribe from the package.[/]")
            else:
                console.print("[warning]Unsubscribe cancelled.[/]")
            pause()
