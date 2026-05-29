# app/vsphere/snapshots.py
"""
TASK-029: Snapshot inventory with age flags.

Commands:
  /vsphere snapshots          — all VMs with snapshots, oldest first
  /vsphere snapshots <vm>     — snapshot tree for a specific VM
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.vsphere.client import get_si
from app.vsphere.vms import _find_vm

logger = logging.getLogger(__name__)

WARN_DAYS = 7
CRITICAL_DAYS = 30


def _age_flag(age_days: int) -> str:
    if age_days >= CRITICAL_DAYS:
        return "❌"
    if age_days >= WARN_DAYS:
        return "⚠️"
    return "  "


def _flatten_snapshots(snap_list, depth: int = 0) -> list:
    result = []
    for snap in snap_list:
        age_days = (datetime.now(timezone.utc) - snap.createTime).days
        result.append({
            "name": snap.name,
            "description": snap.description or "",
            "created": snap.createTime.strftime("%Y-%m-%d"),
            "age_days": age_days,
            "depth": depth,
        })
        result.extend(_flatten_snapshots(snap.childSnapshotList, depth + 1))
    return result


def get_all_snapshots() -> str:
    si = None
    try:
        si = get_si()
        content = si.RetrieveContent()
        from pyVmomi import vim

        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.VirtualMachine], True
        )
        all_vms = list(container.view)
        container.Destroy()

        vms_with_snaps = [vm for vm in all_vms if vm.snapshot]
        if not vms_with_snaps:
            return "📸 Snapshot Inventory\n━━━━━━━━━━━━━━━━━━━━━━━━\n✅ No snapshots found in the environment."

        # Collect and sort (oldest snapshots first)
        vm_snap_data = []
        for vm in vms_with_snaps:
            snaps = _flatten_snapshots(vm.snapshot.rootSnapshotList)
            vm_snap_data.append((vm.name, snaps))
        vm_snap_data.sort(key=lambda x: max(s["age_days"] for s in x[1]), reverse=True)

        total = sum(len(s) for _, s in vm_snap_data)
        lines = [
            f"📸 Snapshot Inventory ({total} snapshots across {len(vm_snap_data)} VMs)",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
        shown = 0
        MAX = 20
        for vm_name, snaps in vm_snap_data:
            if shown >= MAX:
                break
            lines.append(f"\n**{vm_name}** ({len(snaps)} snapshot{'s' if len(snaps) != 1 else ''})")
            for snap in snaps:
                if shown >= MAX:
                    break
                flag = _age_flag(snap["age_days"])
                indent = "  " * snap["depth"]
                lines.append(
                    f"{indent}{flag} {snap['name']:<30} {snap['created']}  ({snap['age_days']} days ago)"
                )
                shown += 1

        if total > MAX:
            lines.append(f"\n… {total - MAX} more snapshots not shown.")

        lines.append(f"\n**Legend:** ❌ >{CRITICAL_DAYS} days  ⚠️ >{WARN_DAYS} days")
        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("Snapshot inventory failed")
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass


def get_vm_snapshots(vm_name: str) -> str:
    si = None
    try:
        si = get_si()
        content = si.RetrieveContent()
        vm = _find_vm(content, vm_name)

        if vm is None:
            return f"❌ VM not found: `{vm_name}`"

        if not vm.snapshot:
            return f"📸 Snapshots: {vm_name}\n━━━━━━━━━━━━━━━━━━━━━━━━━\nNo snapshots on `{vm_name}`."

        snaps = _flatten_snapshots(vm.snapshot.rootSnapshotList)
        lines = [f"📸 Snapshots: {vm_name}", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        for snap in snaps:
            flag = _age_flag(snap["age_days"])
            indent = "  " * snap["depth"]
            lines.append(
                f"{indent}{flag} **{snap['name']}**  ({snap['created']}, {snap['age_days']} days ago)"
            )
            if snap["description"]:
                lines.append(f"{indent}   \"{snap['description']}\"")

        lines.append(f"\n**Legend:** ❌ >{CRITICAL_DAYS} days  ⚠️ >{WARN_DAYS} days")
        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("VM snapshots failed for %s", vm_name)
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass
