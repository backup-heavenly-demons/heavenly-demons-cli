from datetime import datetime
import json
from app.menus.util import pause, clear_screen, format_quota_byte
from app.client.famplan import get_family_data, change_member, remove_member, set_quota_limit, validate_msisdn
from app.console import console, print_cyber_panel, cyber_input, loading_animation
from rich.table import Table
from rich.panel import Panel

WIDTH = 55

def show_family_info(api_key: str, tokens: dict):
    in_family_menu = True
    while in_family_menu:
        clear_screen()

        with loading_animation("Fetching family plan data..."):
            res = get_family_data(api_key, tokens)

        if not res.get("data"):
            console.print("[error]Failed to get family data.[/]")
            pause()
            return
        
        family_detail = res["data"]
        plan_type = family_detail["member_info"]["plan_type"]
        
        if plan_type == "":
            console.print("[warning]You are not family plan organizer.[/]")
            pause()
            return
        
        parent_msisdn = family_detail["member_info"]["parent_msisdn"]
        members = family_detail["member_info"]["members"]
        empyt_slots = [slot for slot in members if slot.get("msisdn") == ""]
        
        total_quota_byte = family_detail["member_info"].get("total_quota", 0)
        remaining_quota_byte = family_detail["member_info"].get("remaining_quota", 0)
        
        total_quota_human = format_quota_byte(total_quota_byte)
        remaining_quota_human = format_quota_byte(remaining_quota_byte)
        
        end_date_ts = family_detail["member_info"].get("end_date", 0)
        end_date = datetime.fromtimestamp(end_date_ts).strftime("%Y-%m-%d")
        
        # Header Info
        info_text = f"""[bold cyan]Plan:[/] {plan_type}
[bold cyan]Parent:[/] {parent_msisdn}
[bold cyan]Shared Quota:[/] {remaining_quota_human} / {total_quota_human}
[bold cyan]Exp:[/] {end_date}
[bold cyan]Members:[/] {len(members) - len(empyt_slots)}/{len(members)}"""
        print_cyber_panel(info_text, title="FAMILY PLAN OVERVIEW")

        # Members Table
        table = Table(show_header=True, header_style="neon_pink", box=None)
        table.add_column("Slot", style="neon_green", justify="right", width=4)
        table.add_column("Member Info", style="bold white")
        table.add_column("Usage", style="cyan")
        table.add_column("Role", style="dim")
        
        for idx, member in enumerate(members, start=1):
            msisdn = member.get("msisdn", "N/A")
            formatted_msisdn = f"{msisdn}"
            if msisdn == "":
                formatted_msisdn = "[dim]<Empty Slot>[/]"
            
            alias = member.get("alias", "N/A")
            member_type = member.get("member_type", "N/A")
            
            quota_allocated_byte = member.get("usage", {}).get("quota_allocated", 0)
            formated_quota_allocated = format_quota_byte(quota_allocated_byte)
            
            quota_used_byte = member.get("usage", {}).get("quota_used", 0)
            formated_quota_used = format_quota_byte(quota_used_byte)

            add_chances = member.get("add_chances", 0)
            total_add_chances = member.get("total_add_chances", 0)
            
            info_display = f"{formatted_msisdn}\nAlias: {alias}"
            if msisdn != "":
                info_display += f"\nAdd Chances: {add_chances}/{total_add_chances}"
            
            table.add_row(
                str(idx),
                info_display,
                f"{formated_quota_used} / {formated_quota_allocated}",
                member_type
            )

        print_cyber_panel(table, title="FAMILY MEMBERS")
        
        console.print(Panel(
            """[bold white]1[/]: Change Member
[bold white]limit <Slot> <Quota MB>[/]: Set Quota Limit
[bold white]del <Slot>[/]: Remove Member
[bold white]00[/]: Back to Main Menu""",
            title="ACTIONS",
            border_style="neon_cyan"
        ))
        
        choice = cyber_input("Enter your choice").strip()
        if choice == "1":
            slot_idx = cyber_input("Enter the slot number").strip()
            target_msisdn = cyber_input("Enter the new member's phone number (start with 62)").strip()
            parent_alias = cyber_input("Enter your alias").strip()
            child_alias = cyber_input("Enter the new member's alias").strip()
            
            try:
                slot_idx_int = int(slot_idx)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    console.print("[error]Invalid slot number.[/]")
                    pause()
                    return
                
                if members[slot_idx_int - 1].get("msisdn") != "":
                    console.print("[error]Selected slot is not empty. Cannot change member.[/]")
                    pause()
                    return
                
                family_member_id = members[slot_idx_int - 1]["family_member_id"]
                slot_id = members[slot_idx_int - 1]["slot_id"]
                
                # Checking MSISDN
                with loading_animation("Validating MSISDN..."):
                    validation_res = validate_msisdn(api_key, tokens, target_msisdn)

                if validation_res.get("status").lower() != "success":
                    console.print("[error]MSISDN validation failed.[/]")
                    console.print_json(data=validation_res)
                    pause()
                    return
                console.print("[neon_green]MSISDN validation successful.[/]")
                
                target_family_plan_role = validation_res["data"].get("family_plan_role", "")
                if target_family_plan_role != "NO_ROLE":
                    console.print(f"[warning]{target_msisdn} is already part of another family plan with role {target_family_plan_role}.[/]")
                    pause()
                    return

                is_continue = cyber_input(f"Are you sure you want to assign {target_msisdn} to slot {slot_idx_int}? (y/n)").strip().lower()
                if is_continue != "y":
                    console.print("[warning]Operation cancelled by user.[/]")
                    pause()
                    return
                
                with loading_animation("Changing member..."):
                    change_member_res = change_member(
                        api_key,
                        tokens,
                        parent_alias,
                        child_alias,
                        slot_id,
                        family_member_id,
                        target_msisdn,
                    )

                if change_member_res.get("status") == "SUCCESS":
                    console.print("[neon_green]Member changed successfully.[/]")
                else:
                    console.print(f"[error]Failed to change member: {change_member_res.get('message', 'Unknown error')}[/]")
                
                console.print_json(data=change_member_res)
            except ValueError:
                console.print("[error]Invalid input. Please enter a valid slot number.[/]")
            pause()
        elif choice.startswith("del "):
            _, slot_num = choice.split(" ", 1)
            try:
                slot_idx_int = int(slot_num)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    console.print("[error]Invalid slot number.[/]")
                    pause()
                    return
                
                member = members[slot_idx_int - 1]
                if member.get("msisdn") == "":
                    console.print("[warning]Selected slot is already empty.[/]")
                    pause()
                    return
                
                is_continue = cyber_input(f"Are you sure you want to remove member {member.get('msisdn')} from slot {slot_idx_int}? (y/n)").strip().lower()
                if is_continue != "y":
                    console.print("[warning]Operation cancelled by user.[/]")
                    pause()
                    return
                
                family_member_id = member["family_member_id"]

                with loading_animation("Removing member..."):
                    res = remove_member(
                        api_key,
                        tokens,
                        family_member_id,
                    )
                if res.get("status") == "SUCCESS":
                    console.print("[neon_green]Member removed successfully.[/]")
                else:
                    console.print(f"[error]Failed to remove member: {res.get('message', 'Unknown error')}[/]")
                
                console.print_json(data=res)
            except ValueError:
                console.print("[error]Invalid input. Please enter a valid slot number.[/]")
            pause()
        elif choice.startswith("limit "):
            try:
                parts = choice.split(" ")
                if len(parts) < 3:
                    raise ValueError

                slot_num = parts[1]
                new_quota_mb = parts[2]

                slot_idx_int = int(slot_num)
                new_quota_mb_int = int(new_quota_mb)
                if slot_idx_int < 1 or slot_idx_int > len(members):
                    console.print("[error]Invalid slot number.[/]")
                    pause()
                    return
                
                member = members[slot_idx_int - 1]
                if member.get("msisdn") == "":
                    console.print("[warning]Selected slot is empty. Cannot set quota limit.[/]")
                    pause()
                    return
                
                family_member_id = member["family_member_id"]
                original_allocation_byte = member.get("usage", {}).get("quota_allocated", 0)
                new_allocation_byte = new_quota_mb_int * 1024 * 1024
                
                with loading_animation(f"Setting quota limit to {new_quota_mb_int}MB..."):
                    res = set_quota_limit(
                        api_key,
                        tokens,
                        original_allocation_byte,
                        new_allocation_byte,
                        family_member_id,
                    )
                if res.get("status") == "SUCCESS":
                    console.print("[neon_green]Quota limit set successfully.[/]")
                else:
                    console.print(f"[error]Failed to set quota limit: {res.get('message', 'Unknown error')}[/]")
                
                console.print_json(data=res)
            except ValueError:
                console.print("[error]Invalid input. Usage: limit <slot> <mb>[/]")
            pause()
        elif choice == "00":
            in_family_menu = False
            return
