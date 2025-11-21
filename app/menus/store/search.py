from app.client.store.search import get_family_list, get_store_packages
from app.menus.package import get_packages_by_family, show_package_details
from app.menus.util import clear_screen, pause
from app.service.auth import AuthInstance
from app.console import console, print_cyber_panel, cyber_input, loading_animation
from rich.table import Table

WIDTH = 55

def show_family_list_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
    in_family_list_menu = True
    while in_family_list_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        with loading_animation("Fetching family list..."):
            family_list_res = get_family_list(api_key, tokens, subs_type, is_enterprise)

        if not family_list_res:
            console.print("[warning]No family list found.[/]")
            in_family_list_menu = False
            continue
        
        family_list = family_list_res.get("data", {}).get("results", [])
        
        clear_screen()
        
        table = Table(show_header=True, header_style="neon_pink", box=None)
        table.add_column("No", style="neon_green", justify="right", width=4)
        table.add_column("Family Name", style="bold white")
        table.add_column("Family Code", style="dim")
        
        for i, family in enumerate(family_list):
            family_name = family.get("label", "N/A")
            family_code = family.get("id", "N/A")
            
            table.add_row(str(i + 1), family_name, family_code)

        print_cyber_panel(table, title="FAMILY LIST")
        
        console.print("[dim]00. Back to Main Menu[/]")
        choice = cyber_input("Input the number to view packages in that family")
        if choice == "00":
            in_family_list_menu = False
            continue
        
        if choice.isdigit() and int(choice) > 0 and int(choice) <= len(family_list):
            selected_family = family_list[int(choice) - 1]
            family_code = selected_family.get("id", "")
            family_name = selected_family.get("label", "N/A")
            
            console.print(f"[info]Fetching packages for family: {family_name}...[/]")
            get_packages_by_family(family_code)
        else:
             console.print("[error]Invalid choice.[/]")
             pause()
    

def show_store_packages_menu(
    subs_type: str = "PREPAID",
    is_enterprise: bool = False,
):
    in_store_packages_menu = True
    while in_store_packages_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        with loading_animation("Fetching store packages..."):
            store_packages_res = get_store_packages(api_key, tokens, subs_type, is_enterprise)

        if not store_packages_res:
            console.print("[warning]No store packages found.[/]")
            in_store_packages_menu = False
            continue
        
        store_packages = store_packages_res.get("data", {}).get("results_price_only", [])
        
        clear_screen()
        
        packages = {}

        table = Table(show_header=True, header_style="neon_pink", box=None)
        table.add_column("No", style="neon_green", justify="right", width=4)
        table.add_column("Package", style="bold white")
        table.add_column("Price", style="yellow")
        table.add_column("Validity", style="cyan")

        for i, package in enumerate(store_packages):
            title = package.get("title", "N/A")
            
            original_price = package.get("original_price", 0)
            discounted_price = package.get("discounted_price", 0)
            
            price = original_price
            if discounted_price > 0:
                price = discounted_price
            
            validity = package.get("validity", "N/A")
            family_name = package.get("family_name", "N/A")
            
            action_type = package.get("action_type", "")
            action_param = package.get("action_param", "")
            
            packages[f"{i + 1}"] = {
                "action_type": action_type,
                "action_param": action_param
            }
            
            table.add_row(
                str(i + 1),
                f"{title}\n[dim]{family_name}[/]",
                f"Rp{price}",
                validity
            )

        print_cyber_panel(table, title="STORE PACKAGES")
        
        console.print("[dim]00. Back to Main Menu[/]")
        choice = cyber_input("Input the number to view package details")
        if choice == "00":
            in_store_packages_menu = False
            continue

        if choice in packages:
            selected_package = packages[choice]
            
            action_type = selected_package["action_type"]
            action_param = selected_package["action_param"]
            
            if action_type == "PDP":
                _ = show_package_details(
                        api_key,
                        tokens,
                        action_param,
                        is_enterprise
                    )
            else:
                console.print(f"[warning]Unhandled Action Type: {action_type}\nParam: {action_param}[/]")
                pause()
        else:
            console.print("[error]Invalid choice. Please enter a valid package number.[/]")
            pause()
