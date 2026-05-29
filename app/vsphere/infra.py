# app/vsphere/infra.py
"""
TASK-027: ESXi host health, cluster status, and datastore capacity.

Commands:
  /vsphere hosts       — all ESXi hosts with state and utilization
  /vsphere cluster     — cluster HA/DRS state and aggregate resources
  /vsphere datastores  — datastore capacity, free space, % used
"""

import logging

from app.vsphere.client import get_si

logger = logging.getLogger(__name__)


def _bytes_to_human(b: int) -> str:
    if b >= 1_099_511_627_776:
        return f"{b / 1_099_511_627_776:.1f} TB"
    if b >= 1_073_741_824:
        return f"{b / 1_073_741_824:.1f} GB"
    return f"{b / 1_048_576:.0f} MB"


def get_hosts() -> str:
    si = None
    try:
        si = get_si()
        content = si.RetrieveContent()
        from pyVmomi import vim

        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.HostSystem], True
        )
        hosts = list(container.view)
        container.Destroy()

        if not hosts:
            return "🖥️  ESXi Hosts\n━━━━━━━━━━━━━━━━━━━━━━━━\nNo ESXi hosts found."

        lines = [
            f"🖥️  ESXi Hosts ({len(hosts)})",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"{'Host':<30} {'State':<14} {'CPU Used':<10} {'Mem Used'}",
            f"{'─'*30} {'─'*14} {'─'*10} {'─'*10}",
        ]
        for host in hosts:
            name = host.name.split(".")[0] if "." in host.name else host.name
            conn_state = host.summary.runtime.connectionState
            power_state = host.summary.runtime.powerState
            is_ok = conn_state == "connected" and power_state == "poweredOn"
            state_icon = "✅" if is_ok else "❌"
            state_str = f"{conn_state}/{power_state}"

            qs = host.summary.quickStats
            hw = host.summary.hardware
            if hw and qs and is_ok:
                total_cpu_mhz = hw.cpuMhz * hw.numCpuCores
                cpu_pct = f"{qs.overallCpuUsage * 100 // total_cpu_mhz}%" if total_cpu_mhz else "N/A"
                total_mem_mb = hw.memorySize // 1_048_576
                mem_pct = f"{qs.overallMemoryUsage * 100 // total_mem_mb}%" if total_mem_mb else "N/A"
            else:
                cpu_pct = mem_pct = "—"

            lines.append(f"{state_icon} {name:<28} {state_str:<14} {cpu_pct:<10} {mem_pct}")

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("vSphere hosts query failed")
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass


def get_cluster() -> str:
    si = None
    try:
        si = get_si()
        content = si.RetrieveContent()
        from pyVmomi import vim

        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.ClusterComputeResource], True
        )
        clusters = list(container.view)
        container.Destroy()

        if not clusters:
            return "🏗️  vSphere Cluster\n━━━━━━━━━━━━━━━━━━━━━\nNo clusters configured."

        lines = []
        for cluster in clusters:
            name = cluster.name
            summary = cluster.summary
            cfg = cluster.configurationEx

            ha_enabled = getattr(cfg.dasConfig, "enabled", False) if hasattr(cfg, "dasConfig") else False
            drs_enabled = drs_mode = False
            if hasattr(cfg, "drsConfig"):
                drs_enabled = getattr(cfg.drsConfig, "enabled", False)
                drs_mode = getattr(cfg.drsConfig, "defaultVmBehavior", "N/A")

            total_cpu_ghz = summary.totalCpu / 1000 if summary.totalCpu else 0
            total_mem_gb = summary.totalMemory / 1_073_741_824 if summary.totalMemory else 0

            lines += [
                f"🏗️  Cluster: {name}",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                f"HA:           {'✅ Enabled' if ha_enabled else '❌ Disabled'}",
                f"DRS:          {'✅ Enabled' if drs_enabled else '❌ Disabled'}"
                + (f" ({drs_mode})" if drs_enabled else ""),
                f"Hosts:        {summary.numEffectiveHosts} effective / {summary.numHosts} total",
                f"Total CPU:    {total_cpu_ghz:.1f} GHz",
                f"Total Memory: {total_mem_gb:.0f} GB",
                f"vMotions:     {summary.numVmotions}",
                "",
            ]
        return "\n".join(lines).rstrip()

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("vSphere cluster query failed")
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass


def get_datastores() -> str:
    si = None
    try:
        si = get_si()
        content = si.RetrieveContent()
        from pyVmomi import vim

        container = content.viewManager.CreateContainerView(
            content.rootFolder, [vim.Datastore], True
        )
        datastores = list(container.view)
        container.Destroy()

        if not datastores:
            return "💾 Datastores\n━━━━━━━━━━━━━━━━━━━━━━\nNo datastores found."

        lines = [
            f"💾 Datastores ({len(datastores)})",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"{'Datastore':<28} {'Capacity':<10} {'Free':<10} {'Used':<7} Status",
            f"{'─'*28} {'─'*10} {'─'*10} {'─'*7} {'─'*10}",
        ]
        for ds in datastores:
            s = ds.summary
            accessible = s.accessible
            cap = s.capacity
            free = s.freeSpace

            if not accessible:
                lines.append(f"❌ {ds.name:<26} —          —          —       Not accessible")
                continue

            used_pct = int((cap - free) * 100 / cap) if cap else 0
            warn = " ⚠️" if used_pct > 80 else ""
            lines.append(
                f"{'✅'} {ds.name:<26} {_bytes_to_human(cap):<10} "
                f"{_bytes_to_human(free):<10} {used_pct}%{warn}"
            )

        return "\n".join(lines)

    except Exception as e:
        from app.utils.responses import error, translate_exception
        logger.exception("vSphere datastores query failed")
        return error(translate_exception(e), hint="Check VCENTER_HOST and credentials in .env.")
    finally:
        if si:
            try:
                from pyVim.connect import Disconnect
                Disconnect(si)
            except Exception:
                pass
