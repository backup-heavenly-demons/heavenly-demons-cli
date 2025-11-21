from datetime import datetime
import json
from app.menus.package import get_packages_by_family, show_package_details
from app.menus.util import pause, clear_screen, format_quota_byte
from app.client.circle import (
    get_group_data,
    get_group_members,
    create_circle,
    validate_circle_member,
    invite_circle_member,
    remove_circle_member,
    accept_circle_invitation,
    spending_tracker,
    get_bonus_data,
)
from app.service.auth import AuthInstance
from app.client.encrypt import decrypt_circle_msisdn
from app.console import console, print_cyber_panel, cyber_input, loading_animation
from rich.table import Table
from rich.panel import Panel

WIDTH = 55

def show_circle_creation(api_key: str, tokens: dict):
    clear_screen()
    console.print(Panel("Create a new Circle", title="CREATE CIRCLE", border_style="neon_pink"))
    
    parent_name = cyber_input("Enter your name (Parent)")
    group_name = cyber_input("Enter Circle name")
    member_msisdn = cyber_input("Enter initial member's MSISDN (e.g., 6281234567890)")
    member_name = cyber_input("Enter initial member's name")
    
    with loading_animation("Creating Circle..."):
        create_res = create_circle(
            api_key,
            tokens,
            parent_name,
            group_name,
            member_msisdn,
            member_name
        )
    
    console.print("[neon_green]Server Response:[/]")
    console.print_json(data=create_res)
    
    pause()

def show_bonus_list(
    api_key: str,
    tokens: dict,
    parent_subs_id: str,
    family_id: str,
):
    in_circle_bonus_menu = True
    
    while in_circle_bonus_menu:
        clear_screen()
        
        with loading_animation("Fetching bonus data..."):
            bonus_data = get_bonus_data(
                api_key,
                tokens,
                parent_subs_id,
                family_id
            )
        if bonus_data.get("status") != "SUCCESS":
            console.print("[error]Failed to fetch bonus data.[/]")
            pause()
            return
        
        bonus_list = bonus_data.get("data", {}).get("bonuses", [])
        if not bonus_list:
            console.print("[warning]No bonus data available.[/]")
            pause()
            return
        
        bonus_table = Table(show_header=True, header_style="neon_pink", box=None)
        bonus_table.add_column("No", style="neon_green", justify="right", width=4)
        bonus_table.add_column("Bonus Name", style="bold white")
        bonus_table.add_column("Type", style="cyan")
        bonus_table.add_column("Action", style="dim")
        
        for idx, bonus in enumerate(bonus_list, start=1):
            bonus_name = bonus.get("name", "N/A")
            bonus_type = bonus.get("bonus_type", "N/A")
            action_type = bonus.get("action_type", "N/A")
            action_param = bonus.get("action_param", "N/A")
            
            bonus_table.add_row(
                str(idx),
                bonus_name,
                bonus_type,
                f"{action_type}\n{action_param}"
            )

        print_cyber_panel(bonus_table, title="CIRCLE BONUS LIST")
            
        console.print("[dim]Enter the number of the bonus to view detail.\n00. Back[/]")
        
        choice = cyber_input("Pilih opsi")
        if choice == "00":
            in_circle_bonus_menu = False
        else:
            if choice.isdigit():
                bonus_number = int(choice)
                if bonus_number < 1 or bonus_number > len(bonus_list):
                    console.print("[error]Invalid bonus number.[/]")
                    pause()
                    continue

                selected_bonus = bonus_list[bonus_number - 1]
                action_type = selected_bonus.get("action_type", "N/A")
                action_param = selected_bonus.get("action_param", "N/A")

                if action_type == "PLP":
                    get_packages_by_family(action_param)
                elif action_type == "PDP":
                    show_package_details(
                        api_key,
                        tokens,
                        action_param,
                        False,
                    )
                else:
                    console.print(f"[warning]Unhandled Action Type: {action_type}\nParam: {action_param}[/]")
                    pause()
            else:
                 console.print("[error]Invalid input.[/]")
                 pause()

def show_circle_info(api_key: str, tokens: dict):
    in_circle_menu = True
    user: dict = AuthInstance.get_active_user()
    my_msisdn = user.get("number", "")

    while in_circle_menu:
        clear_screen()

        with loading_animation("Fetching circle data..."):
            group_res = get_group_data(api_key, tokens)

        if group_res.get("status") != "SUCCESS":
            console.print("[error]Failed to fetch circle data.[/]")
            pause()
            return
        
        group_data = group_res.get("data", {})        
        group_id = group_data.get("group_id", "") # or family_id

        if group_id == "":
            console.print("[warning]You are not part of any Circle.[/]")
            
            create_new = cyber_input("Do you want to create a new Circle? (y/n)")
            if create_new.lower() == "y":
                show_circle_creation(api_key, tokens)
                continue
            else:
                pause()
                return
        
        group_status = group_data.get("group_status", "N/A")
        if group_status == "BLOCKED":
            console.print("[error]This Circle is currently blocked.[/]")
            pause()
            return
        
        group_name = group_data.get("group_name", "N/A")
        owner_name = group_data.get("owner_name", "N/A")
        
        with loading_animation("Fetching members..."):
            members_res = get_group_members(api_key, tokens, group_id)

        if members_res.get("status") != "SUCCESS":
            console.print("[error]Failed to fetch circle members.[/]")
            pause()
            return
        
        members_data = members_res.get("data", {})
        members = members_data.get("members", [])
        if len(members) == 0:
            console.print("[warning]No members found in the Circle.[/]")
            pause()
            return
        
        parent_member_id = ""
        parent_subs_id = ""
        parrent_msisdn = ""
        for member in members:
            if member.get("member_role", "") == "PARENT":
                parent_member_id = member.get("member_id", "")
                parent_subs_id = member.get("subscriber_number", "")
                parrent_msisdn_encrypted = member.get("msisdn", "")
                parrent_msisdn = decrypt_circle_msisdn(api_key, parrent_msisdn_encrypted)
        
        package = members_data.get("package", {})
        package_name = package.get("name", "N/A")
        benefit = package.get("benefit", {})
        allocation_byte = benefit.get("allocation", 0)
        consumption_byte = benefit.get("consumption", 0)
        remaining_byte = benefit.get("remaining", 0)
        
        formatted_allocation = format_quota_byte(allocation_byte)
        formatted_remaining = format_quota_byte(remaining_byte)
        
        # Spending Tracker
        with loading_animation("Fetching spending tracker..."):
            spending_res = spending_tracker(
                api_key,
                tokens,
                parent_subs_id,
                group_id
            )
        if spending_res.get("status") != "SUCCESS":
            console.print("[error]Failed to fetch spending tracker data.[/]")
            pause()
            return
        
        spending_data = spending_res.get("data", {})
        spend = spending_data.get("spend", 0)
        target = spending_data.get("target", 0)
        
        clear_screen()
        
        # Header Info
        info_text = f"""[bold cyan]Circle:[/] {group_name} ({group_status})
[bold cyan]Owner:[/] {owner_name} {parrent_msisdn}
[bold cyan]Package:[/] {package_name} | {formatted_remaining} / {formatted_allocation}
[bold cyan]Spending:[/] Rp{spend:,} / Rp{target:,}"""
        print_cyber_panel(info_text, title="CIRCLE INFO")
        
        # Members List
        table = Table(show_header=True, header_style="neon_pink", box=None)
        table.add_column("No", style="neon_green", justify="right", width=4)
        table.add_column("Member", style="bold white")
        table.add_column("Role", style="cyan")
        table.add_column("Usage", style="dim")
        table.add_column("Status", style="yellow")

        for idx, member in enumerate(members, start=1):
            encrypted_msisdn = member.get("msisdn", "")
            msisdn = decrypt_circle_msisdn(api_key, encrypted_msisdn)
            
            member_role = member.get("member_role", "N/A")
            
            join_date_ts = member.get("join_date", 0)
            slot_type = member.get("slot_type", "N/A")
            member_name = member.get("member_name", "N/A")
            member_allocation_byte = member.get("allocation", 0)
            member_remaining_byte = member.get("remaining", 0)
            member_status = member.get("status", "N/A")
            
            formatted_msisdn = f"{msisdn}"
            if msisdn == "":
                formatted_msisdn = "<No Number>"
            
            me_mark = ""
            if str(msisdn) == str(my_msisdn):
                me_mark = " [bold neon_green](You)[/]"
            
            member_type = "Parent" if member_role == "PARENT" else "Member"
            formated_quota_allocated = format_quota_byte(member_allocation_byte)
            formated_quota_used = format_quota_byte(member_allocation_byte - member_remaining_byte)
            
            table.add_row(
                str(idx),
                f"{formatted_msisdn}\n{member_name}{me_mark}",
                member_type,
                f"{formated_quota_used} / {formated_quota_allocated}",
                member_status
            )

        print_cyber_panel(table, title="CIRCLE MEMBERS")
            
        console.print(Panel(
            """[bold white]1[/]: Invite Member
[bold white]del <N>[/]: Remove Member
[bold white]acc <N>[/]: Accept Invitation
[bold white]2[/]: View Bonus List
[bold white]00[/]: Back to Main Menu""",
            title="ACTIONS",
            border_style="neon_cyan"
        ))

        choice = cyber_input("Pilih opsi")
        if choice == "00":
            in_circle_menu = False
        elif choice == "1":
            msisdn_to_invite = cyber_input("Enter MSISDN to invite (e.g., 6281234567890)")
            with loading_animation("Validating member..."):
                validate_res = validate_circle_member(api_key, tokens, msisdn_to_invite)
            if validate_res.get("status") == "SUCCESS":
                if validate_res.get("data", {}).get("response_code", "") != "200-2001":
                    console.print(f"[error]Cannot invite {msisdn_to_invite}: {validate_res.get('data', {}).get('message', 'Unknown error')}[/]")
                    pause()
                    continue
            
            member_name = cyber_input("Enter member name")
            
            with loading_animation("Sending invitation..."):
                invite_res = invite_circle_member(
                    api_key,
                    tokens,
                    msisdn_to_invite,
                    member_name,
                    group_id,
                    parent_member_id
                )
            if invite_res.get("status") == "SUCCESS":
                if invite_res.get("data", {}).get("response_code", "") == "200-00":
                    console.print(f"[neon_green]Invitation sent to {msisdn_to_invite} successfully.[/]")
                else:
                    console.print(f"[error]Failed to invite {msisdn_to_invite}: {invite_res.get('data', {}).get('message', 'Unknown error')}[/]")
            pause()
        elif choice.startswith("del "):
            try:
                member_number = int(choice.split(" ")[1])
                if member_number < 1 or member_number > len(members):
                    console.print("[error]Invalid member number.[/]")
                    pause()
                    continue
                member_to_remove = members[member_number - 1]
                
                # Prevent removing parent
                if member_to_remove.get("member_role", "") == "PARENT":
                    console.print("[error]Cannot remove the parent member from the Circle.[/]")
                    pause()
                    continue
                
                member_id = member_to_remove.get("member_id", "")
                
                # Prevent removing last member
                is_last_member = len(members) == 2
                if is_last_member:
                    console.print("[error]Cannot remove the last member from the Circle.[/]")
                    pause()
                    continue
                
                msisdn_to_remove = decrypt_circle_msisdn(api_key, member_to_remove.get("msisdn", ""))
                confirm = cyber_input(f"Are you sure you want to remove {msisdn_to_remove} from the Circle? (y/n)")
                if confirm.lower() != "y":
                    console.print("[warning]Removal cancelled.[/]")
                    pause()
                    continue
                
                with loading_animation("Removing member..."):
                    remove_res = remove_circle_member(
                        api_key,
                        tokens,
                        member_id,
                        group_id,
                        parent_member_id,
                        is_last_member
                    )
                if remove_res.get("status") == "SUCCESS":
                    console.print(f"[neon_green]{msisdn_to_remove} has been removed from the Circle.[/]")
                else:
                    console.print(f"[error]Error: {remove_res}[/]")
            except ValueError:
                console.print("[error]Invalid input format for deletion.[/]")
            pause()
        elif choice.startswith("acc "):
            try:
                member_number = int(choice.split(" ")[1])
                if member_number < 1 or member_number > len(members):
                    console.print("[error]Invalid member number.[/]")
                    pause()
                    continue
                member_to_accept = members[member_number - 1]
                
                member_status = member_to_accept.get("status", "")
                if member_status != "INVITED":
                    console.print("[warning]This member is not in an invited state.[/]")
                    pause()
                    continue
                
                member_id = member_to_accept.get("member_id", "")
                msisdn_to_accept = decrypt_circle_msisdn(api_key, member_to_accept.get("msisdn", ""))
                confirm = cyber_input(f"Do you want to accept the invitation for {msisdn_to_accept}? (y/n)")
                if confirm.lower() != "y":
                    console.print("[warning]Acceptance cancelled.[/]")
                    pause()
                    continue
                
                with loading_animation("Accepting invitation..."):
                    accept_res = accept_circle_invitation(
                        api_key,
                        tokens,
                        group_id,
                        member_id,
                        )

                if accept_res.get("status") == "SUCCESS":
                    console.print(f"[neon_green]Invitation for {msisdn_to_accept} has been accepted.[/]")
                else:
                    console.print(f"[error]Error: {accept_res}[/]")
            except ValueError:
                console.print("[error]Invalid input format for acceptance.[/]")
            pause()
        elif choice == "2":
            show_bonus_list(
                api_key,
                tokens,
                parent_subs_id,
                group_id
            )
