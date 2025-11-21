from app.client.store.redeemables import get_redeemables
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.menus.package import show_package_details, get_packages_by_family
from app.console import console, print_cyber_panel, cyber_input, loading_animation
from rich.table import Table

from datetime import datetime

WIDTH = 55

def show_redeemables_menu(is_enterprise: bool = False):
    in_redeemables_menu = True
    while in_redeemables_menu:
        api_key = AuthInstance.api_key
        tokens = AuthInstance.get_active_tokens()
        
        with loading_animation("Fetching redeemables..."):
            redeemables_res = get_redeemables(api_key, tokens, is_enterprise)

        if not redeemables_res:
            console.print("[warning]No redeemables found.[/]")
            in_redeemables_menu = False
            continue
        
        categories = redeemables_res.get("data", {}).get("categories", [])
        
        clear_screen()
        
        packages = {}

        for i, category in enumerate(categories):
            category_name = category.get("category_name", "N/A")
            category_code = category.get("category_code", "N/A")
            redemables = category.get("redeemables", [])
            
            letter = chr(65 + i)

            table = Table(show_header=True, header_style="neon_pink", box=None)
            table.add_column("ID", style="neon_green", justify="right", width=4)
            table.add_column("Name", style="bold white")
            table.add_column("Valid Until", style="cyan")
            table.add_column("Action Type", style="dim")
            
            if len(redemables) == 0:
                # console.print(f"[dim]No redeemables in category {category_name}[/]")
                continue
            
            for j, redemable in enumerate(redemables):
                name = redemable.get("name", "N/A")
                valid_until = redemable.get("valid_until", 0)
                valid_until_date = datetime.strftime(
                    datetime.fromtimestamp(valid_until), "%Y-%m-%d"
                )
                
                action_param = redemable.get("action_param", "")
                action_type = redemable.get("action_type", "")
                
                packages[f"{letter.lower()}{j + 1}"] = {
                    "action_param": action_param,
                    "action_type": action_type
                }
                
                table.add_row(
                    f"{letter}{j + 1}",
                    name,
                    valid_until_date,
                    action_type
                )

            print_cyber_panel(table, title=f"CATEGORY: {category_name} ({category_code})")
                
        console.print("[dim]00. Back[/]")
        
        choice = cyber_input("Enter your choice to view package details (e.g., A1, B2)")
        if choice == "00":
            in_redeemables_menu = False
            continue
        selected_pkg = packages.get(choice.lower())
        if not selected_pkg:
            console.print("[error]Invalid choice. Please enter a valid package code.[/]")
            pause()
            continue
        action_param = selected_pkg["action_param"]
        action_type = selected_pkg["action_type"]
        
        if action_type == "PLP":
            get_packages_by_family(action_param, is_enterprise, "")
        elif action_type == "PDP":
            show_package_details(
                api_key,
                tokens,
                action_param,
                is_enterprise,
            )
        else:
            console.print(f"[warning]Unhandled Action Type: {action_type}\nParam: {action_param}[/]")
            pause()
