from app.menus.package import show_package_details
from app.service.auth import AuthInstance
from app.menus.util import clear_screen, pause
from app.service.bookmark import BookmarkInstance
from app.client.engsel import get_family
from app.console import console, print_cyber_panel, cyber_input, loading_animation
from rich.table import Table

def show_bookmark_menu():
    api_key = AuthInstance.api_key
    tokens = AuthInstance.get_active_tokens()
    
    in_bookmark_menu = True
    while in_bookmark_menu:
        clear_screen()

        bookmarks = BookmarkInstance.get_bookmarks()
        if not bookmarks or len(bookmarks) == 0:
            console.print("[warning]Tidak ada bookmark tersimpan.[/]")
            pause()
            return None
        
        table = Table(show_header=True, header_style="neon_pink", box=None)
        table.add_column("No", style="neon_green", justify="right", width=4)
        table.add_column("Family", style="bold white")
        table.add_column("Variant", style="cyan")
        table.add_column("Option", style="dim")

        for idx, bm in enumerate(bookmarks):
            table.add_row(
                str(idx + 1),
                bm['family_name'],
                bm['variant_name'],
                bm['option_name']
            )

        print_cyber_panel(table, title="BOOKMARKED PACKAGES")
        
        console.print("[dim]00. Kembali ke menu utama | 000. Hapus Bookmark[/]")

        choice = cyber_input("Pilih bookmark (nomor)")
        if choice == "00":
            in_bookmark_menu = False
            return None
        elif choice == "000":
            del_choice = cyber_input("Masukan nomor bookmark yang ingin dihapus")
            if del_choice.isdigit() and 1 <= int(del_choice) <= len(bookmarks):
                del_bm = bookmarks[int(del_choice) - 1]
                BookmarkInstance.remove_bookmark(
                    del_bm["family_code"],
                    del_bm["is_enterprise"],
                    del_bm["variant_name"],
                    del_bm["order"],
                )
                console.print("[neon_green]Bookmark deleted.[/]")
                pause()
            else:
                console.print("[error]Input tidak valid. Silahkan coba lagi.[/]")
                pause()
            continue
        if choice.isdigit() and 1 <= int(choice) <= len(bookmarks):
            selected_bm = bookmarks[int(choice) - 1]
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
                console.print(f"[info]Option Code: {option_code}[/]")
                show_package_details(api_key, tokens, option_code, is_enterprise)            
            
        else:
            console.print("[error]Input tidak valid. Silahkan coba lagi.[/]")
            pause()
            continue
